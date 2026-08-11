package trabajo.exception;

/**
 * ============================================================================
 * PUNTO 3 — Jerarquía de excepciones: NIVEL 3 (hoja) — 3 de 3
 * ============================================================================
 * Se lanza cuando el dato de entrada era válido en su FORMATO, pero la
 * operación viola una regla de NEGOCIO (ej. "no se puede crear el usuario
 * porque falló la persistencia", "no hay cupo disponible", etc.).
 *
 * Diferencia clave con ValidationException:
 *   - ValidationException  -> el dato en sí está mal formado.
 *   - BusinessRuleException -> el dato está bien formado, pero la regla de
 *     negocio no permite completar la operación en este momento/contexto.
 * ============================================================================
 */
public class BusinessRuleException extends DomainException {

    /**
     * @param rule descripción de la regla de negocio que se violó
     */
    public BusinessRuleException(String rule) {
        super("Regla de negocio violada: " + rule, "BUSINESS_RULE_VIOLATION");
    }
}
