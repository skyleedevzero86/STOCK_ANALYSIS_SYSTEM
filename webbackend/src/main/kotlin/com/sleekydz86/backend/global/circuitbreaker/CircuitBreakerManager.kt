package com.sleekydz86.backend.global.circuitbreaker

import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration
import java.util.concurrent.ConcurrentHashMap

@Component
class CircuitBreakerManager {

    private val circuitBreakers = ConcurrentHashMap<String, CircuitBreaker>()

    fun getCircuitBreaker(name: String): CircuitBreaker =
        circuitBreakers.computeIfAbsent(name) {
            CircuitBreaker(
                failureThreshold = 5,
                timeoutDuration = Duration.ofMinutes(1),
                retryDuration = Duration.ofSeconds(30)
            )
        }

    fun <T> executeWithCircuitBreaker(
        name: String,
        operation: () -> Mono<T>
    ): Mono<T> =
        getCircuitBreaker(name).execute(operation)

    fun <T> executeFluxWithCircuitBreaker(
        name: String,
        operation: () -> Flux<T>
    ): Flux<T> =
        getCircuitBreaker(name).executeFlux(operation)

    fun getCircuitBreakerStatus(name: String): Map<String, Any> {
        val breaker = getCircuitBreaker(name)
        return mapOf(
            "name" to name,
            "state" to breaker.getState().name,
            "failureCount" to breaker.getFailureCount(),
            "isOpen" to breaker.isOpen(),
            "isClosed" to breaker.isClosed(),
            "isHalfOpen" to breaker.isHalfOpen()
        )
    }

    fun getAllCircuitBreakerStatus(): Map<String, Map<String, Any>> =
        circuitBreakers.mapValues { (name, _) -> getCircuitBreakerStatus(name) }

    fun resetCircuitBreaker(name: String) {
        circuitBreakers.remove(name)
    }

    fun resetAllCircuitBreakers() {
        circuitBreakers.clear()
    }
}