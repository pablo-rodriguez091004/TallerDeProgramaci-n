package trabajo;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import trabajo.exception.ValidationException;
import trabajo.exception.BusinessRuleException;

/**
 * ============================================================================
 * PUNTO 2 + 3 — Clase coordinadora final (no implementa lógica de negocio
 * directamente, solo ORQUESTA las 5 clases separadas por SRP)
 * ============================================================================
 * Esta es la versión FINAL de tu UserManager: aplica SRP (delega en 4
 * colaboradores en vez de hacer todo ella misma), usa las excepciones de
 * dominio del punto 3 en vez de IllegalArgumentException genérica, y agrega
 * logging técnico con SLF4J en 3 niveles.
 *
 * SIGUE PENDIENTE: esta clase todavía instancia sus dependencias con "new"
 * en el constructor por defecto — eso sigue violando DIP. La solución
 * completa a ese problema está en trabajo.service.UserService (punto 5),
 * que recibe sus dependencias por constructor en vez de crearlas. Se deja
 * así para mantener continuidad con tu ejercicio del punto 2 original;
 * en un proyecto real, este UserManager terminaría siendo reemplazado por
 * UserService.
 * ============================================================================
 */
public class UserManager {

    private static final Logger logger = LoggerFactory.getLogger(UserManager.class);

    private final UserRepository repository;
    private final EmailService emailService;
    private final EmailValidator validator;
    private final ActivityLogger activityLogger;
    private final ReportGenerator reportGenerator;

    public UserManager(UserRepository repository, EmailService emailService,
                        EmailValidator validator, ActivityLogger activityLogger,
                        ReportGenerator reportGenerator) {
        this.repository = repository;
        this.emailService = emailService;
        this.validator = validator;
        this.activityLogger = activityLogger;
        this.reportGenerator = reportGenerator;
    }

    /**
     * Crea un usuario, orquestando validación, persistencia, notificación
     * y auditoría. Lanza excepciones de dominio en vez de errores genéricos.
     */
    public void createUser(String name, String email) {
        if (!validator.isValid(email)) {
            // Se pide la razón EXACTA del fallo (cuál regla no se cumplió)
            // en vez de un mensaje genérico de "email inválido".
            String razon = validator.explainInvalid(email);
            // warn: es un error esperable causado por el usuario final,
            // no un fallo interno del sistema.
            logger.warn("Intento de creación de usuario con email inválido: {} ({})", email, razon);
            throw new ValidationException("Email inválido \"" + email + "\": " + razon);
        }
        try {
            repository.createUser(name, email);
            emailService.sendWelcomeEmail(email);
            activityLogger.log("Usuario creado: " + name);
            // info: camino feliz, útil para trazabilidad en producción.
            logger.info("Usuario '{}' creado exitosamente", name);
        } catch (Exception e) {
            // error: algo interno falló de forma inesperada; se registra
            // la excepción completa (", e" al final) para tener stack trace.
            logger.error("Fallo al crear usuario '{}': {}", name, e.getMessage(), e);
            throw new BusinessRuleException("No fue posible completar la creación del usuario");
        }
    }

    /**
     * Genera un reporte. A diferencia del código original de Copilot,
     * ReportGenerator SÍ se usa aquí — ya no queda como código muerto.
     */
    public String generateReport() {
        logger.info("Generando reporte de usuarios");
        return reportGenerator.generate();
    }
}