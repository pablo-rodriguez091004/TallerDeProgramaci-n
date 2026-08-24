package com.reservas.estructuras;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class StackTest {

    private Stack<Integer> stack;

    @BeforeEach
    void setUp() {
        stack = new Stack<>();
    }

    @Test
    void newStackShouldBeEmpty() {
        assertThat(stack.isEmpty()).isTrue();
        assertThat(stack.size()).isZero();
    }

    @Test
    void pushShouldInsertElementsOnTop() {
        stack.push(1);
        stack.push(2);
        stack.push(3);

        assertThat(stack.size()).isEqualTo(3);
        assertThat(stack.peek()).isEqualTo(3);
    }

    @Test
    void popShouldFollowLifoOrder() {
        stack.push(1);
        stack.push(2);
        stack.push(3);

        assertThat(stack.pop()).isEqualTo(3);
        assertThat(stack.pop()).isEqualTo(2);
        assertThat(stack.pop()).isEqualTo(1);
        assertThat(stack.isEmpty()).isTrue();
    }

    @Test
    void containsShouldFindExistingAndRejectMissingElements() {
        stack.push(5);
        stack.push(10);

        assertThat(stack.contains(5)).isTrue();
        assertThat(stack.contains(999)).isFalse();
    }

    @Test
    void popOnEmptyStackShouldThrowEmptyStructureException() {
        assertThatThrownBy(() -> stack.pop())
                .isInstanceOf(EmptyStructureException.class);
    }

    @Test
    void peekOnEmptyStackShouldThrowEmptyStructureException() {
        assertThatThrownBy(() -> stack.peek())
                .isInstanceOf(EmptyStructureException.class);
    }

    @Test
    void clearShouldEmptyTheStack() {
        stack.push(1);
        stack.push(2);

        stack.clear();

        assertThat(stack.isEmpty()).isTrue();
        assertThat(stack.size()).isZero();
    }
}
