def apply_changes(entity, changes, allowed_fields):
    """Copia a la entidad solo los campos editables presentes en `changes`."""
    for field in allowed_fields:
        if field in changes:
            setattr(entity, field, changes[field])
