package com.sleekydz86.backend.global.exception

import org.springframework.stereotype.Service
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.LocalDateTime
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicLong

@Service
class ErrorMonitoringService {

    private val errorCounts = ConcurrentHashMap<String, AtomicLong>()
    private val errorHistory = ConcurrentHashMap<String, MutableList<ErrorEvent>>()

    fun recordError(errorType: String, message: String, cause: Throwable? = null) {
        errorCounts.computeIfAbsent(errorType) { AtomicLong(0) }.incrementAndGet()

        val errorEvent = ErrorEvent(
            timestamp = LocalDateTime.now(),
            errorType = errorType,
            message = message,
            cause = cause?.javaClass?.simpleName,
            stackTrace = cause?.stackTrace?.take(5)?.joinToString("\n")
        )

        errorHistory.computeIfAbsent(errorType) { mutableListOf() }.add(errorEvent)

        if (errorHistory[errorType]!!.size > 100) {
            errorHistory[errorType]!!.removeAt(0)
        }
    }

    fun getErrorStats(): Map<String, Any> =
        mapOf(
            "totalErrors" to errorCounts.values.sumOf { it.get() },
            "errorCounts" to errorCounts.mapValues { it.value.get() },
            "recentErrors" to errorHistory.mapValues { (_, events) ->
                events.takeLast(10).map { event ->
                    mapOf(
                        "timestamp" to event.timestamp,
                        "message" to event.message,
                        "cause" to event.cause
                    )
                }
            }
        )

    fun <T> monitorOperation(
        operationName: String,
        operation: () -> Mono<T>
    ): Mono<T> =
        operation()
            .doOnError { error ->
                recordError(
                    errorType = error.javaClass.simpleName,
                    message = "Error in $operationName: ${error.message}",
                    cause = error
                )
            }

    fun <T> monitorFluxOperation(
        operationName: String,
        operation: () -> Flux<T>
    ): Flux<T> =
        operation()
            .doOnError { error ->
                recordError(
                    errorType = error.javaClass.simpleName,
                    message = "Error in $operationName: ${error.message}",
                    cause = error
                )
            }

    fun clearErrorHistory() {
        errorCounts.clear()
        errorHistory.clear()
    }
}

data class ErrorEvent(
    val timestamp: LocalDateTime,
    val errorType: String,
    val message: String,
    val cause: String?,
    val stackTrace: String?
)
