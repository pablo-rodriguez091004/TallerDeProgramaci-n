package trabajo;

import java.util.Scanner;
import trabajo.exception.ValidationException;

/**
 * ============================================================================
 * PUNTO DE ENTRADA EJECUTABLE — con menú interactivo
 * ============================================================================
 * Dos formas de usar el programa:
 *   1) Demo automática: prueba 2 usuarios con datos correctos y 2 con datos
 *      incorrectos, mostrando en consola la razón EXACTA de cada fallo.
 *   2) Agregar usuario manual: el usuario escribe nombre y email desde el
 *      teclado, y el programa aplica exactamente el mismo flujo de
 *      validación y manejo de excepciones que la demo automática.
 * ============================================================================
 */
public class Main {

    public static void main(String[] args) {

        UserManager userManager = new UserManager(
                new UserRepository(),
                new EmailService(),
                new EmailValidator(),
                new ActivityLogger(),
                new ReportGenerator()
        );

        Scanner scanner = new Scanner(System.in);
        boolean salir = false;

        while (!salir) {
            mostrarMenu();
            String opcion = scanner.nextLine().trim();

            switch (opcion) {
                case "1":
                    ejecutarDemoAutomatica(userManager);
                    break;
                case "2":
                    agregarUsuarioManual(userManager, scanner);
                    break;
                case "3":
                    salir = true;
                    System.out.println("Saliendo del programa...");
                    break;
                default:
                    System.out.println("Opción no válida, intenta de nuevo.\n");
            }
        }

        scanner.close();
    }

    private static void mostrarMenu() {
        System.out.println("========================================");
        System.out.println(" MENÚ - Gestión de usuarios");
        System.out.println("========================================");
        System.out.println("1. Ejecutar demo automática (2 correctos, 2 incorrectos)");
        System.out.println("2. Agregar un usuario manualmente");
        System.out.println("3. Salir");
        System.out.print("Selecciona una opción: ");
    }

    /**
     * Prueba 2 usuarios con datos válidos y 2 con datos inválidos.
     * Cada caso inválido falla por una regla DISTINTA de EmailValidator,
     * para demostrar que el diagnóstico (explainInvalid) identifica
     * correctamente cuál fue el problema en cada caso.
     */
    private static void ejecutarDemoAutomatica(UserManager userManager) {
        System.out.println("\n=== DEMO: 2 usuarios válidos y 2 inválidos ===\n");

        String[][] datosDePrueba = {
                {"Ana", "ana@test.com"},           // válido
                {"Carlos", "carlos@empresa.co"},   // válido
                {"Luis", "correo-sin-arroba"},     // inválido: falta el símbolo @
                {"Maria", "a@b.net"}               // inválido: dominio no permitido (.net)
        };

        for (String[] datos : datosDePrueba) {
            String nombre = datos[0];
            String email = datos[1];
            try {
                userManager.createUser(nombre, email);
                System.out.println("[OK] Usuario '" + nombre + "' creado correctamente con email: " + email);
            } catch (ValidationException e) {
                System.out.println("[ERROR] No se pudo crear a '" + nombre + "' -> " + e.getMessage());
            }
        }
        System.out.println();
    }

    /**
     * Permite ingresar un usuario nuevo desde la consola. Usa exactamente
     * el mismo UserManager.createUser(...) que la demo automática, así que
     * cualquier dato inválido se rechaza con el mismo mensaje explicativo.
     */
    private static void agregarUsuarioManual(UserManager userManager, Scanner scanner) {
        System.out.println("\n=== Agregar nuevo usuario ===");
        System.out.print("Nombre: ");
        String nombre = scanner.nextLine().trim();

        System.out.print("Email: ");
        String email = scanner.nextLine().trim();

        try {
            userManager.createUser(nombre, email);
            System.out.println("[OK] Usuario '" + nombre + "' creado correctamente.\n");
        } catch (ValidationException e) {
            System.out.println("[ERROR] No se pudo crear el usuario -> " + e.getMessage() + "\n");
        }
    }
}