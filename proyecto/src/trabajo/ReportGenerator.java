package trabajo;

/**
 * ============================================================================
 * PUNTO 2 — Refactor SRP: Clase 3 de 5 — Reportería
 * ============================================================================
 * Responsabilidad ÚNICA: generar reportes.
 *
 * OBSERVACIÓN CRÍTICA (evaluación del código sugerido por Copilot):
 * en la versión original que Copilot propuso, esta clase se definía pero
 * NUNCA se usaba dentro de UserManager — quedaba como código muerto. Aquí
 * se corrige: UserManager SÍ la usa a través de un método generateReport()
 * que delega correctamente en esta clase (ver UserManager.java).
 * ============================================================================
 */
public class ReportGenerator {

    /**
     * Genera un reporte. En una implementación real, aquí iría la lógica
     * de armado del documento (texto, PDF, Excel, etc.).
     * @return contenido del reporte generado
     */
    public String generate() {
        return "";
    }
}
