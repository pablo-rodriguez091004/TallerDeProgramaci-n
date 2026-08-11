package trabajo;

import trabajo.model.User;

/**
 * ============================================================================
 * PUNTO 2 — Refactor SRP: Clase 1 de 5 — Persistencia
 * ============================================================================
 * Responsabilidad ÚNICA: guardar y recuperar usuarios de la base de datos.
 * No sabe nada de validación, email, reportes ni logging — si mañana
 * cambiamos de MySQL a PostgreSQL, solo esta clase se toca.
 *
 * NOTA DE DISEÑO: en su forma actual, UserManager sigue creando esta clase
 * con "new UserRepository()" (ver UserManager.java), lo cual todavía viola
 * DIP. El punto 5 (trabajo.repository.Repository<T,ID>) resuelve ese
 * problema de raíz para los servicios nuevos (UserService, ReportService).
 * Esta clase se deja tal cual para no romper la continuidad con tu punto 2
 * original; en un refactor completo, UserManager terminaría delegando en
 * UserService en vez de en esta clase directamente.
 * ============================================================================
 */
public class UserRepository {

    /**
     * Persiste un nuevo usuario.
     * @param name  nombre del usuario
     * @param email correo del usuario (ya validado por quien llama)
     */
    public void createUser(String name, String email) {
        // acceso a base de datos
    }
}
