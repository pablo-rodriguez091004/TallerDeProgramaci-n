package trabajo.exception;

/**
 * 
 * PUNTO 3 — Jerarquía de excepciones de dominio: NIVEL 1 (raíz)
 * Raíz abstracta de TODA excepción de la aplicación.
 *
 * ¿Por qué abstracta? Para que nadie pueda hacer "new AppException(...)"
 * directamente — obliga a que siempre se lance una subclase concreta con
 * significado real (EntityNotFoundException, ValidationException, etc.),
 * nunca un error genérico sin contexto.
 *
 * ¿Por qué extiende RuntimeException y no Exception?
 * Porque son errores que, si el desarrollador de más arriba no los captura,
 * deben poder propagarse sin obligar a firmar "throws" en cada método
 * intermedio (excepciones no verificadas / unchecked). Esto es una decisión
 * de diseño común en aplicaciones modernas (Spring, por ejemplo, sigue este
 * mismo patrón).
 *
 * El errorCode es útil si luego expones una API REST: puedes mapear cada
 * código a un status HTTP (por ejemplo VALIDATION_ERROR -> 400,
 * ENTITY_NOT_FOUND -> 404) sin acoplar la excepción a la capa web.
 */
public abstract class AppException extends RuntimeException {

    private final String errorCode;

    protected AppException(String message, String errorCode) {
        super(message);
        this.errorCode = errorCode;
    }

    protected AppException(String message, String errorCode, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    /**
     * @return código corto identificando el tipo de error (ej. "VALIDATION_ERROR")
     */
    public String getErrorCode() {
        return errorCode;
    }
}
