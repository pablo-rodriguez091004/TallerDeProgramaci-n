# Video script (English) – Lab guide 6: Hexagonal architecture, DDD and Colombian open data

**Target length:** about 2 min 30 s (≤ 3 min). **Spoken words:** 320 (≈ 137 s at 140 words per minute).
**Before recording:** run `./scripts/demo.sh` (normal mode). Have open: the "Mercado" page, VS Code with `backend/`, and a terminal.
Text in *[brackets]* is what to show on screen; it is not read aloud.

---

### 1. Hexagonal architecture (≈ 40 s)

*[VS Code: folders `domain`, `application`, `api`, `infrastructure` and `bootstrap.py`]*

"Hi, I'm [YOUR NAME]. This is MecaTrack, a booking system for a car workshop. In this lab I refactored the backend into a hexagonal architecture with four layers. The domain holds entities, business rules and ports, which are abstract interfaces, and it only uses the Python standard library. Application services receive those ports through the constructor, and the infrastructure layer implements them with SQLAlchemy, HTTP clients and DuckDB."

*[Open `tests/unit/test_architecture.py`, then the terminal with pytest green]*

"A test reads every import and fails if the domain imports Flask or SQLAlchemy. Thanks to dependency injection, I test the booking service with mocks and no database: the full suite has 115 passing tests, also green in GitHub Actions."

### 2. Colombian open data and DuckDB (≈ 40 s)

*[Mercado page → click "Actualizar datos"]*

"The workshop panel downloads two public Colombian APIs: the vehicle registry from datos.gov.co and the 2018 census population from the DANE geoportal. DuckDB reads the JSON and runs analytical SQL. For example, it analyses twenty-two million active vehicles: the median motorcycle is nine years old, and the median car sixteen. A second query joins both sources to compute vehicles per thousand inhabitants by department."

### 3. Circuit breaker states (≈ 40 s)

*[Browser with `./scripts/demo.sh --breaker-abierto` running: click "Actualizar datos" twice. Then a terminal with `./scripts/demo.sh --ciclo` to show the full cycle back to CLOSED]*

"Each external host has its own circuit breaker. This is a controlled demo: I point datos.gov.co to an invalid host. After three consecutive failures the breaker goes from CLOSED to OPEN, and calls are rejected instantly without using the network. The DANE breaker stays CLOSED. After thirty seconds it becomes HALF-OPEN and lets one trial call through; if it succeeds, it closes again. Transient errors are retried with exponential backoff and jitter."

### 4. Critical evaluation of an AI suggestion (≈ 25 s)

*[Show `infrastructure/analytics/queries.py`, the `clave_resuelta` block]*

"I used an AI assistant. One suggestion was wrong: it wrote a left join with a correlated subquery, and DuckDB rejected it at runtime. I rewrote it to resolve the join key first. [IF YOU USED COPILOT, DESCRIBE YOUR OWN EXAMPLE HERE.] The lesson: AI is fast, but every output must be verified."

### 5. Summary (≈ 15 s)

"To sum up: ports and adapters keep the business core independent, DDD bounded contexts organise the code, and circuit breakers make external data safe to use. Thanks for watching."

---

## English resource prepared before the session: glossary

| Term | Meaning in this project |
|---|---|
| Port | Abstract interface owned by the domain (e.g. `AppointmentRepository`) |
| Adapter | Concrete implementation of a port (e.g. `SqlAlchemyAppointmentRepository`) |
| Composition root | The single place where adapters are created and injected (`bootstrap.py`) |
| Bounded context | Part of the domain with its own language and model (Scheduling, Payments, Market data, …) |
| Anticorruption layer | Translation layer that keeps external models out of the core (open-data clients) |
| Circuit breaker | Guard with three states (CLOSED, OPEN, HALF-OPEN) that stops calling a failing dependency |
| Exponential backoff with jitter | Retry waits that double each time, with randomness to avoid synchronized retries |
| ADR | Architecture Decision Record: context, decision and consequences of a design choice |
