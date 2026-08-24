package com.reservas.estructuras;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class LinkedListTest {

    private LinkedList<Integer> list;

    @BeforeEach
    void setUp() {
        list = new LinkedList<>();
    }

    @Test
    void newListShouldBeEmpty() {
        assertThat(list.isEmpty()).isTrue();
        assertThat(list.size()).isZero();
    }

    @Test
    void addLastShouldInsertElementsInOrder() {
        list.addLast(1);
        list.addLast(2);
        list.addLast(3);

        assertThat(list.size()).isEqualTo(3);
        assertThat(list.get(0)).isEqualTo(1);
        assertThat(list.get(1)).isEqualTo(2);
        assertThat(list.get(2)).isEqualTo(3);
    }

    @Test
    void addFirstShouldInsertAtTheBeginning() {
        list.addLast(2);
        list.addFirst(1);

        assertThat(list.get(0)).isEqualTo(1);
        assertThat(list.get(1)).isEqualTo(2);
    }

    @Test
    void containsShouldFindExistingAndRejectMissingElements() {
        list.addLast(10);
        list.addLast(20);

        assertThat(list.contains(10)).isTrue();
        assertThat(list.contains(99)).isFalse();
    }

    @Test
    void removeShouldDeleteAnExistingElement() {
        list.addLast(1);
        list.addLast(2);
        list.addLast(3);

        boolean removed = list.remove(2);

        assertThat(removed).isTrue();
        assertThat(list.contains(2)).isFalse();
        assertThat(list.size()).isEqualTo(2);
    }

    @Test
    void removeFirstShouldReturnAndDropTheHead() {
        list.addLast(10);
        list.addLast(20);

        int first = list.removeFirst();

        assertThat(first).isEqualTo(10);
        assertThat(list.size()).isEqualTo(1);
    }

    @Test
    void removeFirstOnEmptyListShouldThrowEmptyStructureException() {
        assertThatThrownBy(() -> list.removeFirst())
                .isInstanceOf(EmptyStructureException.class);
    }

    @Test
    void getWithOutOfRangeIndexShouldThrow() {
        list.addLast(1);

        assertThatThrownBy(() -> list.get(5))
                .isInstanceOf(IndexOutOfBoundsException.class);
    }

    @Test
    void clearShouldEmptyTheList() {
        list.addLast(1);
        list.addLast(2);

        list.clear();

        assertThat(list.isEmpty()).isTrue();
        assertThat(list.size()).isZero();
    }
}
