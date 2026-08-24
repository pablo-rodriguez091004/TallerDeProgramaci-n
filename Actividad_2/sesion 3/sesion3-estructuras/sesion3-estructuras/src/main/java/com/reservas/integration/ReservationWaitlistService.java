package com.reservas.integration;

import com.reservas.estructuras.EmptyStructureException;
import com.reservas.estructuras.Queue;

/**
 * Real use case for the custom {@link Queue}: when a space (a sports court,
 * a coworking desk, an event venue) is fully booked, new reservation
 * requests are placed on a FIFO waitlist. As soon as a slot frees up, the
 * client who has been waiting the longest is offered it first.
 */
public class ReservationWaitlistService {

    private final String resourceName;
    private final Queue<Reservation> waitlist = new Queue<>();

    public ReservationWaitlistService(String resourceName) {
        this.resourceName = resourceName;
    }

    /**
     * Adds a reservation request to the back of the waitlist.
     */
    public void joinWaitlist(Reservation reservation) {
        waitlist.enqueue(reservation);
    }

    /**
     * Offers the freed slot to the client that has waited the longest.
     *
     * @return the reservation that should now be confirmed
     * @throws EmptyStructureException if nobody is waiting
     */
    public Reservation offerFreedSlot() {
        return waitlist.dequeue();
    }

    public boolean hasWaitingClients() {
        return !waitlist.isEmpty();
    }

    public int waitlistSize() {
        return waitlist.size();
    }

    public String getResourceName() {
        return resourceName;
    }
}
