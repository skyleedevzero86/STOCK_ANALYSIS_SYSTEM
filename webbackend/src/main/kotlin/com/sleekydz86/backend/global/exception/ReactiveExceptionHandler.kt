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
                error = "종목을 찾을 수 없음",
                message = ex.message ?: "요청하신 종목을 찾을 수 없습니다",
                path = request.path()
            ))

    fun handleInvalidSymbol(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.badRequest()
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 400,
                error = "잘못된 종목 코드",
                message = ex.message ?: "유효하지 않은 종목 코드입니다",
                path = request.path()
            ))

    fun handleExternalApiError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(503)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 503,
                error = "외부 API 오류",
                message = ex.message ?: "외부 서비스를 사용할 수 없습니다",
                path = request.path()
            ))

    fun handleDataProcessingError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(500)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 500,
                error = "데이터 처리 오류",
                message = ex.message ?: "데이터 처리 중 오류가 발생했습니다",
                path = request.path()
            ))

    fun handleWebSocketError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(500)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 500,
                error = "WebSocket 오류",
                message = ex.message ?: "WebSocket 연결 오류가 발생했습니다",
                path = request.path()
            ))

    fun handleCircuitBreakerOpen(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(503)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 503,
                error = "서비스 일시 중단",
                message = "서비스가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요",
                path = request.path()
            ))

    fun handleRateLimitExceeded(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(429)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 429,
                error = "요청 한도 초과",
                message = "요청이 너무 많습니다. 잠시 후 다시 시도해주세요",
                path = request.path()
            ))

    fun handleAuthenticationError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(401)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 401,
                error = "인증 실패",
                message = ex.message ?: "인증이 필요합니다",
                path = request.path()
            ))

    fun handleAuthorizationError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(403)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 403,
                error = "접근 거부",
                message = ex.message ?: "권한이 부족합니다",
                path = request.path()
            ))

    fun handleGenericError(request: ServerRequest, ex: Throwable): Mono<ServerResponse> =
        ServerResponse.status(500)
            .bodyValue(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = 500,
                error = "서버 내부 오류",
                message = ex.message ?: ex.javaClass.simpleName ?: "예상치 못한 오류가 발생했습니다",
                path = request.path()
            ))
}
