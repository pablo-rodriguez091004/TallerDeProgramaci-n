package com.reservas.integration;

import com.reservas.estructuras.EmptyStructureException;
import com.reservas.estructuras.Stack;

/**
 * Real use case for the custom {@link Stack}: employees and admins can undo
 * their last actions (create, cancel, reschedule) on reservations. Every
 * action is pushed onto a history stack; undo pops the most recent one,
 * which is exactly the LIFO behaviour an "undo" feature needs.
 */
public class ReservationActionHistory {

    /**
     * A single recorded action, kept immutable and simple on purpose since
     * this class only demonstrates the Stack integration.
     */
    public record Action(String type, String reservationId, String description) {
    }

    private final Stack<Action> history = new Stack<>();

    /**
     * Records a new action performed on a reservation.
     */
    public void record(String type, String reservationId, String description) {
        history.push(new Action(type, reservationId, description));
    }

    /**
     * Undoes (pops) the most recent action.
     *
     * @return the action that was undone
     * @throws EmptyStructureException if there is nothing to undo
     */
    public Action undoLast() {
        return history.pop();
    }

    /**
     * Looks at the most recent action without removing it.
     */
    public Action peekLast() {
        return history.peek();
    }

    public boolean canUndo() {
        return !history.isEmpty();
    }

    public int historySize() {
        return history.size();
    }
}
