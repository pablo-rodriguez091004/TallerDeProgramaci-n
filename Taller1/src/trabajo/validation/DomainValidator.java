package trabajo.validation;

/**
 * ============================================================================
 * PUNTO 4 — Interfaz funcional de validación
 * ============================================================================
 * @FunctionalInterface: tiene EXACTAMENTE un método abstracto (validate).
 * Eso es lo que permite implementarla con una expresión lambda o un method
 * reference en lugar de tener que escribir una clase completa cada vez.
 *
 * El método default "and" NO cuenta como segundo método abstracto (los
 * métodos default ya tienen cuerpo), así que la interfaz sigue siendo
 * funcional. Sirve para COMPONER validadores pequeños en uno más complejo,
 * sin que quien los usa (EmailValidator) necesite saber cómo está
 * implementada cada regla individual — esto es composición sobre herencia.
 *
 * @param <T> tipo de dato que se va a validar (String, un objeto de dominio, etc.)
 * ============================================================================
 */
@FunctionalInterface
public interface DomainValidator<T> {

    /**
     * Valida un valor según una regla específica.
     * @param value valor a validar
     * @return true si cumple la regla, false si no
     */
    boolean validate(T value);

    /**
     * Combina este validador con otro: el resultado solo es válido si
     * AMBOS lo son. Permite escribir cadenas como:
     *   validadorA.and(validadorB).and(validadorC)
     */
    default DomainValidator<T> and(DomainValidator<T> other) {
        return value -> this.validate(value) && other.validate(value);
    }
}
