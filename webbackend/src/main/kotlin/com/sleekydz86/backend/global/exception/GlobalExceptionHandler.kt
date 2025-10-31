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
                error = "Stock Not Found",
                message = ex.message ?: "Stock not found",
                path = ""
            ))
    }

    @ExceptionHandler(InvalidSymbolException::class)
    fun handleInvalidSymbol(ex: InvalidSymbolException): ResponseEntity<ErrorResponse> {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
            .body(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = HttpStatus.BAD_REQUEST.value(),
                error = "Invalid Symbol",
                message = ex.message ?: "Invalid stock symbol",
                path = ""
            ))
    }

    @ExceptionHandler(ExternalApiException::class)
    fun handleExternalApiError(ex: ExternalApiException): ResponseEntity<ErrorResponse> {
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
            .body(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = HttpStatus.SERVICE_UNAVAILABLE.value(),
                error = "External API Error",
                message = ex.message ?: "External service unavailable",
                path = ""
            ))
    }

    @ExceptionHandler(DataProcessingException::class)
    fun handleDataProcessingError(ex: DataProcessingException): ResponseEntity<ErrorResponse> {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = HttpStatus.INTERNAL_SERVER_ERROR.value(),
                error = "Data Processing Error",
                message = ex.message ?: "Error processing data",
                path = ""
            ))
    }

    @ExceptionHandler(WebSocketException::class)
    fun handleWebSocketError(ex: WebSocketException): ResponseEntity<ErrorResponse> {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = HttpStatus.INTERNAL_SERVER_ERROR.value(),
                error = "WebSocket Error",
                message = ex.message ?: "WebSocket connection error",
                path = ""
            ))
    }

    @ExceptionHandler(Exception::class)
    fun handleGenericException(ex: Exception): ResponseEntity<ErrorResponse> {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(ErrorResponse(
                timestamp = LocalDateTime.now(),
                status = HttpStatus.INTERNAL_SERVER_ERROR.value(),
                error = "Internal Server Error",
                message = "An unexpected error occurred",
                path = ""
            ))
    }
}
