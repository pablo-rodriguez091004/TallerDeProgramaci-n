package trabajo.repository;

import trabajo.model.Report;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * ============================================================================
 * PUNTO 5 — Implementación concreta #2 de Repository<T, ID>
 * ============================================================================
 * Misma idea que InMemoryUserRepository pero para Report. Demuestra que la
 * interfaz genérica Repository<T, ID> sirve para CUALQUIER entidad, no solo
 * para User — esa es la fuerza real de haberla hecho genérica en vez de
 * escribir una interfaz específica por cada tipo.
 * ============================================================================
 */
public class InMemoryReportRepository implements Repository<Report, Long> {

    private final Map<Long, Report> storage = new HashMap<>();
    private long nextId = 1;

    @Override
    public Report save(Report entity) {
        if (entity.getId() == null) {
            entity.setId(nextId++);
        }
        storage.put(entity.getId(), entity);
        return entity;
    }

    @Override
    public Optional<Report> findById(Long id) {
        return Optional.ofNullable(storage.get(id));
    }

    @Override
    public List<Report> findAll() {
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
