# Microservices øvelser

I skal i dag arbejde videre med Microservice øvelserne fra i går.    
Der er ikke noget undervisning i dag, men jeg (Claus) er på Teams og kan kontaktes der for hjælp og feedback.

Vi lavede i går disse services:

1. **Account Service**:
   - Håndterer brugerkonti, herunder registrering, autentificering og profiladministration.
   - Behandler login, logout, passwordhåndtering og brugerroller.

7. **Currency Service**:
   - Håndterer omregning mellem forskellige valutaer for at sikre, at priserne vises korrekt afhængigt af brugerens valgte valuta.
   - Opdaterer valutakurser i realtid ved at integrere med eksterne valutakurseressourcer og API'er.
   - Giver funktionalitet til at indstille eller vælge en foretrukken valuta for både brugere og administratorer.

2. **Product Catalog Service**:
   - Styrer listen over tilgængelige produkter, inklusive detaljer såsom navn, beskrivelse, pris og billeder.
   - Tilbyder funktionalitet til at søge, filtrere og kategorisere produkter.

I dag skal i lave en UI Service, dvs. en frontend der interagerer med disse 3 services.

## UI Service med StreamLit

**Formål**: Skab en brugervenlig frontend der integrerer alle tre services til en sammenhængende e-commerce oplevelse.

**Framework**: StreamLit

**Opgavebeskrivelse**:

Jeres UI Service skal implementere følgende funktionaliteter:

### 1. Brugeradministration (Account Service integration)
- Login/logout side
- Registreringsformular for nye brugere
- Vis brugerinfo og mulighed for at redigere profil

### 2. Produktkatalog (Product Catalog Service integration)
- Vis liste over alle produkter
- Søgefunktion til at finde specifikke produkter
- Produktdetaljer side med billeder og beskrivelser
- Filtering og kategorisering af produkter

### 3. Valutahåndtering (Currency Service integration)
- Dropdown til at vælge foretrukken valuta
- Automatisk omregning af alle priser baseret på valgt valuta
- Vis aktuelle valutakurser

### Tekniske krav:
- Implementer HTTP requests til jeres 3 services (requests biblioteket)
- Brug StreamLit komponenter som `st.selectbox`, `st.form`, `st.columns` etc.

I kan evt. håndterer fejl vha try/catch
