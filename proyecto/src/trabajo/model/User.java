package trabajo.model;

/**
 * Modelo de dominio mínimo. Se usa en trabajo.repository y trabajo.service
 * para el punto 5 (DIP con Repository<T, ID> genérico).
 */
public class User {

    private Long id;
    private final String name;
    private final String email;

    public User(String name, String email) {
        this.name = name;
        this.email = email;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public String getEmail() { return email; }
}
