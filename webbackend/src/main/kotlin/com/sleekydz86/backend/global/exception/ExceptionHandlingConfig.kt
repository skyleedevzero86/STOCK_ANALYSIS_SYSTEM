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
                        error = "게이트웨이 타임아웃",
                        message = "요청 시간이 초과되었습니다",
                        path = ""
                    ))
            },
            "circuit_breaker" to { error ->
                ServerResponse.status(503)
                    .bodyValue(ErrorResponse(
                        timestamp = java.time.LocalDateTime.now(),
                        status = 503,
                        error = "서비스 일시 중단",
                        message = "서비스가 일시적으로 사용할 수 없습니다",
                        path = ""
                    ))
            },
            "validation" to { error ->
                ServerResponse.status(400)
                    .bodyValue(ErrorResponse(
                        timestamp = java.time.LocalDateTime.now(),
                        status = 400,
                        error = "잘못된 요청",
                        message = error.message ?: "입력값 검증에 실패했습니다",
                        path = ""
                    ))
            },
            "external_api" to { error ->
                ServerResponse.status(502)
                    .bodyValue(ErrorResponse(
                        timestamp = java.time.LocalDateTime.now(),
                        status = 502,
                        error = "게이트웨이 오류",
                        message = "외부 서비스 오류가 발생했습니다",
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
