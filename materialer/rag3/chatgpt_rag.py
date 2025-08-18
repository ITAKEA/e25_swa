"""
SQL RAG App — Question → SQL → DB → Answer (two-pass LLM)

Quickstart
----------
1) Python 3.10+
2) `pip install openai>=1.30.0 python-dotenv`
3) Create an `.env` file in the same folder containing:

   OPENAI_API_KEY=sk-...  # your key
   OPENAI_MODEL=gpt-4o-mini  # or another chat-capable model

4) Run:
   python sql_rag.py "How many orders did we have in July 2024?"

What it does
------------
• Pass 1: Sends your natural-language question + DB schema to the LLM → returns a *single* SQLite SELECT query (guardrailed).
• Executes the SQL on a local SQLite DB (auto-created with a tiny sample sales schema + seed data on first run).
• Pass 2: Sends the original question + the SQL + the query results back to the LLM → returns a concise, grounded answer.

Safety
------
• Only allows a single SELECT/CTE SELECT (no writes/DDL/PRAGMA; rejects dangerous keywords).
• Adds LIMIT 100 to non-limited queries to avoid giant result sets.
• If the LLM can’t produce a safe query, you’ll get an explanatory message instead.

Switching DBs
-------------
This demo uses SQLite for simplicity. To adapt to Postgres/MySQL, replace `sqlite3` with SQLAlchemy + the right driver, and update `introspect_schema()` to pull columns/types from INFORMATION_SCHEMA or SQLAlchemy's inspector.
"""

from __future__ import annotations
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

# ================ Config ==================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DB_PATH = os.getenv("SQL_RAG_DB", "rag_sql.db")
MAX_ROWS_TO_SEND = 100  # hard cap for pass-2 payload size

# Lazy import so the script still prints a helpful error if OpenAI isn't installed yet
_openai_client = None

def openai_client():
    global _openai_client
    if _openai_client is None:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "OpenAI SDK not found. Please run: pip install openai>=1.30.0\n"
            ) from e
        _openai_client = OpenAI(api_key=OPENAI_API_KEY or None)
    return _openai_client

# ================ Demo DB (SQLite) ==================

SCHEMA_SQL = """
-- customers
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    country TEXT
);

-- products
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    price REAL NOT NULL
);

-- orders
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL, -- ISO date string YYYY-MM-DD
    status TEXT NOT NULL,     -- e.g., 'pending','shipped','delivered','canceled'
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);

-- order_items
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL, -- snapshot of products.price at time of order
    FOREIGN KEY(order_id) REFERENCES orders(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);
"""

SEED_SQL = """
INSERT OR IGNORE INTO customers (id, name, email, country) VALUES
  (1, 'Alice Larsen', 'alice@example.com', 'Denmark'),
  (2, 'Bob Nielsen', 'bob@example.com', 'Denmark'),
  (3, 'Carla Svensson', 'carla@example.com', 'Sweden'),
  (4, 'Diego Romero', 'diego@example.com', 'Spain');

INSERT OR IGNORE INTO products (id, name, category, price) VALUES
  (1, 'Road Bike', 'Bikes', 1200.00),
  (2, 'Helmet', 'Accessories', 50.00),
  (3, 'Cycling Jersey', 'Apparel', 80.00),
  (4, 'Mountain Bike', 'Bikes', 1600.00);

INSERT OR IGNORE INTO orders (id, customer_id, order_date, status) VALUES
  (1, 1, '2024-06-28', 'delivered'),
  (2, 1, '2024-07-12', 'delivered'),
  (3, 2, '2024-07-19', 'shipped'),
  (4, 3, '2024-07-30', 'canceled'),
  (5, 2, '2024-08-02', 'delivered'),
  (6, 4, '2025-01-05', 'delivered');

INSERT OR IGNORE INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES
  (1, 1, 1, 1, 1200.00),
  (2, 1, 2, 2, 50.00),
  (3, 2, 2, 1, 50.00),
  (4, 2, 3, 2, 80.00),
  (5, 3, 4, 1, 1600.00),
  (6, 4, 3, 1, 80.00),
  (7, 5, 1, 1, 1150.00),
  (8, 5, 2, 1, 50.00),
  (9, 6, 4, 1, 1600.00),
  (10, 6, 2, 1, 55.00);
"""


def ensure_db(db_path: str = DB_PATH) -> None:
    fresh = not os.path.exists(db_path)
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            conn.executescript(SCHEMA_SQL)
            if fresh:
                conn.executescript(SEED_SQL)
    finally:
        conn.close()

# ================ Schema Introspection ==================

def introspect_schema(db_path: str = DB_PATH) -> str:
    """Return a compact, LLM-friendly schema description."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [r[0] for r in cur.fetchall()]
        lines = []
        for t in tables:
            cur = conn.execute(f"PRAGMA table_info({t})")
            cols = [f"{row['name']} {row['type']}" for row in cur.fetchall()]
            lines.append(f"TABLE {t} (" + ", ".join(cols) + ")")
        # Minimal foreign key hints
        lines.append("JOINS: orders.customer_id = customers.id; order_items.order_id = orders.id; order_items.product_id = products.id")
        return "\n".join(lines)
    finally:
        conn.close()

# ================ SQL Guardrails ==================

DANGEROUS = re.compile(r"\b(insert|update|delete|drop|create|alter|replace|pragma|attach|vacuum|reindex|grant|revoke)\b", re.I)
SELECT_LIKE = re.compile(r"^\s*(with\b.*?\)?\s*)?select\b", re.I | re.S)


def sanitize_sql(sql: str) -> str:
    sql = sql.strip()
    # Strip common markdown fences or "SQL:" prefixes
    sql = re.sub(r"^```\w*\n|```$", "", sql.strip(), flags=re.I | re.M)
    sql = re.sub(r"^\s*SQL\s*:\s*", "", sql, flags=re.I)
    # Remove trailing semicolon
    if sql.endswith(";"):
        sql = sql[:-1]
    # Basic checks
    if DANGEROUS.search(sql):
        raise ValueError("Refused: query contains dangerous keywords.")
    if not SELECT_LIKE.search(sql):
        raise ValueError("Refused: only a single SELECT (optionally with CTE) is allowed.")
    # Ensure single statement
    if ";" in sql:
        raise ValueError("Refused: multiple statements detected.")
    # Add LIMIT 100 if missing and not obviously aggregating huge sets
    if re.search(r"\blimit\b", sql, re.I) is None:
        sql += " LIMIT 100"
    return sql

# ================ LLM Prompts ==================

def llm_generate_sql(question: str, schema_text: str) -> str:
    client = openai_client()
    sys = (
        "You are a SQLite expert. Given a database schema and a user question, "
        "write exactly ONE safe SQL SELECT query (you may use CTEs). "
        "Rules: Use only listed tables/columns. Use ISO dates (YYYY-MM-DD). "
        "Prefer INNER JOINs unless the question implies missing rows. "
        "NEVER modify data. Return ONLY the SQL, no explanation, no code fences. "
        "If it cannot be answered from the schema, return: CANNOT_ANSWER -- <short reason>"
    )
    user = (
        f"SCHEMA\n{schema_text}\n\n"
        f"QUESTION\n{question}\n\n"
        "Return only SQL."
    )
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    sql = resp.choices[0].message.content.strip()
    return sql


def llm_answer(question: str, sql: str, columns: List[str], rows: List[Tuple[Any, ...]]) -> str:
    client = openai_client()
    # Downsample rows if needed
    rows_out = rows[:MAX_ROWS_TO_SEND]
    data_as_dicts = [dict(zip(columns, r)) for r in rows_out]
    sys = (
        "You are a helpful data analyst. You will receive: the original question, "
        "the SQL used, and the query results as JSON rows. Answer concisely, using "
        "ONLY the provided data. If results are empty, say so and suggest a useful "
        "follow-up query or a likely reason. If there are many rows, summarize aggregates. "
        "If there are important caveats, mention them briefly."
    )
    user = json.dumps(
        {
            "question": question,
            "sql": sql,
            "columns": columns,
            "rows": data_as_dicts,
        },
        ensure_ascii=False,
    )
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()

# ================ DB Exec ==================

def run_sql(sql: str, db_path: str = DB_PATH) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        return cols, [tuple(r) for r in rows]
    finally:
        conn.close()

# ================ Orchestration ==================

def ask(question: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing. Add it to your environment or .env file.")

    ensure_db(DB_PATH)
    schema_text = introspect_schema(DB_PATH)

    raw_sql = llm_generate_sql(question, schema_text)
    if raw_sql.upper().startswith("CANNOT_ANSWER"):
        reason = raw_sql.split("--", 1)[1].strip() if "--" in raw_sql else "Unknown reason"
        return f"I couldn't form a safe SQL query for this question: {reason}"

    try:
        safe_sql = sanitize_sql(raw_sql)
    except ValueError as e:
        return f"Refused to execute generated SQL: {e} \n\nSQL was:\n{raw_sql}"

    try:
        cols, rows = run_sql(safe_sql)
    except Exception as e:
        return f"The generated SQL failed to run: {e}\n\nSQL was:\n{safe_sql}"

    # Pass 2 to LLM for the final natural-language answer
    return llm_answer(question, safe_sql, cols, rows)

# ================ CLI ==================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SQL RAG demo: Question → SQL → Answer")
    parser.add_argument("question", type=str, help="Your question in natural language")
    args = parser.parse_args()

    print(ask(args.question))
