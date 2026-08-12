package trabajo.model;

/**
 * Segundo modelo de dominio, usado por ReportService para demostrar que
 * Repository<T, ID> se puede inyectar en MÁS DE UN servicio (punto 5 exige
 * "al menos 2 servicios del dominio").
 */
public class Report {

    private Long id;
    private final String content;

    public Report(String content) {
        this.content = content;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getContent() { return content; }
}
