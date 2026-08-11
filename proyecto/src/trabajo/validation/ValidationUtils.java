package trabajo.validation;

/**
 * ============================================================================
 * PUNTO 4 — Utilidades de validación (fuente del "method reference")
 * ============================================================================
 * Clase de utilidades con métodos estáticos. Su método isNotBlank() es el
 * que se referencia como "ValidationUtils::isNotBlank" en EmailValidator —
 * esa es la forma más limpia de reutilizar un método ya escrito como si
 * fuera una lambda, sin duplicar su lógica.
 * ============================================================================
 */
public final class ValidationUtils {

    // Constructor privado: es una clase de solo utilidades, no se instancia.
    private ValidationUtils() {}

    /**
     * @param value texto a evaluar
     * @return true si NO es null y tiene contenido distinto de espacios en blanco
     */
    public static boolean isNotBlank(String value) {
        return value != null && !value.trim().isEmpty();
    }
}
