package com.sleekydz86.backend.global.circuitbreaker

import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.AtomicReference
import com.sleekydz86.backend.global.exception.CircuitBreakerOpenException

enum class CircuitState {
    CLOSED, OPEN, HALF_OPEN
}

class CircuitBreaker(
    private val failureThreshold: Int = 5,
    private val timeoutDuration: Duration = Duration.ofMinutes(1),
    private val retryDuration: Duration = Duration.ofSeconds(30)
) {
    private val failureCount = AtomicInteger(0)
    private val lastFailureTime = AtomicLong(0)
    private val state = AtomicReference(CircuitState.CLOSED)

    fun <T> execute(operation: () -> Mono<T>): Mono<T> =
        when (state.get()) {
            CircuitState.CLOSED -> executeOperation(operation)
            CircuitState.OPEN -> handleOpenState<T>()
            CircuitState.HALF_OPEN -> executeOperation(operation)
        }

    fun <T> executeFlux(operation: () -> Flux<T>): Flux<T> =
        when (state.get()) {
            CircuitState.CLOSED -> executeFluxOperation(operation)
            CircuitState.OPEN -> Flux.error(CircuitBreakerOpenException("Circuit breaker is open"))
            CircuitState.HALF_OPEN -> executeFluxOperation(operation)
        }

    private fun <T> executeOperation(operation: () -> Mono<T>): Mono<T> =
        operation()
            .doOnSuccess { onSuccess() }
            .doOnError { onFailure() }
            .onErrorResume { error ->
                if (state.get() == CircuitState.OPEN) {
                    Mono.error(CircuitBreakerOpenException("Circuit breaker is open"))
                } else {
                    Mono.error(error)
                }
            }

    private fun <T> executeFluxOperation(operation: () -> Flux<T>): Flux<T> =
        operation()
            .doOnComplete { onSuccess() }
            .doOnError { onFailure() }
            .onErrorResume { error ->
                if (state.get() == CircuitState.OPEN) {
                    Flux.error(CircuitBreakerOpenException("Circuit breaker is open"))
                } else {
                    Flux.error(error)
                }
            }

    private fun onSuccess() {
        failureCount.set(0)
        state.set(CircuitState.CLOSED)
    }

    private fun onFailure() {
        val currentTime = System.currentTimeMillis()
        lastFailureTime.set(currentTime)

        val failures = failureCount.incrementAndGet()
        if (failures >= failureThreshold) {
            state.set(CircuitState.OPEN)
        }
    }

    private fun <T> handleOpenState(): Mono<T> {
        val currentTime = System.currentTimeMillis()
        val timeSinceLastFailure = currentTime - lastFailureTime.get()

        return if (timeSinceLastFailure >= retryDuration.toMillis()) {
            state.set(CircuitState.HALF_OPEN)
            Mono.error<T>(CircuitBreakerOpenException("Circuit breaker transitioning to half-open"))
        } else {
            Mono.error<T>(CircuitBreakerOpenException("Circuit breaker is open"))
        }
    }

    fun getState(): CircuitState = state.get()
    fun getFailureCount(): Int = failureCount.get()
    fun isOpen(): Boolean = state.get() == CircuitState.OPEN
    fun isClosed(): Boolean = state.get() == CircuitState.CLOSED
    fun isHalfOpen(): Boolean = state.get() == CircuitState.HALF_OPEN
}
