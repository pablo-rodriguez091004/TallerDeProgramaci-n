package com.reservas;

import com.reservas.estructuras.BST;
import com.reservas.estructuras.LinkedList;
import com.reservas.estructuras.Queue;
import com.reservas.estructuras.Stack;
import com.reservas.integration.DailyBookingSchedule;
import com.reservas.integration.Reservation;
import com.reservas.integration.ReservationActionHistory;
import com.reservas.integration.ReservationDateIndex;
import com.reservas.integration.ReservationWaitlistService;

import java.time.LocalDateTime;

/**
 * Demo entry point showing the four custom data structures working both
 * on their own and integrated into real use cases of the space reservation
 * project. Run with:
 * <pre>{@code mvn compile exec:java}</pre>
 */
public final class Main {

    public static void main(String[] args) {
        demoBareStructures();
        System.out.println();
        demoIntegration();
    }

    private static void demoBareStructures() {
        System.out.println("== Demo estructuras propias ==");

        LinkedList<String> list = new LinkedList<>();
        list.addLast("A");
        list.addLast("B");
        list.addFirst("Z");
        System.out.println("LinkedList: " + list + " (size=" + list.size() + ")");

        Stack<Integer> stack = new Stack<>();
        stack.push(1);
        stack.push(2);
        stack.push(3);
        System.out.println("Stack: " + stack + " -> pop()=" + stack.pop());

        Queue<String> queue = new Queue<>();
        queue.enqueue("cliente1");
        queue.enqueue("cliente2");
        System.out.println("Queue: " + queue + " -> dequeue()=" + queue.dequeue());

        BST<Integer> bst = new BST<>();
        int[] values = {50, 30, 70, 20, 40, 60, 80};
        for (int v : values) {
            bst.insert(v);
        }
        System.out.println("BST inOrder: " + bst.inOrder() + " (height=" + bst.height() + ")");
    }

    private static void demoIntegration() {
        System.out.println("== Demo integracion con el dominio de reservas ==");

        // Queue -> lista de espera
        ReservationWaitlistService waitlist = new ReservationWaitlistService("Cancha 1");
        waitlist.joinWaitlist(new Reservation("R1", "Cancha 1", "Ana", LocalDateTime.now().plusHours(1)));
        waitlist.joinWaitlist(new Reservation("R2", "Cancha 1", "Luis", LocalDateTime.now().plusHours(2)));
        System.out.println("Lista de espera (" + waitlist.getResourceName() + "): " + waitlist.waitlistSize() + " clientes");
        System.out.println("Se libera un cupo, se ofrece a: " + waitlist.offerFreedSlot());

        // Stack -> historial de acciones (undo)
        ReservationActionHistory history = new ReservationActionHistory();
        history.record("CREATE", "R1", "Reserva creada por Ana");
        history.record("RESCHEDULE", "R1", "Reserva movida a las 5pm");
        System.out.println("Ultima accion registrada: " + history.peekLast());
        System.out.println("Deshaciendo -> " + history.undoLast());

        // LinkedList -> agenda diaria ordenada
        DailyBookingSchedule schedule = new DailyBookingSchedule("Cancha 1");
        schedule.addBooking(new Reservation("R1", "Cancha 1", "Ana", LocalDateTime.now().plusHours(1)));
        schedule.addBooking(new Reservation("R3", "Cancha 1", "Marta", LocalDateTime.now().plusHours(3)));
        System.out.println(schedule);
        System.out.println("Cancha 1 tiene la reserva R3? " + schedule.isBooked("R3"));

        // BST -> indice por fecha
        ReservationDateIndex dateIndex = new ReservationDateIndex();
        dateIndex.index(new Reservation("R1", "Cancha 1", "Ana", LocalDateTime.now().plusHours(1)));
        dateIndex.index(new Reservation("R2", "Cancha 1", "Luis", LocalDateTime.now().plusHours(2)));
        dateIndex.index(new Reservation("R3", "Cancha 1", "Marta", LocalDateTime.now().plusHours(3)));
        System.out.println("Proxima reserva: " + dateIndex.earliest());
        System.out.println("Reporte cronologico: " + dateIndex.chronologicalReport());
    }
}
