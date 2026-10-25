# ADR 0001 — Hexagonal architecture organised by DDD bounded contexts

- **Status:** Accepted
- **Date:** 2026-10-24
- **Deciders:** Pablo Rodríguez (student, project owner); implementation assisted by an AI coding assistant (see `docs/USO_DE_IA.md`)
- **Scope:** `backend/` of MecaTrack, the booking and vehicle-tracking system for a car repair workshop
- **Format:** Nygard's ADR template (context, decision, consequences), extended with the alternatives that were considered

## 1. Context

MecaTrack is a Flask + SQLAlchemy + PostgreSQL application with a vanilla HTML/JS frontend. Before this decision (commit `7cca398`) the backend was a **layered "routes → repositories" design**:

- 9 Flask blueprints in `routes/` called module-level repository functions that used the global `db.session`.
- Business rules lived **inside the HTTP handlers**. For example, the 30 % deposit and the creation of both payments were coded in `POST /appointments`, and the "paying the deposit confirms the appointment" rule lived in `POST /payments/<id>/pay`.
- The core scheduling engine (`utils/scheduling_engine.py`) imported the repositories directly, so it could not run without a database.
- All 31 tests were integration tests against PostgreSQL (≈10 s). There was **no unit test and no mock**: no rule could be tested in isolation.
- Lab guide 6 adds two new external dependencies: Colombian open-data APIs (datos.gov.co and the DANE geoportal) that can fail, plus DuckDB for analytics. Without boundaries, those libraries would leak into the business code the same way SQLAlchemy already had.

Forces:

1. The scheduling rule (simultaneous bay **and** mechanic availability, half-open intervals `[start, end)`) is the heart of the product and must be testable without infrastructure.
2. The HTTP contract used by the frontend (paths, status codes, Spanish `{"error": ...}` bodies) and the documented `/api/v1` contract (OpenAPI 3.0.3) **must not change**.
3. The CI pipeline must stay green during the whole refactor.
4. This is a one-person academic project: the solution has to be explainable and cannot rely on heavy frameworks.

## 2. Decision

We adopt **Hexagonal Architecture (Ports and Adapters)** (Cockburn, 2005). The code is split into **four layers**, and inside the core layers it is split again by **DDD bounded context** (Evans, 2003).

```
            ┌──────────────────────── bootstrap.py (composition root) ────────────────────────┐
            │                                                                                  │
 HTTP ──►  api/  ──►  application/  ──►  domain/  ◄── implements ports ──  infrastructure/  ──► PostgreSQL,
 (Flask)   driving    use cases (DI by   entities, rules,                   driven adapters        datos.gov.co,
           adapters   constructor)       PORTS (ABC)                                               DANE, Gemini, DuckDB
```

| Layer | Contents | May import |
|---|---|---|
| `domain/` | Entities (dataclasses), pure business rules, **ports** (abstract base classes) and domain errors | Python standard library only |
| `application/` | One service per use-case group. Every dependency is a port received **through the constructor** | `domain` |
| `api/` | Flask blueprints (legacy + `/api/v1` with flask-smorest), schemas, session adapter, mapping of domain errors to HTTP | `application`, `domain` |
| `infrastructure/` | SQLAlchemy models and repositories, unit of work, Werkzeug hasher, Gemini gateway, resilient HTTP client, open-data clients, DuckDB analytics | `domain` |
| `bootstrap.py` | The **only** place where concrete adapters are instantiated and injected | everything |

The dependency rule is **enforced by a test**, not just by convention. `tests/unit/test_architecture.py` parses every file with `ast` and fails if:

- `domain` imports anything outside the standard library (Flask, SQLAlchemy, httpx, DuckDB, …);
- `application` imports a framework or IO library;
- `api` imports `infrastructure`; or
- `infrastructure` imports `api` or `application`.

A mutation check (adding `import flask` to a domain module) made the test fail as expected.

### 2.1 Bounded contexts

| Bounded context | Package | Subdomain type | Main concepts | Ports (driven side) |
|---|---|---|---|---|
| **Scheduling** | `scheduling` | **Core** | Appointment, blocking statuses, half-open slot overlap, `ResourceAllocator` (bay + mechanic) | `AppointmentRepository` |
| **Payments** | `payments` | Supporting | Payment (deposit / balance), 30/70 split, "deposit confirms appointment" | `PaymentRepository`, `Clock` |
| **Service tracking** | `tracking` | Supporting | Tracking record, part usage, all-or-nothing stock discount | `TrackingRepository`, `PartRepository` |
| **Workshop management** | `catalog` | Supporting | Business, bay, service catalogue, part, vehicle | `BusinessRepository`, `BayRepository`, `ServiceRepository`, `PartRepository`, `VehicleRepository` |
| **Identity & access** | `identity` | Generic | User, role, credentials | `UserRepository`, `PasswordHasher` |
| **AI assistant** | `ai_assistant` | Supporting | RAG retrieval, prompts, answer validation, per-user quota | `LlmGateway`, `AiCallLog` |
| **Market data** | `market_data` | Generic (external data) | Open-data sources, snapshots, analytics result, source health | `DataSource` (+ 3 specialisations), `SnapshotStore`, `HealthMonitor`, `MarketAnalytics` |

Two shared ports cut across contexts: `UnitOfWork` and `Clock` (`domain/shared`). In total the domain exposes **18 abstract ports**.

### 2.2 Context map (relationships)

- **Scheduling → Payments (customer/supplier, same transaction).** Booking an appointment creates its deposit and balance payments in one unit of work, and paying the deposit confirms the appointment. Payments therefore reads `AppointmentRepository`. This coupling is deliberate (atomicity) and documented here as a known trade-off.
- **Scheduling → Workshop management and Identity (conformist).** The allocator consumes bays and active mechanics through their ports, as they are.
- **Market data ↔ datos.gov.co / DANE (anticorruption layer).** The adapters in `infrastructure/market_data` translate Socrata (SoQL, `$limit/$offset` paging) and ArcGIS REST (`resultOffset` paging, errors inside HTTP 200) into plain records. They also translate `httpx`, retry and circuit-breaker errors into the domain error `DataSourceUnavailable`. The external models never reach the core.
- **AI assistant → LLM provider (anticorruption layer).** `GeminiGateway` maps SDK and HTTP errors to `LlmTimeout`, `LlmRateLimited`, `LlmProviderError` and `LlmNotConfigured`, which are defined in the domain.

### 2.3 Dependency injection

- Every application service receives its ports through `__init__`, for example `AppointmentService(appointments, vehicles, services, allocator, payments, uow)` and `PaymentService(payments, appointments, uow, clock)`. Even the clock is injected, so time-dependent rules are deterministic in tests.
- The domain service `ResourceAllocator(bays, users, appointments)` follows the same rule.
- **Manual DI with a single composition root** (`bootstrap.build_container`) was preferred over a DI library: the whole object graph is about 60 readable lines.
- The adapters are stateless per request (they use Flask-SQLAlchemy's request-scoped session), so the container is built once per app. The circuit breakers live there too, because their state must survive between requests.

### 2.4 Resilience of the external adapters (driven side)

- Each external host has its own **circuit breaker**: CLOSED → OPEN after 3 consecutive transient failures, OPEN → HALF_OPEN after 30 s, then one trial call → CLOSED or back to OPEN (Nygard, 2018; Fowler, 2014).
- Inside the breaker, transient failures (timeouts, connection errors, HTTP 429/5xx) are **retried with exponential backoff and equal jitter**: ceiling `min(8, 0.5·2^(n-1))` s (Brooker, 2015).
- 4xx responses are neither retried nor counted, because they signal a bad request, not an unhealthy dependency.
- `CircuitOpenError` is never retried, so the client fails fast.

## 3. Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| **Keep the layered routes → repositories design** and only add services | Does not stop framework imports in business code, and still cannot unit-test the allocator. Fails the "domain independent of IO" requirement. |
| **Use the SQLAlchemy models as domain entities** | Less code, but the core would depend on SQLAlchemy and on lazy-loading sessions; the architecture test would be impossible. |
| **Package by context at the top level** (`scheduling/{domain,application,…}`) | Equally valid in DDD. Rejected because the lab guide asks for four visible top-level layers (`domain/application/api/infrastructure`). Contexts are kept as sub-packages instead. |
| **DI framework** (e.g. `dependency-injector`) | Adds a dependency and "magic" for a 12-service graph. A composition root is explicit and easy to defend. |
| **Third-party resilience library** (e.g. `tenacity`, `pybreaker`) | The guide asks to implement the circuit breaker and backoff, and own components can be tested with an injected clock, sleep and RNG. The libraries remain a sensible choice for production. |

## 4. Consequences

### Positive

- **Testability.** 73 unit tests (use cases with `unittest.mock.create_autospec` on each port, pure rules, circuit breaker, retry, DuckDB adapter) run in **1.12 s with no database**. Before, the suite had 0 unit tests. The 42 integration tests (14.7 s) still exercise the real HTTP + PostgreSQL path.
- **No regressions.** The original 31 tests pass with unchanged assertions. 7 characterisation tests written during the refactor were run first against the original code (7/7) and then against the new one (7/7). `flask db check` reports no schema change, and the exported `openapi.json` is byte-identical after phase 1.
- **Replaceable infrastructure.** Adding DuckDB and two external APIs did not touch any existing use case. A failing source is isolated by its own breaker: when datos.gov.co fails, the DANE source keeps working (covered by `test_outage_opens_the_datos_gov_circuit_but_dane_still_works`).
- **Explicit business language.** Rules such as `split_price`, `overlaps`, `confirms_appointment` and `ensure_participant` are named, pure and documented in one place.

### Negative / costs

- **More code and some duplication.** Every entity exists twice (domain dataclass and ORM model). A generic mapper (`SqlAlchemyRepository`) keeps this small, but adding a column now means editing two classes.
- **Detached entities need explicit `save()`.** Mutating an entity no longer persists it automatically; forgetting `repository.save(...)` is a new kind of bug. The integration tests are the safety net.
- **Two error languages inside application.** Use cases keep the Spanish messages of the legacy routes and the English messages of `/api/v1` so that neither contract changes. A future ADR could move translation to the API layer, keyed by error `code`.
- **Known context coupling.** Payments depends on the scheduling repository (§2.2). Splitting them would require domain events or an outbox, which is out of scope.
- **Learning curve.** Ports, adapters and a composition root are more concepts than "a route calls a repository". This ADR and `docs/guia-sustentacion.md` exist to reduce that cost.

### Follow-up

- `python-services/` (legacy scripts) was already broken before this ADR: it imports a `models.Usuario` that does not exist. It is outside the hexagon and should be migrated or removed.
- If the workshop grows to several businesses, the Identity ↔ Workshop management relationship needs an explicit mechanic → business link, as `domain/scheduling/allocation.py` notes.

## 5. References

- Brooker, M. (2015, March 4). *Exponential backoff and jitter*. AWS Architecture Blog. https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
- Cockburn, A. (2005). *Hexagonal architecture*. https://alistair.cockburn.us/hexagonal-architecture/
- Evans, E. (2003). *Domain-driven design: Tackling complexity in the heart of software*. Addison-Wesley.
- Fowler, M. (2014, March 6). *CircuitBreaker*. martinfowler.com. https://martinfowler.com/bliki/CircuitBreaker.html
- Nygard, M. T. (2011, November 15). *Documenting architecture decisions*. Cognitect. https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- Nygard, M. T. (2018). *Release it! Design and deploy production-ready software* (2nd ed.). Pragmatic Bookshelf.
