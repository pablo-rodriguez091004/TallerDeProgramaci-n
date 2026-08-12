package trabajo.service;

import trabajo.exception.EntityNotFoundException;
import trabajo.model.Report;
import trabajo.repository.Repository;

/**
 * ============================================================================
 * PUNTO 5 — Servicio de dominio #2, con Repository inyectado por CONSTRUCTOR
 * ============================================================================
 * Segundo servicio requerido por el enunciado ("al menos 2 servicios del
 * dominio"). Misma idea que UserService: depende de la abstracción
 * Repository<Report, Long>, nunca de una implementación concreta.
 * ============================================================================
 */
public class ReportService {

    private final Repository<Report, Long> reportRepository;

    public ReportService(Repository<Report, Long> reportRepository) {
        this.reportRepository = reportRepository;
    }

    public Report getReport(Long id) {
        return reportRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Report", id));
    }

    public Report save(Report report) {
        return reportRepository.save(report);
    }
}
