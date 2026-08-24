package com.reservas.estructuras;

/**
 * A generic LIFO (last-in, first-out) stack implemented from scratch using
 * a singly linked internal structure, without relying on {@code java.util.*}.
 *
 * @param <T> the type of elements stored in this stack
 */
public class Stack<T> {

    private static class Node<T> {
        private T data;
        private Node<T> next;

        private Node(T data) {
            this.data = data;
        }
    }

    private Node<T> top;
    private int size;

    /**
     * Creates an empty stack.
     * @complexity O(1)
     */
    public Stack() {
        this.top = null;
        this.size = 0;
    }

    /**
     * Pushes a new element on top of the stack.
     *
     * @param value the element to push
     * @complexity O(1)
     */
    public void push(T value) {
        Node<T> node = new Node<>(value);
        node.next = top;
        top = node;
        size++;
    }

    /**
     * Removes and returns the element on top of the stack.
     *
     * @return the former top element
     * @throws EmptyStructureException if the stack is empty
     * @complexity O(1)
     */
    public T pop() {
        if (isEmpty()) {
            throw new EmptyStructureException("Cannot pop() from an empty Stack");
        }
        T value = top.data;
        top = top.next;
        size--;
        return value;
    }

    /**
     * Returns the top element without removing it.
     *
     * @return the top element
     * @throws EmptyStructureException if the stack is empty
     * @complexity O(1)
     */
    public T peek() {
        if (isEmpty()) {
            throw new EmptyStructureException("Cannot peek() an empty Stack");
        }
        return top.data;
    }

    /**
     * Checks whether the given value is present anywhere in the stack.
     *
     * @param value the value to search for
     * @return true if found, false otherwise
     * @complexity O(n)
     */
    public boolean contains(T value) {
        Node<T> current = top;
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
     * Returns true if the stack has no elements.
     * @complexity O(1)
     */
    public boolean isEmpty() {
        return size == 0;
    }

    /**
     * Removes every element from the stack.
     * @complexity O(1)
     */
    public void clear() {
        top = null;
        size = 0;
    }

    /**
     * Copies the contents of the stack into a new array, ordered from
     * top to bottom.
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
        Node<T> current = top;
        int i = 0;
        while (current != null) {
            array[i++] = current.data;
            current = current.next;
        }
        return array;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder("[top -> ");
        Node<T> current = top;
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
