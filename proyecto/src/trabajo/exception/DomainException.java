package trabajo.exception;

/**
 * ============================================================================
 * PUNTO 3 — Jerarquía de excepciones de dominio: NIVEL 2 (intermedio)
 * ============================================================================
 * Agrupa TODOS los errores que pertenecen a las reglas del negocio/dominio
 * (a diferencia, por ejemplo, de errores de infraestructura como "no hay
 * conexión a la base de datos", que en un diseño más grande tendrían su
 * propia rama, ej. InfrastructureException).
 *
 * Sigue siendo abstracta por la misma razón que AppException: es un nivel
 * de agrupación, no un error concreto que se deba lanzar directamente.
 *
 * Tener este nivel intermedio permite capturar TODOS los errores de dominio
 * de una sola vez cuando hace falta:
 *
 *   try {
 *       userService.createUser(...);
 *   } catch (DomainException e) {
 *       // captura EntityNotFoundException, ValidationException Y
 *       // BusinessRuleException con un solo catch
 *   }
 * ============================================================================
 */
public abstract class DomainException extends AppException {
    protected DomainException(String message, String errorCode) {
        super(message, errorCode);
    }
}
