package trabajo.exception;

/**
 * ============================================================================
 * PUNTO 3 — Jerarquía de excepciones: NIVEL 3 (hoja) — 2 de 3
 * ============================================================================
 * Se lanza cuando un dato de ENTRADA no cumple el formato/reglas esperadas
 * ANTES de intentar procesarlo (ej. un email con formato inválido).
 * Es la reemplazante directa del "IllegalArgumentException" genérico que
 * usaba el UserManager original — ahora el error tiene contexto de dominio.
 * ============================================================================
 */
public class ValidationException extends DomainException {

    /**
     * @param message explicación concreta de qué dato falló y por qué
     */
    public ValidationException(String message) {
        super(message, "VALIDATION_ERROR");
    }
}
