package com.reservas.integration;

import java.time.LocalDateTime;

/**
 * Simple domain model representing a space reservation, used to
 * demonstrate the data structures from {@code com.reservas.estructuras}
 * in real use cases of the semester project (space reservation and
 * capacity control system).
 *
 * <p>Implements {@link Comparable} by {@code dateTime} so it can be
 * stored directly in the custom {@code BST}.</p>
 */
public class Reservation implements Comparable<Reservation> {

    private final String id;
    private final String resourceName;
    private final String clientName;
    private final LocalDateTime dateTime;

    public Reservation(String id, String resourceName, String clientName, LocalDateTime dateTime) {
        this.id = id;
        this.resourceName = resourceName;
        this.clientName = clientName;
        this.dateTime = dateTime;
    }

    public String getId() {
        return id;
    }

    public String getResourceName() {
        return resourceName;
    }

    public String getClientName() {
        return clientName;
    }

    public LocalDateTime getDateTime() {
        return dateTime;
    }

    @Override
    public int compareTo(Reservation other) {
        return this.dateTime.compareTo(other.dateTime);
    }

    @Override
    public String toString() {
        return String.format("Reservation[%s, %s, client=%s, at=%s]", id, resourceName, clientName, dateTime);
    }
}
