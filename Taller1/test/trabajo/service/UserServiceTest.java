package trabajo.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import trabajo.exception.AppException;
import trabajo.exception.BusinessRuleException;
import trabajo.exception.DomainException;
import trabajo.exception.EntityNotFoundException;
import trabajo.exception.ValidationException;
import trabajo.model.User;
import trabajo.repository.Repository;
import trabajo.validation.DomainValidator;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * ============================================================================
 * PUNTO 6 — Pruebas unitarias (JUnit 5 + AssertJ + Mockito)
 * ============================================================================
 * Gracias a que UserService depende de Repository<User, Long> y de
 * DomainValidator<String> (abstracciones, punto 5), podemos MOCKEARLOS
 * aquí sin tocar una base de datos real ni lógica de validación real.
 * Esa es la recompensa práctica de haber aplicado DIP correctamente.
 * ============================================================================
 */
class UserServiceTest {

    private Repository<User, Long> repository;
    private DomainValidator<String> validator;
    private UserService userService;

    @BeforeEach
    void setUp() {
        repository = mock(Repository.class);
        validator = mock(DomainValidator.class);
        userService = new UserService(repository, validator);
    }

    @Test
    void deberiaLanzarValidationExceptionSiElEmailEsInvalido() {
        when(validator.validate("correo-malo")).thenReturn(false);

        assertThatThrownBy(() -> userService.createUser("Ana", "correo-malo"))
                .isInstanceOf(ValidationException.class)
                .hasMessageContaining("Email inválido");
    }

    @Test
    void deberiaLanzarEntityNotFoundExceptionSiElUsuarioNoExiste() {
        when(repository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> userService.getUser(99L))
                .isInstanceOf(EntityNotFoundException.class)
                .hasMessageContaining("User")
                .hasMessageContaining("99");
    }

    @Test
    void deberiaCrearUsuarioCuandoElEmailEsValido() {
        when(validator.validate("ana@test.com")).thenReturn(true);
        when(repository.save(any(User.class))).thenAnswer(inv -> inv.getArgument(0));

        User creado = userService.createUser("Ana", "ana@test.com");

        assertThat(creado.getName()).isEqualTo("Ana");
        verify(repository, times(1)).save(any(User.class));
    }

    @Test
    void laJerarquiaDeExcepcionesDeberiaRespetarLaHerenciaDefinida() {
        EntityNotFoundException ex = new EntityNotFoundException("User", 1L);

        assertThat(ex)
                .isInstanceOf(DomainException.class)
                .isInstanceOf(AppException.class)
                .isInstanceOf(RuntimeException.class);
    }

    @Test
    void cadaExcepcionDeberiaExponerSuPropioErrorCode() {
        ValidationException validationEx = new ValidationException("dato inválido");
        BusinessRuleException businessEx = new BusinessRuleException("stock insuficiente");

        assertThat(validationEx.getErrorCode()).isEqualTo("VALIDATION_ERROR");
        assertThat(businessEx.getErrorCode()).isEqualTo("BUSINESS_RULE_VIOLATION");
    }

    @Test
    void elMensajeDeEntityNotFoundDeberiaIncluirEntidadEId() {
        EntityNotFoundException ex = new EntityNotFoundException("Report", 42L);

        assertThat(ex.getMessage())
                .contains("Report")
                .contains("42");
    }
}
