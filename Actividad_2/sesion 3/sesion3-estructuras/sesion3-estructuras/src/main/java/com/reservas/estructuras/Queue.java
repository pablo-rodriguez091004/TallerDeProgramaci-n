package com.reservas.estructuras;

/**
 * A generic FIFO (first-in, first-out) queue implemented from scratch using
 * a singly linked internal structure with head and tail pointers, without
 * relying on {@code java.util.*}.
 *
 * @param <T> the type of elements stored in this queue
 */
public class Queue<T> {

    private static class Node<T> {
        private T data;
        private Node<T> next;

        private Node(T data) {
            this.data = data;
        }
    }

    private Node<T> head;
    private Node<T> tail;
    private int size;

    /**
     * Creates an empty queue.
     * @complexity O(1)
     */
    public Queue() {
        this.head = null;
        this.tail = null;
        this.size = 0;
    }

    /**
     * Adds a new element at the back of the queue.
     *
     * @param value the element to enqueue
     * @complexity O(1)
     */
    public void enqueue(T value) {
        Node<T> node = new Node<>(value);
        if (isEmpty()) {
            head = node;
            tail = node;
        } else {
            tail.next = node;
            tail = node;
        }
        size++;
    }

    /**
     * Removes and returns the element at the front of the queue.
     *
     * @return the former front element
     * @throws EmptyStructureException if the queue is empty
     * @complexity O(1)
     */
    public T dequeue() {
        if (isEmpty()) {
            throw new EmptyStructureException("Cannot dequeue() from an empty Queue");
        }
        T value = head.data;
        head = head.next;
        size--;
        if (head == null) {
            tail = null;
        }
        return value;
    }

    /**
     * Returns the front element without removing it.
     *
     * @return the front element
     * @throws EmptyStructureException if the queue is empty
     * @complexity O(1)
     */
    public T peek() {
        if (isEmpty()) {
            throw new EmptyStructureException("Cannot peek() an empty Queue");
        }
        return head.data;
    }

    /**
     * Checks whether the given value is present anywhere in the queue.
     *
     * @param value the value to search for
     * @return true if found, false otherwise
     * @complexity O(n)
     */
    public boolean contains(T value) {
        Node<T> current = head;
        while (current != null) {
            if (current.data == null ? value == null : current.data.equals(value)) {
                return true;
            }
            current = current.next;
        }
        return false;
    }

    /**
     * Returns the number of elements currently stored.
     * @complexity O(1)
     */
    public int size() {
        return size;
    }

    /**
     * Returns true if the queue has no elements.
     * @complexity O(1)
     */
    public boolean isEmpty() {
        return size == 0;
    }

    /**
     * Removes every element from the queue.
     * @complexity O(1)
     */
    public void clear() {
        head = null;
        tail = null;
        size = 0;
    }

    /**
     * Copies the contents of the queue into a new array, ordered from
     * front to back.
     *
     * <p>Returns {@code Object[]} rather than an unsafe {@code (T[])}-cast
     * array, which would throw {@code ClassCastException} the moment the
     * caller assigned it to a more specific array type.</p>
     *
     * @return an array snapshot of the current elements
     * @complexity O(n)
     */
    public Object[] toArray() {
        Object[] array = new Object[size];
        Node<T> current = head;
        int i = 0;
        while (current != null) {
            array[i++] = current.data;
            current = current.next;
        }
        return array;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder("[front -> ");
        Node<T> current = head;
        while (current != null) {
            sb.append(current.data);
            if (current.next != null) {
                sb.append(", ");
            }
            current = current.next;
        }
        return sb.append("]").toString();
    }
}
