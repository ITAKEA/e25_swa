```mermaid 
graph TB
    subgraph "Client Layer"
        WEB[Web Application]
        MOBILE[Mobile App]
    end

    subgraph "API Gateway"
        GATEWAY[API Gateway<br/>Route & Auth]
    end

    subgraph "Core Services"
        USER[User Service<br/>Authentication & Profiles]
        PRODUCT[Product Service<br/>Catalog & Inventory]
        ORDER[Order Service<br/>Order Management]
        PAYMENT[Payment Service<br/>Transactions]
        CART[Cart Service<br/>Shopping Cart]
        SEARCH[Search Service<br/>Product Discovery]
    end

    subgraph "Supporting Services"
        NOTIFY[Notification Service<br/>Email & SMS]
        REVIEW[Review Service<br/>Ratings & Comments]
        SHIPPING[Shipping Service<br/>Delivery Tracking]
    end

    subgraph "Data Layer"
        USERDB[(User DB)]
        PRODUCTDB[(Product DB)]
        ORDERDB[(Order DB)]
        CACHE[(Redis Cache)]
    end

    subgraph "External Services"
        PAYGATE[Payment Gateway<br/>Stripe/PayPal]
        SHIPAPI[Shipping API<br/>FedEx/UPS]
    end

    WEB --> GATEWAY
    MOBILE --> GATEWAY
    
    GATEWAY --> USER
    GATEWAY --> PRODUCT
    GATEWAY --> ORDER
    GATEWAY --> CART
    GATEWAY --> SEARCH
    GATEWAY --> REVIEW

    USER --> USERDB
    USER --> CACHE
    
    PRODUCT --> PRODUCTDB
    PRODUCT --> CACHE
    
    CART --> CACHE
    
    SEARCH --> PRODUCTDB
    
    ORDER --> ORDERDB
    ORDER --> PAYMENT
    ORDER --> SHIPPING
    ORDER --> NOTIFY
    
    PAYMENT --> PAYGATE
    
    SHIPPING --> SHIPAPI
    SHIPPING --> NOTIFY
    
    REVIEW --> PRODUCTDB
    
    style GATEWAY fill:#4A90E2
    style USER fill:#7ED321
    style PRODUCT fill:#7ED321
    style ORDER fill:#7ED321
    style PAYMENT fill:#F5A623
    style CART fill:#7ED321
    style SEARCH fill:#7ED321
    style NOTIFY fill:#BD10E0
    style REVIEW fill:#BD10E0
    style SHIPPING fill:#BD10E0

    ```