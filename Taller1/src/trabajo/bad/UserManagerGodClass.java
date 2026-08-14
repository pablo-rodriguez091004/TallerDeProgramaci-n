package trabajo.bad;

/**
 * ============================================================================
 * PUNTO 1 — Código original a analizar (Bad Smell: God Class)
 * ============================================================================
 *
 * Este es el fragmento que Copilot podría generar. Se deja INTACTO en su
 * propio paquete "bad" solo como referencia histórica del "antes" — no se usa
 * en ningún otro lugar del proyecto. Las clases reales y correctas están en
 * trabajo.* (ver UserRepository, EmailService, etc.) y en trabajo.exception,
 * trabajo.validation, trabajo.repository, trabajo.service.
 *
 * ----------------------------------------------------------------------------
 * ANÁLISIS: ¿cuántos y cuáles principios SOLID viola?
 * ----------------------------------------------------------------------------
 *
 * 1) SINGLE RESPONSIBILITY PRINCIPLE (SRP) — VIOLADO, de forma directa.
 *    La clase tiene 5 razones distintas para cambiar: persistencia
 *    (createUser), notificación (sendEmail), reportería (generateReport),
 *    validación (validateEmail) y auditoría (logActivity). Cada una
 *    pertenece a un dominio distinto y debería vivir en su propia clase.
 *
 * 2) OPEN/CLOSED PRINCIPLE (OCP) — VIOLADO, de forma directa.
 *    Para agregar un nuevo tipo de reporte, un nuevo canal de notificación
 *    o una nueva regla de validación, hay que MODIFICAR UserManager
 *    directamente en lugar de extenderla mediante nuevas implementaciones.
 *    No existen abstracciones (interfaces) que permitan añadir
 *    comportamiento sin tocar el código existente.
 *
 * 3) DEPENDENCY INVERSION PRINCIPLE (DIP) — VIOLACIÓN CONDICIONAL.
 *    El fragmento original no muestra campos ni implementación interna,
 *    así que no podemos afirmarlo con certeza a partir del código dado.
 *    PERO: si los métodos (createUser, sendEmail, etc.) dependen de
 *    implementaciones concretas (un DAO específico, un cliente SMTP
 *    específico) en lugar de interfaces/abstracciones, la clase queda
 *    acoplada a detalles de bajo nivel, dificultando pruebas unitarias y
 *    el cambio de proveedor. En la práctica, en el punto 2 confirmamos que
 *    SÍ ocurre (ver UserManager.java, que hace "new UserRepository()").
 *
 * 4) INTERFACE SEGREGATION PRINCIPLE (ISP) — VIOLACIÓN CONDICIONAL.
 *    Si en algún momento se extrae una interfaz IUserManager que agrupe
 *    los 5 métodos, cualquier cliente que solo necesite, por ejemplo,
 *    validateEmail(), se vería forzado a depender también de
 *    generateReport() y sendEmail(), que no usa. Con el fragmento tal cual
 *    (sin interfaz explícita) esto es un riesgo latente, no un hecho.
 *
 * 5) LISKOV SUBSTITUTION PRINCIPLE (LSP) — NO APLICA.
 *    No hay herencia ni polimorfismo involucrado en este fragmento, por lo
 *    que LSP no se ve comprometido directamente.
 *
 * CONCLUSIÓN: 2 violaciones confirmadas por el código (SRP, OCP),
 * 2 violaciones condicionales/potenciales (DIP, ISP) y 1 principio que no
 * aplica (LSP).
 * ============================================================================
 */
public class UserManagerGodClass {

    // Persistencia
    public void createUser() {
        // acceso a base de datos
    }

    // Notificación
    public void sendEmail() {
        // envío de correo
    }

    // Reportería
    public void generateReport() {
        // generación de reportes
    }

    // Validación
    public void validateEmail() {
        // validación de formato de email
    }

    // Auditoría
    public void logActivity() {
        // registro de actividad
    }
}
