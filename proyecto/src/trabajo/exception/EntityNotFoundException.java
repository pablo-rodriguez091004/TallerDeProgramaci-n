package trabajo.exception;

/**
 * ============================================================================
 * PUNTO 3 — Jerarquía de excepciones: NIVEL 3 (hoja) — 1 de 3
 * ============================================================================
 * Se lanza cuando se busca una entidad por su id y esta no existe.
 * Ejemplo de uso: UserService.getUser(id) cuando el id no está en el
 * repositorio.
 * ============================================================================
 */
public class EntityNotFoundException extends DomainException {

    /**
     * @param entityName nombre legible de la entidad (ej. "User", "Report")
     * @param id         identificador que se buscó y no se encontró
     */
    public EntityNotFoundException(String entityName, Object id) {
        super(String.format("%s con id %s no fue encontrado", entityName, id),
              "ENTITY_NOT_FOUND");
    }
}
