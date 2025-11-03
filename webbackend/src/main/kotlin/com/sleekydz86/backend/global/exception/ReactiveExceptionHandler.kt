package com.sleekydz86.backend.global.exception

import org.springframework.web.reactive.function.server.ServerRequest
import org.springframework.web.reactive.function.server.ServerResponse
import reactor.core.publisher.Mono
import java.time.LocalDateTime

object ReactiveExceptionHandler {

    fun handleStockNotFound(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(404)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 404,
                error = "Stock Not Found",
                message = ex.message ?: "Stock not found",
                path = request.path()
            ))

    fun handleInvalidSymbol(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.badRequest()
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 400,
                error = "Invalid Symbol",
                message = ex.message ?: "Invalid stock symbol",
                path = request.path()
            ))

    fun handleExternalApiError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(503)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 503,
                error = "External API Error",
                message = ex.message ?: "External service unavailable",
                path = request.path()
            ))

    fun handleDataProcessingError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(500)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 500,
                error = "Data Processing Error",
                message = ex.message ?: "Error processing data",
                path = request.path()
            ))

    fun handleWebSocketError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(500)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 500,
                error = "WebSocket Error",
                message = ex.message ?: "WebSocket connection error",
                path = request.path()
            ))

    fun handleCircuitBreakerOpen(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(503)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 503,
                error = "Service Temporarily Unavailable",
                message = "Circuit breaker is open. Please try again later.",
                path = request.path()
            ))

    fun handleRateLimitExceeded(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(429)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 429,
                error = "Rate Limit Exceeded",
                message = "Too many requests. Please try again later.",
                path = request.path()
            ))

    fun handleAuthenticationError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(401)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 401,
                error = "Authentication Failed",
                message = ex.message ?: "Authentication required",
                path = request.path()
            ))

    fun handleAuthorizationError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(403)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 403,
                error = "Access Denied",
                message = ex.message ?: "Insufficient permissions",
                path = request.path()
            ))

    fun handleGenericError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(500)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 500,
                error = "Internal Server Error",
                message = "An unexpected error occurred",
                path = request.path()
            ))
}
