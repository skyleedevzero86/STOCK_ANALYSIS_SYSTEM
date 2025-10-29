package com.sleekydz86.backend.domain.functional

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration

object FunctionalUtils {

    fun <T> Flux<T>.withErrorHandling(
        onError: (Throwable) -> Mono<T> = { Mono.error(it) }
    ): Flux<T> = this.onErrorResume(onError)

    fun <T> Mono<T>.withErrorHandling(
        onError: (Throwable) -> Mono<T> = { Mono.error(it) }
    ): Mono<T> = this.onErrorResume(onError)

    fun <T> Flux<T>.withRetry(
        maxAttempts: Long = 3,
        delay: Duration = Duration.ofSeconds(1)
    ): Flux<T> = this.retryWhen { errors ->
        errors.take(maxAttempts)
            .delayElements(delay)
    }

    fun <T> Mono<T>.withRetry(
        maxAttempts: Long = 3,
        delay: Duration = Duration.ofSeconds(1)
    ): Mono<T> = this.retryWhen { errors ->
        errors.take(maxAttempts)
            .delayElements(delay)
    }

    fun <T> Flux<T>.withTimeout(
        timeout: Duration = Duration.ofSeconds(30)
    ): Flux<T> = this.timeout(timeout)

    fun <T> Mono<T>.withTimeout(
        timeout: Duration = Duration.ofSeconds(30)
    ): Mono<T> = this.timeout(timeout)

    fun <T> Flux<T>.withLogging(
        logPrefix: String = ""
    ): Flux<T> = this.doOnNext {
        println("$logPrefix: $it")
    }.doOnError {
        println("$logPrefix Error: ${it.message}")
    }

    fun <T> Mono<T>.withLogging(
        logPrefix: String = ""
    ): Mono<T> = this.doOnNext {
        println("$logPrefix: $it")
    }.doOnError {
        println("$logPrefix Error: ${it.message}")
    }
}