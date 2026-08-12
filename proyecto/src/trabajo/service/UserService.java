package trabajo.service;

import trabajo.exception.EntityNotFoundException;
import trabajo.exception.ValidationException;
import trabajo.model.User;
import trabajo.repository.Repository;
import trabajo.validation.DomainValidator;

/**
 * ============================================================================
 * PUNTO 5 — Servicio de dominio #1, con Repository inyectado por CONSTRUCTOR
 * ============================================================================
 * Nótese la diferencia clave con trabajo.UserManager: esta clase NUNCA hace
 * "new InMemoryUserRepository()". Recibe la abstracción Repository<User,
 * Long> ya construida desde afuera (inyección de dependencias manual).
 *
 * Esto es DIP aplicado de verdad:
 *   - UserService (módulo de alto nivel) depende de Repository (abstracción)
 *   - InMemoryUserRepository (módulo de bajo nivel) también depende de esa
 *     misma abstracción, implementándola
 *   - Ninguno de los dos depende directamente del otro
 * ============================================================================
 */
public class UserService {

    private final Repository<User, Long> userRepository;
    private final DomainValidator<String> emailValidator;

    /**
     * Inyección por constructor: quien construya UserService decide qué
     * implementación de Repository y de DomainValidator usar (real, mock,
     * en memoria, con base de datos, etc.).
     */
    public UserService(Repository<User, Long> userRepository,
                        DomainValidator<String> emailValidator) {
        this.userRepository = userRepository;
        this.emailValidator = emailValidator;
    }

    public User createUser(String name, String email) {
        if (!emailValidator.validate(email)) {
            throw new ValidationException("Email inválido: " + email);
        }
        return userRepository.save(new User(name, email));
    }

    public User getUser(Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("User", id));
    }
}
