package com.sleekydz86.backend.global.exception

import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import reactor.util.retry.Retry
import java.time.Duration

object RetryHandler {

    fun <T> withRetry(
        operation: () -> Mono<T>,
        maxAttempts: Long = 3,
        delay: Duration = Duration.ofSeconds(1)
    ): Mono<T> =
        operation()
            .retryWhen(
                Retry.fixedDelay(maxAttempts, delay)
                    .filter { error ->
                        when (error) {
                            is ExternalApiException -> true
                            is java.util.concurrent.TimeoutException -> true
                            is java.net.ConnectException -> true
                            is java.net.SocketTimeoutException -> true
                            else -> false
                        }
                    }
            )

    fun <T> withRetryFlux(
        operation: () -> Flux<T>,
        maxAttempts: Long = 3,
        delay: Duration = Duration.ofSeconds(1)
    ): Flux<T> =
        operation()
            .retryWhen(
                Retry.fixedDelay(maxAttempts, delay)
                    .filter { error ->
                        when (error) {
                            is ExternalApiException -> true
                            is java.util.concurrent.TimeoutException -> true
                            is java.net.ConnectException -> true
                            is java.net.SocketTimeoutException -> true
                            else -> false
                        }
                    }
            )

    fun <T> withExponentialBackoff(
        operation: () -> Mono<T>,
        maxAttempts: Long = 3,
        initialDelay: Duration = Duration.ofSeconds(1)
    ): Mono<T> =
        operation()
            .retryWhen(
                Retry.backoff(maxAttempts, initialDelay)
                    .filter { error ->
                        when (error) {
                            is ExternalApiException -> true
                            is java.util.concurrent.TimeoutException -> true
                            is java.net.ConnectException -> true
                            is java.net.SocketTimeoutException -> true
                            else -> false
                        }
                    }
            )

    fun <T> withExponentialBackoffFlux(
        operation: () -> Flux<T>,
        maxAttempts: Long = 3,
        initialDelay: Duration = Duration.ofSeconds(1)
    ): Flux<T> =
        operation()
            .retryWhen(
                Retry.backoff(maxAttempts, initialDelay)
                    .filter { error ->
                        when (error) {
                            is ExternalApiException -> true
                            is java.util.concurrent.TimeoutException -> true
                            is java.net.ConnectException -> true
                            is java.net.SocketTimeoutException -> true
                            else -> false
                        }
                    }
            )
}
