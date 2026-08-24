package com.reservas.estructuras;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class BSTTest {

    private BST<Integer> tree;

    @BeforeEach
    void setUp() {
        tree = new BST<>();
    }

    @Test
    void newTreeShouldBeEmpty() {
        assertThat(tree.isEmpty()).isTrue();
        assertThat(tree.size()).isZero();
    }

    @Test
    void insertShouldGrowTheTreeAndKeepOrder() {
        tree.insert(50);
        tree.insert(30);
        tree.insert(70);
        tree.insert(20);
        tree.insert(40);

        assertThat(tree.size()).isEqualTo(5);
        assertThat(tree.inOrder().toArray()).containsExactly(20, 30, 40, 50, 70);
    }

    @Test
    void searchShouldFindExistingAndRejectMissingValues() {
        tree.insert(50);
        tree.insert(30);
        tree.insert(70);

        assertThat(tree.search(30)).isTrue();
        assertThat(tree.search(999)).isFalse();
    }

    @Test
    void deleteShouldRemoveLeafNode() {
        tree.insert(50);
        tree.insert(30);
        tree.insert(70);

        boolean removed = tree.delete(30);

        assertThat(removed).isTrue();
        assertThat(tree.search(30)).isFalse();
        assertThat(tree.size()).isEqualTo(2);
    }

    @Test
    void deleteShouldRemoveNodeWithTwoChildrenAndKeepBstProperty() {
        int[] values = {50, 30, 70, 20, 40, 60, 80};
        for (int v : values) {
            tree.insert(v);
        }

        boolean removed = tree.delete(50);

        assertThat(removed).isTrue();
        assertThat(tree.size()).isEqualTo(6);
        assertThat(tree.search(50)).isFalse();
        assertThat(tree.inOrder().toArray()).containsExactly(20, 30, 40, 60, 70, 80);
    }

    @Test
    void deleteMissingValueShouldReturnFalseAndKeepSize() {
        tree.insert(50);

        boolean removed = tree.delete(999);

        assertThat(removed).isFalse();
        assertThat(tree.size()).isEqualTo(1);
    }

    @Test
    void findMinAndFindMaxShouldReturnBoundaryValues() {
        int[] values = {50, 30, 70, 20, 40, 60, 80};
        for (int v : values) {
            tree.insert(v);
        }

        assertThat(tree.findMin()).isEqualTo(20);
        assertThat(tree.findMax()).isEqualTo(80);
    }

    @Test
    void findMinOnEmptyTreeShouldThrowEmptyStructureException() {
        assertThatThrownBy(() -> tree.findMin())
                .isInstanceOf(EmptyStructureException.class);
    }
}
