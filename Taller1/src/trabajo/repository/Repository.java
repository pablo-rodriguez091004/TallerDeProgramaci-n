package trabajo.repository;

import java.util.List;
import java.util.Optional;

/**
 * ============================================================================
 * PUNTO 5 — DIP: abstracción genérica de persistencia
 * ============================================================================
 * Esta es LA pieza clave del punto 5. En vez de que cada servicio dependa
 * de una clase concreta como "UserRepository" (acoplamiento a un detalle de
 * implementación), depende de ESTA interfaz.
 *
 * Dependency Inversion Principle dice: los módulos de alto nivel (los
 * servicios) no deben depender de módulos de bajo nivel (el acceso a
 * datos concreto); ambos deben depender de una abstracción. Eso es
 * exactamente esto: tanto UserService como ReportService dependen de
 * Repository<T, ID>, nunca de una implementación específica.
 *
 * Ventaja práctica inmediata: en tests unitarios puedes inyectar un mock
 * de Repository sin tocar base de datos real (ver UserServiceTest).
 *
 * @param <T>  tipo de entidad (User, Report, etc.)
 * @param <ID> tipo del identificador de esa entidad (Long, String, UUID...)
 * ============================================================================
 */
public interface Repository<T, ID> {

    /** Guarda una entidad nueva o actualiza una existente. */
    T save(T entity);

    /** Busca una entidad por su id. Optional evita retornar null. */
    Optional<T> findById(ID id);

    /** Retorna todas las entidades almacenadas. */
    List<T> findAll();

    /** Elimina una entidad por su id. */
    void deleteById(ID id);

    /** Indica si existe una entidad con ese id. */
    boolean existsById(ID id);
}
