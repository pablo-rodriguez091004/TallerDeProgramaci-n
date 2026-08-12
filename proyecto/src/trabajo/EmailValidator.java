package trabajo;

import trabajo.validation.DomainValidator;
import trabajo.validation.ValidationUtils;

/**
 * ============================================================================
 * PUNTO 2 — Refactor SRP: Clase 4 de 5 — Validación
 * PUNTO 4 — Uso real de la interfaz funcional DomainValidator
 * ============================================================================
 * Responsabilidad ÚNICA: decidir si un email es válido.
 *
 * Aquí se ven los 4 elementos que pide el punto 4:
 *   - 3 expresiones lambda diferentes (una de una línea, una con bloque de
 *     código, y una que reutiliza lógica de otra parte del proyecto)
 *   - 1 method reference (ValidationUtils::isNotBlank)
 *
 * Cada regla vive aislada en su propio DomainValidator y se combinan con
 * .and(...) — así, si mañana el negocio pide una regla nueva (por ejemplo,
 * "no permitir emails temporales de mailinator.com"), se agrega UNA línea
 * nueva sin tocar las reglas existentes (esto es además un ejemplo de OCP:
 * extendemos comportamiento sin modificar el que ya funciona).
 * ============================================================================
 */
public class EmailValidator {

    // 1) Lambda de una sola expresión: valida presencia del símbolo "@"
    private final DomainValidator<String> hasAtSymbol =
            email -> email != null && email.contains("@");

    // 2) Lambda con cuerpo de bloque: valida un rango de longitud
    private final DomainValidator<String> hasValidLength = email -> {
        if (email == null) return false;
        return email.length() >= 5 && email.length() <= 100;
    };

    // 3) Lambda que reutiliza otra clase del proyecto: valida el dominio permitido
    private final DomainValidator<String> hasAllowedDomain = email ->
            email != null && (email.endsWith(".com") || email.endsWith(".co"));

    // 4) Method reference a un método estático propio (no es una lambda escrita
    //    a mano, es una REFERENCIA directa a un método que ya existe)
    private final DomainValidator<String> notBlank = ValidationUtils::isNotBlank;

    // Composición de las 4 reglas en un único validador final
    private final DomainValidator<String> fullValidation =
            notBlank.and(hasAtSymbol).and(hasValidLength).and(hasAllowedDomain);

    /**
     * @param email correo a validar
     * @return true si cumple TODAS las reglas de negocio configuradas
     */

    public boolean isValid(String email) {
        return fullValidation.validate(email);
    }
    public String explainInvalid(String email) {
        if (!notBlank.validate(email)) {
            return "el email está vacío o es nulo";
        }
        if (!hasAtSymbol.validate(email)) {
            return "el email no contiene el símbolo @";
        }
        if (!hasValidLength.validate(email)) {
            return "la longitud del email no está entre 5 y 100 caracteres";
        }
        if (!hasAllowedDomain.validate(email)) {
            return "el dominio del email no está permitido (debe terminar en .com o .co)";
        }
        return null;
    }
}

