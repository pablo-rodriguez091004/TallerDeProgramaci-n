package com.reservas.estructuras;

/**
 * A generic singly linked list implemented from scratch, without relying on
 * {@code java.util.*}. Maintains both head and tail pointers so that
 * insertion at either end is O(1).
 *
 * @param <T> the type of elements stored in this list
 */
public class LinkedList<T> {

    /**
     * Internal node holding a value and a reference to the next node.
     */
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
     * Creates an empty linked list.
     * @complexity O(1)
     */
    public LinkedList() {
        this.head = null;
        this.tail = null;
        this.size = 0;
    }

    /**
     * Inserts a new element at the beginning of the list.
     *
     * @param value the element to insert
     * @complexity O(1)
     */
    public void addFirst(T value) {
        Node<T> node = new Node<>(value);
        if (isEmpty()) {
            head = node;
            tail = node;
        } else {
            node.next = head;
            head = node;
        }
        size++;
    }

    /**
     * Appends a new element at the end of the list.
     *
     * @param value the element to insert
     * @complexity O(1) because a tail pointer is maintained
     */
    public void addLast(T value) {
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
     * Removes and returns the first element of the list.
     *
     * @return the former first element
     * @throws EmptyStructureException if the list is empty
     * @complexity O(1)
     */
    public T removeFirst() {
        if (isEmpty()) {
            throw new EmptyStructureException("Cannot removeFirst() from an empty LinkedList");
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
     * Removes and returns the last element of the list.
     *
     * @return the former last element
     * @throws EmptyStructureException if the list is empty
     * @complexity O(n) because the singly linked structure requires a full
     *             traversal to reach the node before the tail
     */
    public T removeLast() {
        if (isEmpty()) {
            throw new EmptyStructureException("Cannot removeLast() from an empty LinkedList");
        }
        T value = tail.data;
        if (head == tail) {
            head = null;
            tail = null;
        } else {
            Node<T> current = head;
            while (current.next != tail) {
                current = current.next;
            }
            current.next = null;
            tail = current;
        }
        size--;
        return value;
    }

    /**
     * Removes the first occurrence of the given value.
     *
     * @param value the value to remove
     * @return true if an element was removed, false if not found
     * @complexity O(n)
     */
    public boolean remove(T value) {
        if (isEmpty()) {
            return false;
        }
        if (equalsValue(head.data, value)) {
            removeFirst();
            return true;
        }
        Node<T> current = head;
        while (current.next != null && !equalsValue(current.next.data, value)) {
            current = current.next;
        }
        if (current.next == null) {
            return false;
        }
        if (current.next == tail) {
            tail = current;
        }
        current.next = current.next.next;
        size--;
        return true;
    }

    /**
     * Returns the element located at the given index.
     *
     * @param index zero-based position
     * @return the element at that position
     * @throws IndexOutOfBoundsException if the index is out of range
     * @complexity O(n)
     */
    public T get(int index) {
        if (index < 0 || index >= size) {
            throw new IndexOutOfBoundsException("Index: " + index + ", Size: " + size);
        }
        Node<T> current = head;
        for (int i = 0; i < index; i++) {
            current = current.next;
        }
        return current.data;
    }

    /**
     * Checks whether the given value exists in the list.
     *
     * @param value the value to search for
     * @return true if found, false otherwise
     * @complexity O(n)
     */
    public boolean contains(T value) {
        Node<T> current = head;
        while (current != null) {
            if (equalsValue(current.data, value)) {
                return true;
            }
            current = current.next;
        }
        return false;
    }

    /**
     * Returns the first element without removing it.
     *
     * @return the first element
     * @throws EmptyStructureException if the list is empty
     * @complexity O(1)
     */
    public T peekFirst() {
        if (isEmpty()) {
            throw new EmptyStructureException("Cannot peekFirst() from an empty LinkedList");
        }
        return head.data;
    }

    /**
     * Returns the number of elements currently stored.
     * @complexity O(1)
     */
    public int size() {
        return size;
    }

    /**
     * Returns true if the list has no elements.
     * @complexity O(1)
     */
    public boolean isEmpty() {
        return size == 0;
    }

    /**
     * Removes every element from the list.
     * @complexity O(1)
     */
    public void clear() {
        head = null;
        tail = null;
        size = 0;
    }

    /**
     * Copies the contents of the list into a new array, preserving order.
     *
     * <p>Returns {@code Object[]} rather than an unsafe {@code (T[])}-cast
     * array: since arrays carry runtime type information but generics do
     * not, casting a freshly-allocated {@code Object[]} to {@code T[]}
     * would throw {@code ClassCastException} as soon as the caller assigns
     * it to a more specific array type. Returning {@code Object[]} is the
     * safe, well-known pattern for a hand-rolled generic container.</p>
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

    private boolean equalsValue(T a, T b) {
        return a == null ? b == null : a.equals(b);
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder("[");
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
