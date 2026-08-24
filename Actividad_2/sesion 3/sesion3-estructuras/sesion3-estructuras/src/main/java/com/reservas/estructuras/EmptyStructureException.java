package com.reservas.estructuras;

/**
 * Thrown when an operation that requires at least one element
 * (e.g. removeFirst, pop, dequeue, findMin) is invoked on an
 * empty data structure.
 *
 * <p>This is an unchecked exception because attempting to read from
 * an empty structure is considered a programming error that should
 * be prevented with an {@code isEmpty()} check, not a recoverable
 * condition that every caller must declare.</p>
 */
public class EmptyStructureException extends RuntimeException {

    public EmptyStructureException(String message) {
        super(message);
    }
}
