
package trabajo;

import trabajo.exception.AppException;
import trabajo.exception.EntityNotFoundException;
import trabajo.exception.ValidationException;
import trabajo.model.User;
import trabajo.repository.InMemoryUserRepository;
import trabajo.repository.Repository;
import trabajo.service.UserService;
import trabajo.validation.DomainValidator;

public class Main {

    public static void main(String[] args) {

        System.out.println("=== DEMO: UserManager (puntos 2 y 3) ===");
        UserManager userManager = new UserManager(
                new UserRepository(),
                new EmailService(),
                new EmailValidator(),
                new ActivityLogger(),
                new ReportGenerator()
        );

        userManager.createUser("Ana", "ana@test.com");

        try {
            userManager.createUser("Luis", "correo-sin-arroba");
        } catch (ValidationException e) {
            System.out.println("Excepción capturada -> " + e.getErrorCode() + ": " + e.getMessage());
        }

        System.out.println();
        System.out.println("=== DEMO: UserService con DIP (punto 5) ===");

        Repository<User, Long> repository = new InMemoryUserRepository();
        DomainValidator<String> validator = new EmailValidator()::isValid;
        UserService userService = new UserService(repository, validator);

        User creado = userService.createUser("Marta", "marta@test.co");
        System.out.println("Usuario creado con id: " + creado.getId());

        try {
            userService.getUser(999L);
        } catch (AppException e) {
            System.out.println("Excepción capturada -> " + e.getErrorCode() + ": " + e.getMessage());
        }
    }
}