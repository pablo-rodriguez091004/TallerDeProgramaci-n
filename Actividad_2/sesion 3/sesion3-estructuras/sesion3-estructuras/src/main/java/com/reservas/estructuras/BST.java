package com.reservas.estructuras;

/**
 * A generic Binary Search Tree implemented from scratch, without relying on
 * {@code java.util.*}. Elements must implement {@link Comparable} so the
 * tree can decide where each value belongs.
 *
 * <p>Average-case complexities below assume a reasonably balanced tree.
 * This implementation does not self-balance (it is not an AVL or Red-Black
 * tree), so a worst case of O(n) is possible when elements are inserted in
 * already-sorted order, which degenerates the tree into a linked list.</p>
 *
 * @param <T> the type of elements stored in this tree, must be Comparable
 */
public class BST<T extends Comparable<T>> {

    private static class Node<T> {
        private T data;
        private Node<T> left;
        private Node<T> right;

        private Node(T data) {
            this.data = data;
        }
    }

    private Node<T> root;
    private int size;

    /**
     * Creates an empty binary search tree.
     * @complexity O(1)
     */
    public BST() {
        this.root = null;
        this.size = 0;
    }

    /**
     * Inserts a new value into the tree. Duplicate values are ignored.
     *
     * @param value the value to insert
     * @complexity O(log n) average, O(n) worst case (unbalanced tree)
     */
    public void insert(T value) {
        root = insertRecursive(root, value);
    }

    private Node<T> insertRecursive(Node<T> node, T value) {
        if (node == null) {
            size++;
            return new Node<>(value);
        }
        int cmp = value.compareTo(node.data);
        if (cmp < 0) {
            node.left = insertRecursive(node.left, value);
        } else if (cmp > 0) {
            node.right = insertRecursive(node.right, value);
        }
        // cmp == 0 -> duplicate, ignored
        return node;
    }

    /**
     * Checks whether a value exists in the tree.
     *
     * @param value the value to search for
     * @return true if found, false otherwise
     * @complexity O(log n) average, O(n) worst case
     */
    public boolean search(T value) {
        Node<T> current = root;
        while (current != null) {
            int cmp = value.compareTo(current.data);
            if (cmp == 0) {
                return true;
            }
            current = cmp < 0 ? current.left : current.right;
        }
        return false;
    }

    /**
     * Removes a value from the tree, if present.
     *
     * @param value the value to remove
     * @return true if a node was removed, false if the value was not found
     * @complexity O(log n) average, O(n) worst case
     */
    public boolean delete(T value) {
        int sizeBefore = size;
        root = deleteRecursive(root, value);
        return size < sizeBefore;
    }

    private Node<T> deleteRecursive(Node<T> node, T value) {
        if (node == null) {
            return null;
        }
        int cmp = value.compareTo(node.data);
        if (cmp < 0) {
            node.left = deleteRecursive(node.left, value);
        } else if (cmp > 0) {
            node.right = deleteRecursive(node.right, value);
        } else {
            // Node found: this is the only branch that should decrement size
            size--;
            if (node.left == null && node.right == null) {
                return null;
            }
            if (node.left == null) {
                return node.right;
            }
            if (node.right == null) {
                return node.left;
            }
            // Two children: replace with the smallest value of the right subtree,
            // then physically remove that successor node (without touching size again).
            Node<T> successor = findMinNode(node.right);
            node.data = successor.data;
            node.right = deleteMinNode(node.right);
        }
        return node;
    }

    /**
     * Removes the leftmost (minimum) node of the given subtree and returns
     * the resulting subtree. Used internally by {@link #deleteRecursive}
     * to physically detach a successor node after its value has already
     * been copied upward; does not affect {@code size}.
     */
    private Node<T> deleteMinNode(Node<T> node) {
        if (node.left == null) {
            return node.right;
        }
        node.left = deleteMinNode(node.left);
        return node;
    }

    /**
     * Returns the smallest value stored in the tree.
     *
     * @return the minimum value
     * @throws EmptyStructureException if the tree is empty
     * @complexity O(log n) average, O(n) worst case
     */
    public T findMin() {
        if (isEmpty()) {
            throw new EmptyStructureException("Cannot findMin() on an empty BST");
        }
        return findMinNode(root).data;
    }

    private Node<T> findMinNode(Node<T> node) {
        while (node.left != null) {
            node = node.left;
        }
        return node;
    }

    /**
     * Returns the largest value stored in the tree.
     *
     * @return the maximum value
     * @throws EmptyStructureException if the tree is empty
     * @complexity O(log n) average, O(n) worst case
     */
    public T findMax() {
        if (isEmpty()) {
            throw new EmptyStructureException("Cannot findMax() on an empty BST");
        }
        Node<T> current = root;
        while (current.right != null) {
            current = current.right;
        }
        return current.data;
    }

    /**
     * Returns the height of the tree (number of edges on the longest
     * root-to-leaf path). An empty tree has height -1.
     *
     * @complexity O(n)
     */
    public int height() {
        return heightRecursive(root);
    }

    private int heightRecursive(Node<T> node) {
        if (node == null) {
            return -1;
        }
        return 1 + Math.max(heightRecursive(node.left), heightRecursive(node.right));
    }

    /**
     * Returns all elements in ascending order using an in-order traversal.
     *
     * @return a custom LinkedList with the elements sorted ascending
     * @complexity O(n)
     */
    public LinkedList<T> inOrder() {
        LinkedList<T> result = new LinkedList<>();
        inOrderRecursive(root, result);
        return result;
    }

    private void inOrderRecursive(Node<T> node, LinkedList<T> result) {
        if (node == null) {
            return;
        }
        inOrderRecursive(node.left, result);
        result.addLast(node.data);
        inOrderRecursive(node.right, result);
    }

    /**
     * Returns the number of elements currently stored.
     * @complexity O(1)
     */
    public int size() {
        return size;
    }

    /**
     * Returns true if the tree has no elements.
     * @complexity O(1)
     */
    public boolean isEmpty() {
        return size == 0;
    }

    /**
     * Removes every element from the tree.
     * @complexity O(1)
     */
    public void clear() {
        root = null;
        size = 0;
    }
}
