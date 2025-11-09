package com.sleekydz86.backend.global.exception

import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.RestControllerAdvice
import java.time.LocalDateTime

@RestControllerAdvice
class GlobalExceptionHandler {

    @ExceptionHandler(StockNotFoundException::class)
    fun handleStockNotFound(ex: StockNotFoundException): ResponseEntity<ErrorResponse> {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = HttpStatus.NOT_FOUND.value(),
                error = "종목을 찾을 수 없음",
                message = ex.message ?: "요청하신 종목을 찾을 수 없습니다",
                path = ""
            ))
    }

    @ExceptionHandler(InvalidSymbolException::class)
    fun handleInvalidSymbol(ex: InvalidSymbolException): ResponseEntity<ErrorResponse> {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
            .body(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = HttpStatus.BAD_REQUEST.value(),
                error = "잘못된 종목 코드",
                message = ex.message ?: "유효하지 않은 종목 코드입니다",
                path = ""
            ))
    }

    @ExceptionHandler(ExternalApiException::class)
    fun handleExternalApiError(ex: ExternalApiException): ResponseEntity<ErrorResponse> {
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
            .body(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = HttpStatus.SERVICE_UNAVAILABLE.value(),
                error = "외부 API 오류",
                message = ex.message ?: "외부 서비스를 사용할 수 없습니다",
                path = ""
            ))
    }

    @ExceptionHandler(DataProcessingException::class)
    fun handleDataProcessingError(ex: DataProcessingException): ResponseEntity<ErrorResponse> {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = HttpStatus.INTERNAL_SERVER_ERROR.value(),
                error = "데이터 처리 오류",
                message = ex.message ?: "데이터 처리 중 오류가 발생했습니다",
                path = ""
            ))
    }

    @ExceptionHandler(WebSocketException::class)
    fun handleWebSocketError(ex: WebSocketException): ResponseEntity<ErrorResponse> {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = HttpStatus.INTERNAL_SERVER_ERROR.value(),
                error = "WebSocket 오류",
                message = ex.message ?: "WebSocket 연결 오류가 발생했습니다",
                path = ""
            ))
    }

    @ExceptionHandler(Exception::class)
    fun handleGenericException(ex: Exception): ResponseEntity<ErrorResponse> {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = HttpStatus.INTERNAL_SERVER_ERROR.value(),
                error = "서버 내부 오류",
                message = "예상치 못한 오류가 발생했습니다",
                path = ""
            ))
    }
}
