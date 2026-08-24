# Sesión 3 – Galería de Implementaciones de Estructuras de Datos

Proyecto Maven en Java que implementa **desde cero** (sin `java.util.*`) las
cuatro estructuras de datos clásicas usando **Generics**: `LinkedList`,
`Stack`, `Queue` y `BST` (Árbol Binario de Búsqueda). Incluye benchmarks,
pruebas unitarias con JUnit 5 + AssertJ, integración con el proyecto
semestral (sistema de reserva de espacios) y un pipeline de CI/CD.

## Estructura del proyecto

```
sesion3-estructuras/
├── pom.xml
├── .github/workflows/ci.yml          # Pipeline CI/CD (GitHub Actions)
├── src/main/java/com/reservas/
│   ├── estructuras/                  # Punto 1 y 2: estructuras + JavaDoc + @complexity
│   │   ├── LinkedList.java
│   │   ├── Stack.java
│   │   ├── Queue.java
│   │   ├── BST.java
│   │   └── EmptyStructureException.java
│   ├── benchmark/
│   │   └── BenchmarkRunner.java      # Punto 2: benchmark 1.000 / 10.000 / 100.000
│   ├── integration/                  # Punto 4: integración al proyecto semestral
│   │   ├── Reservation.java
│   │   ├── ReservationWaitlistService.java   (usa Queue)
│   │   ├── ReservationActionHistory.java     (usa Stack)
│   │   ├── DailyBookingSchedule.java         (usa LinkedList)
│   │   └── ReservationDateIndex.java         (usa BST)
│   └── Main.java                     # Demo ejecutable de todo lo anterior
├── src/test/java/com/reservas/estructuras/
│   ├── LinkedListTest.java           # Punto 3: ≥5 pruebas JUnit5 + AssertJ
│   ├── StackTest.java
│   ├── QueueTest.java
│   └── BSTTest.java
└── PRESENTACION.md                   # Guion de la presentación técnica de 5 minutos
```

## Requisitos

- Java 17+
- Maven 3.8+

## Cómo abrir en VS Code

1. Descomprime el archivo `.zip` en cualquier carpeta.
2. Abre esa carpeta en VS Code (`File > Open Folder...`).
3. Con la extensión **Extension Pack for Java** instalada, VS Code detectará
   automáticamente el `pom.xml` y configurará el proyecto.

## Comandos principales

Compilar el proyecto:

```bash
mvn compile
```

Ejecutar las pruebas unitarias (JUnit 5 + AssertJ):

```bash
mvn test
```

Ejecutar la demo (estructuras + casos de uso integrados):

```bash
mvn compile exec:java
```

Ejecutar el benchmark (1.000 / 10.000 / 100.000 elementos):

```bash
mvn compile exec:java@run-benchmark
```

## Punto 1 – Estructuras de datos propias

Cada estructura (`LinkedList<T>`, `Stack<T>`, `Queue<T>`, `BST<T extends Comparable<T>>`)
está implementada con nodos enlazados propios (clase interna `Node<T>`), sin
usar ninguna clase de `java.util.*`. Todas incluyen los métodos
fundamentales: inserción, eliminación, búsqueda, `size()`, `isEmpty()`,
`clear()` y `toArray()`, además de una excepción propia
(`EmptyStructureException`) para operaciones inválidas sobre estructuras
vacías.

## Punto 2 – JavaDoc y complejidad Big-O

Cada método público documenta su complejidad con la etiqueta personalizada
`@complexity` (por ejemplo `@complexity O(1)` o `@complexity O(log n) average, O(n) worst case`).
Puedes generar el HTML de JavaDoc con:

```bash
mvn javadoc:javadoc
```

(si el plugin `maven-javadoc-plugin` no está en el `pom.xml` de tu entorno,
puedes agregarlo o simplemente leer los comentarios en el código fuente).

El benchmark (`BenchmarkRunner`) mide tiempos de inserción, búsqueda y
eliminación para **1.000, 10.000 y 100.000** elementos en cada estructura,
imprimiendo una tabla comparativa en consola.

## Punto 3 – Pruebas unitarias

Cada estructura tiene entre 7 y 8 pruebas con JUnit 5 + AssertJ (mínimo 5
exigido) cubriendo: estructura vacía, inserción, búsqueda, eliminación y
manejo de excepciones. El pipeline `.github/workflows/ci.yml` ejecuta
`mvn test` automáticamente en cada push/PR.

## Punto 4 – Integración con el proyecto semestral

Se integran las cuatro estructuras en casos de uso reales del sistema de
reserva de espacios:

| Estructura | Clase de integración | Caso de uso |
|---|---|---|
| `Queue` | `ReservationWaitlistService` | Lista de espera FIFO cuando un espacio está lleno |
| `Stack` | `ReservationActionHistory` | Historial de acciones para deshacer (undo) |
| `LinkedList` | `DailyBookingSchedule` | Agenda ordenada de reservas de un recurso |
| `BST` | `ReservationDateIndex` | Índice de reservas por fecha para reportes y disponibilidad |

`Main.java` ejecuta una demo de los cuatro casos de uso.

## Presentación técnica (5 minutos)

Ver `PRESENTACION.md` para el guion completo, o el archivo `.pptx` adjunto
con las diapositivas listas para exponer ante el grupo.
