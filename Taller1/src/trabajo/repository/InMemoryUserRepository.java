package trabajo.repository;

import trabajo.model.User;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * ============================================================================
 * PUNTO 5 — Implementación concreta #1 de Repository<T, ID>
 * ============================================================================
 * Implementación en memoria (útil para pruebas y para desarrollar sin
 * depender aún de MySQL/JPA). El punto clave es que UserService NUNCA
 * referencia esta clase directamente — solo conoce la interfaz Repository.
 * Mañana puedes escribir "JdbcUserRepository implements Repository<User,
 * Long>" y sustituirla sin tocar ni una línea de UserService.
 * ============================================================================
 */
public class InMemoryUserRepository implements Repository<User, Long> {

    private final Map<Long, User> storage = new HashMap<>();
    private long nextId = 1;

    @Override
    public User save(User entity) {
        if (entity.getId() == null) {
            entity.setId(nextId++);
        }
        storage.put(entity.getId(), entity);
        return entity;
    }

    @Override
    public Optional<User> findById(Long id) {
        return Optional.ofNullable(storage.get(id));
    }

    @Override
    public List<User> findAll() {
        return new ArrayList<>(storage.values());
    }

    @Override
    public void deleteById(Long id) {
        storage.remove(id);
    }

    @Override
    public boolean existsById(Long id) {
        return storage.containsKey(id);
    }
}
