package trabajo;

/**
 * ============================================================================
 * PUNTO 2 — Refactor SRP: Clase 5 de 5 — Auditoría
 * ============================================================================
 * Responsabilidad ÚNICA: dejar constancia de qué ocurrió en el sistema
 * (auditoría de negocio, no confundir con el logging técnico de SLF4J que
 * se agrega en el punto 3 — son capas distintas: esta clase registra HECHOS
 * DE NEGOCIO ("se creó el usuario X"), SLF4J registra EVENTOS TÉCNICOS
 * ("warn: email inválido recibido").
 * ============================================================================
 */
public class ActivityLogger {

    /**
     * Registra una actividad de negocio.
     * @param activity descripción de la actividad ocurrida
     */
    public void log(String activity) {
        // registro de logging / auditoría
    }
}
