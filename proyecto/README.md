# Sesión 2 — SOLID, Excepciones e Interfaces

Proyecto Maven listo para abrir en VS Code (extensión "Extension Pack for Java").
Cada clase está en su propio archivo, en el paquete que le corresponde según su
responsabilidad — así es como debe verse un proyecto Java organizado por capas.

## Cómo abrirlo

1. Descomprime el `.zip`.
2. En VS Code: `Archivo > Abrir carpeta...` y selecciona la carpeta `proyecto/`.
3. Si tienes la extensión de Java instalada, VS Code detecta el `pom.xml`
   automáticamente y descarga las dependencias (SLF4J, JUnit 5, AssertJ, Mockito).
4. Para correr los tests: clic derecho sobre `test/trabajo/service/UserServiceTest.java`
   → "Run Tests", o desde terminal: `mvn test`.

## Estructura del proyecto

```
proyecto/
├── pom.xml
├── README.md
├── PR_DESCRIPTION.md          ← plantilla de PR en inglés (punto 6)
├── src/trabajo/
│   ├── bad/
│   │   └── UserManagerGodClass.java     ← PUNTO 1: código original + análisis SOLID
│   │
│   ├── UserRepository.java              ← PUNTO 2: persistencia
│   ├── EmailService.java                ← PUNTO 2: notificación
│   ├── ReportGenerator.java             ← PUNTO 2: reportería
│   ├── EmailValidator.java              ← PUNTO 2 + 4: validación (usa DomainValidator)
│   ├── ActivityLogger.java              ← PUNTO 2: auditoría
│   ├── UserManager.java                 ← PUNTO 2 + 3: coordinador con excepciones y logging
│   │
│   ├── exception/                       ← PUNTO 3: jerarquía de excepciones
│   │   ├── AppException.java            (nivel 1, abstracta)
│   │   ├── DomainException.java         (nivel 2, abstracta)
│   │   ├── EntityNotFoundException.java (nivel 3)
│   │   ├── ValidationException.java     (nivel 3)
│   │   └── BusinessRuleException.java   (nivel 3)
│   │
│   ├── validation/                      ← PUNTO 4: interfaz funcional
│   │   ├── DomainValidator.java         (@FunctionalInterface)
│   │   └── ValidationUtils.java         (fuente del method reference)
│   │
│   ├── model/                           ← modelos de dominio usados en punto 5
│   │   ├── User.java
│   │   └── Report.java
│   │
│   ├── repository/                      ← PUNTO 5: DIP con Repository<T, ID>
│   │   ├── Repository.java              (interfaz genérica)
│   │   ├── InMemoryUserRepository.java
│   │   └── InMemoryReportRepository.java
│   │
│   └── service/                         ← PUNTO 5: servicios con inyección por constructor
│       ├── UserService.java
│       └── ReportService.java
│
└── test/trabajo/service/
    └── UserServiceTest.java             ← PUNTO 6: 6 pruebas JUnit 5 + AssertJ + Mockito
```

## Resumen de cada punto

### Punto 1 — Análisis SOLID (`src/trabajo/bad/UserManagerGodClass.java`)

Violaciones **confirmadas** por el código dado:
- **SRP**: 5 responsabilidades distintas en una sola clase (persistencia, notificación,
  reportería, validación, auditoría).
- **OCP**: agregar comportamiento nuevo obliga a modificar la clase existente, no hay
  abstracciones para extenderla.

Violaciones **condicionales** (el fragmento no muestra campos/dependencias, así que solo
se pueden inferir):
- **DIP**: si los métodos usan implementaciones concretas en vez de interfaces.
- **ISP**: si se agrupan los 5 métodos en una interfaz, un cliente que solo necesite uno
  quedaría forzado a depender de los otros cuatro.

**No aplica**: LSP (no hay herencia ni polimorfismo en el fragmento).

### Punto 2 — Refactor SRP

Se separaron las 5 responsabilidades en 5 clases (`UserRepository`, `EmailService`,
`ReportGenerator`, `EmailValidator`, `ActivityLogger`) más un coordinador (`UserManager`)
que orquesta sin implementar lógica de negocio directamente. `ReportGenerator`, que en el
código original de Copilot quedaba sin usar, ahora se invoca correctamente desde
`UserManager.generateReport()`.

### Punto 3 — Jerarquía de excepciones + SLF4J

`AppException` (abstracta) → `DomainException` (abstracta) → `EntityNotFoundException` /
`ValidationException` / `BusinessRuleException`. Integradas en `UserManager` con logging
en 3 niveles: `warn` (error esperable del usuario), `error` (fallo interno inesperado,
con stack trace) e `info` (camino feliz).

### Punto 4 — Interfaz funcional

`DomainValidator<T>` con un único método abstracto `validate(T)` y un método `default and(...)`
para componer validadores. Implementada en `EmailValidator` con 3 lambdas distintas
(expresión simple, bloque de código, reutilización de lógica) y 1 method reference
(`ValidationUtils::isNotBlank`).

### Punto 5 — DIP con Repository genérico

`Repository<T, ID>` define las operaciones CRUD básicas. `UserService` y `ReportService`
reciben su repositorio correspondiente **por constructor**, nunca lo instancian con `new`
— eso es DIP aplicado correctamente, a diferencia de `UserManager` (punto 2), que todavía
crea sus dependencias internamente.

### Punto 6 — Pruebas + PR

6 pruebas en `UserServiceTest` (superan el mínimo de 5) que validan: lanzamiento de
`ValidationException`, lanzamiento de `EntityNotFoundException`, creación exitosa de
usuario, jerarquía de herencia de excepciones, `errorCode` de cada excepción, y formato
del mensaje de error. La plantilla de PR en inglés está en `PR_DESCRIPTION.md`.
