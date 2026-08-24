package com.reservas.integration;

import com.reservas.estructuras.BST;
import com.reservas.estructuras.LinkedList;

/**
 * Real use case for the custom {@link BST}: an index of all reservations
 * of a resource ordered by date/time, used to quickly check availability,
 * find the next upcoming reservation, or list every reservation in
 * chronological order for a report -- operations that benefit from the
 * BST's ordered O(log n) average search instead of a linear scan.
 */
public class ReservationDateIndex {

    private final BST<Reservation> index = new BST<>();

    /**
     * Indexes a reservation by its date/time.
     */
    public void index(Reservation reservation) {
        index.insert(reservation);
    }

    /**
     * Checks whether a reservation exists at exactly this date/time.
     */
    public boolean existsAt(Reservation probe) {
        return index.search(probe);
    }

    /**
     * Removes a reservation from the index (e.g. on cancellation).
     */
    public boolean remove(Reservation reservation) {
        return index.delete(reservation);
    }

    /**
     * Returns the earliest upcoming reservation.
     */
    public Reservation earliest() {
        return index.findMin();
    }

    /**
     * Returns the latest reservation currently indexed.
     */
    public Reservation latest() {
        return index.findMax();
    }

    /**
     * Returns every indexed reservation ordered chronologically, ideal for
     * generating an availability report.
     */
    public LinkedList<Reservation> chronologicalReport() {
        return index.inOrder();
    }

    public int totalIndexed() {
        return index.size();
    }

    public boolean isEmpty() {
        return index.isEmpty();
    }
}
