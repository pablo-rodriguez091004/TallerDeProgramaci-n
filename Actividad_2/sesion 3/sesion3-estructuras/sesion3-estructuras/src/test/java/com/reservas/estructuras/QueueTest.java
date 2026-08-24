package com.reservas.estructuras;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class QueueTest {

    private Queue<Integer> queue;

    @BeforeEach
    void setUp() {
        queue = new Queue<>();
    }

    @Test
    void newQueueShouldBeEmpty() {
        assertThat(queue.isEmpty()).isTrue();
        assertThat(queue.size()).isZero();
    }

    @Test
    void enqueueShouldAddElementsAtTheBack() {
        queue.enqueue(1);
        queue.enqueue(2);
        queue.enqueue(3);

        assertThat(queue.size()).isEqualTo(3);
        assertThat(queue.peek()).isEqualTo(1);
    }

    @Test
    void dequeueShouldFollowFifoOrder() {
        queue.enqueue(1);
        queue.enqueue(2);
        queue.enqueue(3);

        assertThat(queue.dequeue()).isEqualTo(1);
        assertThat(queue.dequeue()).isEqualTo(2);
        assertThat(queue.dequeue()).isEqualTo(3);
        assertThat(queue.isEmpty()).isTrue();
    }

    @Test
    void containsShouldFindExistingAndRejectMissingElements() {
        queue.enqueue(7);
        queue.enqueue(8);

        assertThat(queue.contains(7)).isTrue();
        assertThat(queue.contains(123)).isFalse();
    }

    @Test
    void dequeueOnEmptyQueueShouldThrowEmptyStructureException() {
        assertThatThrownBy(() -> queue.dequeue())
                .isInstanceOf(EmptyStructureException.class);
    }

    @Test
    void peekOnEmptyQueueShouldThrowEmptyStructureException() {
        assertThatThrownBy(() -> queue.peek())
                .isInstanceOf(EmptyStructureException.class);
    }

    @Test
    void clearShouldEmptyTheQueue() {
        queue.enqueue(1);
        queue.enqueue(2);

        queue.clear();

        assertThat(queue.isEmpty()).isTrue();
        assertThat(queue.size()).isZero();
    }
}
