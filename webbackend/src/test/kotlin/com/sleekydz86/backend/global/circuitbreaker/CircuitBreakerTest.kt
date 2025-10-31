package com.sleekydz86.backend.global.circuitbreaker

import com.sleekydz86.backend.global.exception.CircuitBreakerOpenException
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import reactor.test.StepVerifier
import java.time.Duration

class CircuitBreakerTest {

    private lateinit var circuitBreaker: CircuitBreaker

    @BeforeEach
    fun setUp() {
        circuitBreaker = CircuitBreaker(
            failureThreshold = 3,
            timeoutDuration = Duration.ofMinutes(1),
            retryDuration = Duration.ofSeconds(1)
        )
    }

    @Test
    @DisplayName("회로 차단기 실행 - 성공 시 CLOSED 상태 유지")
    fun `execute - should remain CLOSED when operation succeeds`() {
        //given
        val data = "success"
        val operation = { Mono.just(data) }

        //when
        val result = circuitBreaker.execute(operation)

        //then
        StepVerifier.create(result)
            .expectNext(data)
            .verifyComplete()
        assertEquals(CircuitState.CLOSED, circuitBreaker.getState())
        assertEquals(0, circuitBreaker.getFailureCount())
    }

    @Test
    @DisplayName("회로 차단기 실행 - 실패 횟수가 임계값 미만일 때 CLOSED 상태 유지")
    fun `execute - should remain CLOSED when failure count is below threshold`() {
        //given
        val error = RuntimeException("Error")
        var callCount = 0
        val operation = {
            callCount++
            if (callCount < 3) Mono.error(error) else Mono.just("success")
        }

        //when & then
        StepVerifier.create(circuitBreaker.execute(operation))
            .expectError(RuntimeException::class.java)
            .verify()

        StepVerifier.create(circuitBreaker.execute(operation))
            .expectError(RuntimeException::class.java)
            .verify()

        assertEquals(CircuitState.CLOSED, circuitBreaker.getState())
        assertTrue(circuitBreaker.isClosed())
    }

    @Test
    @DisplayName("회로 차단기 실행 - 실패 횟수가 임계값에 도달하면 OPEN 상태로 전환")
    fun `execute - should transition to OPEN when failure threshold is reached`() {
        //given
        val error = RuntimeException("Error")
        val operation = { Mono.error<String>(error) }

        //when
        repeat(3) {
            StepVerifier.create(circuitBreaker.execute(operation))
                .expectError()
                .verify()
        }

        //then
        assertEquals(CircuitState.OPEN, circuitBreaker.getState())
        assertTrue(circuitBreaker.isOpen())
        assertFalse(circuitBreaker.isClosed())
    }

    @Test
    @DisplayName("회로 차단기 실행 - OPEN 상태일 때 CircuitBreakerOpenException 발생")
    fun `execute - should throw CircuitBreakerOpenException when OPEN`() {
        //given
        val error = RuntimeException("Error")
        val operation = { Mono.error<String>(error) }

        repeat(3) {
            StepVerifier.create(circuitBreaker.execute(operation))
                .expectError()
                .verify()
        }

        //when
        val result = circuitBreaker.execute { Mono.just("test") }

        //then
        StepVerifier.create(result)
            .expectError(CircuitBreakerOpenException::class.java)
            .verify()
    }

    @Test
    @DisplayName("회로 차단기 실행 - 재시도 시간 후 HALF_OPEN 상태로 전환")
    fun `execute - should transition to HALF_OPEN after retry duration`() {
        //given
        val error = RuntimeException("Error")
        val operation = { Mono.error<String>(error) }

        repeat(3) {
            StepVerifier.create(circuitBreaker.execute(operation))
                .expectError()
                .verify()
        }

        assertEquals(CircuitState.OPEN, circuitBreaker.getState())

        //when
        Thread.sleep(1100)

        //then
        val result = circuitBreaker.execute { Mono.just("test") }
        StepVerifier.create(result)
            .expectError(CircuitBreakerOpenException::class.java)
            .verify()
    }

    @Test
    @DisplayName("회로 차단기 실행 - HALF_OPEN 상태에서 성공 시 CLOSED로 복귀")
    fun `execute - should return to CLOSED when HALF_OPEN operation succeeds`() {
        //given
        val error = RuntimeException("Error")
        val failureOperation = { Mono.error<String>(error) }

        repeat(3) {
            StepVerifier.create(circuitBreaker.execute(failureOperation))
                .expectError()
                .verify()
        }

        Thread.sleep(1100)

        //when
        val successOperation = { Mono.just("success") }
        val result = circuitBreaker.execute(successOperation)

        //then
        StepVerifier.create(result)
            .expectNext("success")
            .verifyComplete()
        assertEquals(CircuitState.CLOSED, circuitBreaker.getState())
        assertEquals(0, circuitBreaker.getFailureCount())
    }

    @Test
    @DisplayName("회로 차단기 Flux 실행 - 성공 시 CLOSED 상태 유지")
    fun `executeFlux - should remain CLOSED when operation succeeds`() {
        //given
        val data = listOf("item1", "item2")
        val operation = { Flux.fromIterable(data) }

        //when
        val result = circuitBreaker.executeFlux(operation)

        //then
        StepVerifier.create(result)
            .expectNext("item1")
            .expectNext("item2")
            .verifyComplete()
        assertEquals(CircuitState.CLOSED, circuitBreaker.getState())
    }

    @Test
    @DisplayName("회로 차단기 Flux 실행 - OPEN 상태일 때 CircuitBreakerOpenException 발생")
    fun `executeFlux - should throw CircuitBreakerOpenException when OPEN`() {
        //given
        val error = RuntimeException("Error")
        val operation = { Flux.error<String>(error) }

        repeat(3) {
            StepVerifier.create(circuitBreaker.executeFlux(operation))
                .expectError()
                .verify()
        }

        //when
        val result = circuitBreaker.executeFlux { Flux.just("test") }

        //then
        StepVerifier.create(result)
            .expectError(CircuitBreakerOpenException::class.java)
            .verify()
    }

    @Test
    @DisplayName("회로 차단기 상태 확인 - isClosed 메서드")
    fun `isClosed - should return true when circuit is CLOSED`() {
        //given
        val operation = { Mono.just("success") }

        //when
        StepVerifier.create(circuitBreaker.execute(operation))
            .expectNext("success")
            .verifyComplete()

        //then
        assertTrue(circuitBreaker.isClosed())
        assertFalse(circuitBreaker.isOpen())
        assertFalse(circuitBreaker.isHalfOpen())
    }

    @Test
    @DisplayName("회로 차단기 상태 확인 - isOpen 메서드")
    fun `isOpen - should return true when circuit is OPEN`() {
        //given
        val error = RuntimeException("Error")
        val operation = { Mono.error<String>(error) }

        //when
        repeat(3) {
            StepVerifier.create(circuitBreaker.execute(operation))
                .expectError()
                .verify()
        }

        //then
        assertTrue(circuitBreaker.isOpen())
        assertFalse(circuitBreaker.isClosed())
    }

    @Test
    @DisplayName("회로 차단기 실패 횟수 확인 - 실패 후 카운트 증가")
    fun `getFailureCount - should increment after failures`() {
        //given
        val error = RuntimeException("Error")
        val operation = { Mono.error<String>(error) }

        //when
        StepVerifier.create(circuitBreaker.execute(operation))
            .expectError()
            .verify()

        //then
        assertEquals(1, circuitBreaker.getFailureCount())
    }

    @Test
    @DisplayName("회로 차단기 실패 횟수 확인 - 성공 시 카운트 리셋")
    fun `getFailureCount - should reset count after success`() {
        //given
        val error = RuntimeException("Error")
        val failureOperation = { Mono.error<String>(error) }
        val successOperation = { Mono.just("success") }

        StepVerifier.create(circuitBreaker.execute(failureOperation))
            .expectError()
            .verify()

        assertEquals(1, circuitBreaker.getFailureCount())

        //when
        StepVerifier.create(circuitBreaker.execute(successOperation))
            .expectNext("success")
            .verifyComplete()

        //then
        assertEquals(0, circuitBreaker.getFailureCount())
    }
}
