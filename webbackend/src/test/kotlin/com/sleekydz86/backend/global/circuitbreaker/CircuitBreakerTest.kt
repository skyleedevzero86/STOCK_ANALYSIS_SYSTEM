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
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏??§Ìñâ - ?±Í≥µ ??CLOSED ?ÅÌÉú ?†Ï?")
    fun `execute - should remain CLOSED when operation succeeds`() {

        val data = "success"
        val operation = { Mono.just(data) }

        val result = circuitBreaker.execute(operation)

        StepVerifier.create(result)
            .expectNext(data)
            .verifyComplete()
        assertEquals(CircuitState.CLOSED, circuitBreaker.getState())
        assertEquals(0, circuitBreaker.getFailureCount())
    }

    @Test
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏??§Ìñâ - ?§Ìå® ?üÏàòÍ∞Ä ?ÑÍ≥ÑÍ∞?ÎØ∏Îßå????CLOSED ?ÅÌÉú ?†Ï?")
    fun `execute - should remain CLOSED when failure count is below threshold`() {

        val error = RuntimeException("Error")
        var callCount = 0
        val operation = {
            callCount++
            if (callCount < 3) Mono.error(error) else Mono.just("success")
        }

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
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏??§Ìñâ - ?§Ìå® ?üÏàòÍ∞Ä ?ÑÍ≥ÑÍ∞íÏóê ?ÑÎã¨?òÎ©¥ OPEN ?ÅÌÉúÎ°??ÑÌôò")
    fun `execute - should transition to OPEN when failure threshold is reached`() {

        val error = RuntimeException("Error")
        val operation = { Mono.error<String>(error) }

        repeat(3) {
            StepVerifier.create(circuitBreaker.execute(operation))
                .expectError()
                .verify()
        }

        assertEquals(CircuitState.OPEN, circuitBreaker.getState())
        assertTrue(circuitBreaker.isOpen())
        assertFalse(circuitBreaker.isClosed())
    }

    @Test
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏??§Ìñâ - OPEN ?ÅÌÉú????CircuitBreakerOpenException Î∞úÏÉù")
    fun `execute - should throw CircuitBreakerOpenException when OPEN`() {

        val error = RuntimeException("Error")
        val operation = { Mono.error<String>(error) }

        repeat(3) {
            StepVerifier.create(circuitBreaker.execute(operation))
                .expectError()
                .verify()
        }

        val result = circuitBreaker.execute { Mono.just("test") }

        StepVerifier.create(result)
            .expectError(CircuitBreakerOpenException::class.java)
            .verify()
    }

    @Test
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏??§Ìñâ - ?¨Ïãú???úÍ∞Ñ ??HALF_OPEN ?ÅÌÉúÎ°??ÑÌôò")
    fun `execute - should transition to HALF_OPEN after retry duration`() {

        val error = RuntimeException("Error")
        val operation = { Mono.error<String>(error) }

        repeat(3) {
            StepVerifier.create(circuitBreaker.execute(operation))
                .expectError()
                .verify()
        }

        assertEquals(CircuitState.OPEN, circuitBreaker.getState())

        Thread.sleep(1100)

        val result = circuitBreaker.execute { Mono.just("test") }
        StepVerifier.create(result)
            .expectError(CircuitBreakerOpenException::class.java)
            .verify()
    }

    @Test
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏??§Ìñâ - HALF_OPEN ?ÅÌÉú?êÏÑú ?±Í≥µ ??CLOSEDÎ°?Î≥µÍ?")
    fun `execute - should return to CLOSED when HALF_OPEN operation succeeds`() {

        val error = RuntimeException("Error")
        val failureOperation = { Mono.error<String>(error) }

        repeat(3) {
            StepVerifier.create(circuitBreaker.execute(failureOperation))
                .expectError()
                .verify()
        }

        Thread.sleep(1100)

        val successOperation = { Mono.just("success") }
        val result = circuitBreaker.execute(successOperation)

        StepVerifier.create(result)
            .expectNext("success")
            .verifyComplete()
        assertEquals(CircuitState.CLOSED, circuitBreaker.getState())
        assertEquals(0, circuitBreaker.getFailureCount())
    }

    @Test
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏?Flux ?§Ìñâ - ?±Í≥µ ??CLOSED ?ÅÌÉú ?†Ï?")
    fun `executeFlux - should remain CLOSED when operation succeeds`() {

        val data = listOf("item1", "item2")
        val operation = { Flux.fromIterable(data) }

        val result = circuitBreaker.executeFlux(operation)

        StepVerifier.create(result)
            .expectNext("item1")
            .expectNext("item2")
            .verifyComplete()
        assertEquals(CircuitState.CLOSED, circuitBreaker.getState())
    }

    @Test
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏?Flux ?§Ìñâ - OPEN ?ÅÌÉú????CircuitBreakerOpenException Î∞úÏÉù")
    fun `executeFlux - should throw CircuitBreakerOpenException when OPEN`() {

        val error = RuntimeException("Error")
        val operation = { Flux.error<String>(error) }

        repeat(3) {
            StepVerifier.create(circuitBreaker.executeFlux(operation))
                .expectError()
                .verify()
        }

        val result = circuitBreaker.executeFlux { Flux.just("test") }

        StepVerifier.create(result)
            .expectError(CircuitBreakerOpenException::class.java)
            .verify()
    }

    @Test
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏??ÅÌÉú ?ïÏù∏ - isClosed Î©îÏÑú??)
    fun `isClosed - should return true when circuit is CLOSED`() {

        val operation = { Mono.just("success") }

        StepVerifier.create(circuitBreaker.execute(operation))
            .expectNext("success")
            .verifyComplete()

        assertTrue(circuitBreaker.isClosed())
        assertFalse(circuitBreaker.isOpen())
        assertFalse(circuitBreaker.isHalfOpen())
    }

    @Test
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏??ÅÌÉú ?ïÏù∏ - isOpen Î©îÏÑú??)
    fun `isOpen - should return true when circuit is OPEN`() {

        val error = RuntimeException("Error")
        val operation = { Mono.error<String>(error) }

        repeat(3) {
            StepVerifier.create(circuitBreaker.execute(operation))
                .expectError()
                .verify()
        }

        assertTrue(circuitBreaker.isOpen())
        assertFalse(circuitBreaker.isClosed())
    }

    @Test
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏??§Ìå® ?üÏàò ?ïÏù∏ - ?§Ìå® ??Ïπ¥Ïö¥??Ï¶ùÍ?")
    fun `getFailureCount - should increment after failures`() {

        val error = RuntimeException("Error")
        val operation = { Mono.error<String>(error) }

        StepVerifier.create(circuitBreaker.execute(operation))
            .expectError()
            .verify()

        assertEquals(1, circuitBreaker.getFailureCount())
    }

    @Test
    @DisplayName("?åÎ°ú Ï∞®Îã®Í∏??§Ìå® ?üÏàò ?ïÏù∏ - ?±Í≥µ ??Ïπ¥Ïö¥??Î¶¨ÏÖã")
    fun `getFailureCount - should reset count after success`() {

        val error = RuntimeException("Error")
        val failureOperation = { Mono.error<String>(error) }
        val successOperation = { Mono.just("success") }

        StepVerifier.create(circuitBreaker.execute(failureOperation))
            .expectError()
            .verify()

        assertEquals(1, circuitBreaker.getFailureCount())

        StepVerifier.create(circuitBreaker.execute(successOperation))
            .expectNext("success")
            .verifyComplete()

        assertEquals(0, circuitBreaker.getFailureCount())
    }
}
