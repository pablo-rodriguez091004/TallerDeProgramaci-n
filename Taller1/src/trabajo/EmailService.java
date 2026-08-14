package trabajo;

/**
 * ============================================================================
 * PUNTO 2 — Refactor SRP: Clase 2 de 5 — Notificación
 * ============================================================================
 * Responsabilidad ÚNICA: enviar correos. No sabe nada de la base de datos,
 * de validación ni de reportes. Si mañana cambiamos de proveedor SMTP a un
 * servicio como SendGrid, solo esta clase cambia.
 * ============================================================================
 */
public class EmailService {

    /**
     * Envía un correo de bienvenida al email indicado.
     * @param email destinatario del correo
     */
    public void sendWelcomeEmail(String email) {
        // envío de correo
    }
}
