package com.reservas.integration;

import com.reservas.estructuras.LinkedList;

/**
 * Real use case for the custom {@link LinkedList}: the ordered agenda of
 * reservations for a single resource (e.g. "Cancha 1") on a given day.
 * Reservations are appended as they are confirmed, can be looked up,
 * cancelled, and listed in the order they were booked -- exactly the
 * access pattern a simple ordered list is built for.
 */
public class DailyBookingSchedule {

    private final String resourceName;
    private final LinkedList<Reservation> bookings = new LinkedList<>();

    public DailyBookingSchedule(String resourceName) {
        this.resourceName = resourceName;
    }

    /**
     * Confirms a new booking, appending it at the end of the day's agenda.
     */
    public void addBooking(Reservation reservation) {
        bookings.addLast(reservation);
    }

    /**
     * Cancels a booking by matching reservation id.
     *
     * @return true if a booking was found and removed
     */
    public boolean cancelBooking(String reservationId) {
        for (int i = 0; i < bookings.size(); i++) {
            Reservation r = bookings.get(i);
            if (r.getId().equals(reservationId)) {
                return bookings.remove(r);
            }
        }
        return false;
    }

    /**
     * Checks whether the resource already has a booking with this id.
     */
    public boolean isBooked(String reservationId) {
        for (int i = 0; i < bookings.size(); i++) {
            if (bookings.get(i).getId().equals(reservationId)) {
                return true;
            }
        }
        return false;
    }

    public int totalBookings() {
        return bookings.size();
    }

    public String getResourceName() {
        return resourceName;
    }

    @Override
    public String toString() {
        return "Agenda(" + resourceName + ") " + bookings;
    }
}
