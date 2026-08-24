package com.reservas.benchmark;

import com.reservas.estructuras.BST;
import com.reservas.estructuras.LinkedList;
import com.reservas.estructuras.Queue;
import com.reservas.estructuras.Stack;

/**
 * Benchmarks insertion, search and deletion for the four custom data
 * structures ({@code LinkedList}, {@code Stack}, {@code Queue}, {@code BST})
 * with 1.000, 10.000 and 100.000 elements, as required by the "Sesion 3"
 * assignment. Results are printed to the console as a simple table.
 *
 * <p>Run with:
 * <pre>{@code mvn compile exec:java@run-benchmark}</pre>
 * or directly with {@code mvn exec:java -Dexec.mainClass=com.reservas.benchmark.BenchmarkRunner}
 * after {@code mvn compile}.</p>
 */
public final class BenchmarkRunner {

    private static final int[] SIZES = {1_000, 10_000, 100_000};

    private BenchmarkRunner() {
    }

    public static void main(String[] args) {
        System.out.println("=== Benchmark: Galeria de Estructuras de Datos ===");
        System.out.printf("%-12s %-10s %-15s %-15s %-15s%n", "Estructura", "N", "Insercion(ms)", "Busqueda(ms)", "Eliminacion(ms)");
        System.out.println("-".repeat(70));

        for (int n : SIZES) {
            benchmarkLinkedList(n);
            benchmarkStack(n);
            benchmarkQueue(n);
            benchmarkBST(n);
        }
    }

    private static void benchmarkLinkedList(int n) {
        LinkedList<Integer> list = new LinkedList<>();

        long insertStart = System.nanoTime();
        for (int i = 0; i < n; i++) {
            list.addLast(i);
        }
        long insertMs = toMillis(System.nanoTime() - insertStart);

        long searchStart = System.nanoTime();
        list.contains(n / 2);
        list.contains(-1); // worst case: not found, forces full traversal
        long searchMs = toMillis(System.nanoTime() - searchStart);

        long deleteStart = System.nanoTime();
        for (int i = 0; i < Math.min(1000, n); i++) {
            list.removeFirst();
        }
        long deleteMs = toMillis(System.nanoTime() - deleteStart);

        printRow("LinkedList", n, insertMs, searchMs, deleteMs);
    }

    private static void benchmarkStack(int n) {
        Stack<Integer> stack = new Stack<>();

        long insertStart = System.nanoTime();
        for (int i = 0; i < n; i++) {
            stack.push(i);
        }
        long insertMs = toMillis(System.nanoTime() - insertStart);

        long searchStart = System.nanoTime();
        stack.contains(n / 2);
        stack.contains(-1);
        long searchMs = toMillis(System.nanoTime() - searchStart);

        long deleteStart = System.nanoTime();
        for (int i = 0; i < Math.min(1000, n); i++) {
            stack.pop();
        }
        long deleteMs = toMillis(System.nanoTime() - deleteStart);

        printRow("Stack", n, insertMs, searchMs, deleteMs);
    }

    private static void benchmarkQueue(int n) {
        Queue<Integer> queue = new Queue<>();

        long insertStart = System.nanoTime();
        for (int i = 0; i < n; i++) {
            queue.enqueue(i);
        }
        long insertMs = toMillis(System.nanoTime() - insertStart);

        long searchStart = System.nanoTime();
        queue.contains(n / 2);
        queue.contains(-1);
        long searchMs = toMillis(System.nanoTime() - searchStart);

        long deleteStart = System.nanoTime();
        for (int i = 0; i < Math.min(1000, n); i++) {
            queue.dequeue();
        }
        long deleteMs = toMillis(System.nanoTime() - deleteStart);

        printRow("Queue", n, insertMs, searchMs, deleteMs);
    }

    private static void benchmarkBST(int n) {
        BST<Integer> tree = new BST<>();

        // Insert in a shuffled order so the tree stays reasonably balanced
        // (sequential insertion would degenerate a plain BST into a list).
        int[] values = shuffledRange(n);

        long insertStart = System.nanoTime();
        for (int value : values) {
            tree.insert(value);
        }
        long insertMs = toMillis(System.nanoTime() - insertStart);

        long searchStart = System.nanoTime();
        tree.search(n / 2);
        tree.search(-1);
        long searchMs = toMillis(System.nanoTime() - searchStart);

        long deleteStart = System.nanoTime();
        for (int i = 0; i < Math.min(1000, n); i++) {
            tree.delete(values[i]);
        }
        long deleteMs = toMillis(System.nanoTime() - deleteStart);

        printRow("BST", n, insertMs, searchMs, deleteMs);
    }

    private static int[] shuffledRange(int n) {
        int[] values = new int[n];
        for (int i = 0; i < n; i++) {
            values[i] = i;
        }
        // Simple linear congruential generator so the benchmark does not
        // depend on java.util for randomness either.
        long seed = 88172645463325252L ^ n;
        for (int i = n - 1; i > 0; i--) {
            seed ^= (seed << 13);
            seed ^= (seed >>> 7);
            seed ^= (seed << 17);
            int j = (int) (Math.floorMod(seed, (long) (i + 1)));
            int tmp = values[i];
            values[i] = values[j];
            values[j] = tmp;
        }
        return values;
    }

    private static long toMillis(long nanos) {
        return nanos / 1_000_000;
    }

    private static void printRow(String structure, int n, long insertMs, long searchMs, long deleteMs) {
        System.out.printf("%-12s %-10d %-15d %-15d %-15d%n", structure, n, insertMs, searchMs, deleteMs);
    }
}
