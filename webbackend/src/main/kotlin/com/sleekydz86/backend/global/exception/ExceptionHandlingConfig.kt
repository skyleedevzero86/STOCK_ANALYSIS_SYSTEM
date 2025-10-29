package com.sleekydz86.backend.global.exception

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.reactive.function.server.ServerResponse
import reactor.core.publisher.Mono
import java.time.Duration

@Configuration
class ExceptionHandlingConfig {

    @Bean
    fun errorHandlingStrategies(): Map<String, (Throwable) -> Mono<ServerResponse>> =
        mapOf(
            "timeout" to { error ->
                ServerResponse.status(504)
                    .bodyValue(ErrorResponse(
                        timestamp = java.time.LocalDateTime.now(),
                        status = 504,
                        error = "Gateway Timeout",
                        message = "Request timeout occurred",
                        path = ""
                    ))
            },
            "circuit_breaker" to { error ->
                ServerResponse.status(503)
                    .bodyValue(ErrorResponse(
                        timestamp = java.time.LocalDateTime.now(),
                        status = 503,
                        error = "Service Unavailable",
                        message = "Circuit breaker is open",
                        path = ""
                    ))
            },
            "validation" to { error ->
                ServerResponse.status(400)
                    .bodyValue(ErrorResponse(
                        timestamp = java.time.LocalDateTime.now(),
                        status = 400,
                        error = "Bad Request",
                        message = error.message ?: "Validation failed",
                        path = ""
                    ))
            },
            "external_api" to { error ->
                ServerResponse.status(502)
                    .bodyValue(ErrorResponse(
                        timestamp = java.time.LocalDateTime.now(),
                        status = 502,
                        error = "Bad Gateway",
                        message = "External service error",
                        path = ""
                    ))
            }
        )

    @Bean
    fun defaultTimeout(): Duration = Duration.ofSeconds(30)

    @Bean
    fun maxRetryAttempts(): Int = 3

    @Bean
    fun retryDelay(): Duration = Duration.ofSeconds(1)
}
