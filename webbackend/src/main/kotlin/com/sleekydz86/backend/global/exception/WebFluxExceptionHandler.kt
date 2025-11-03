package com.sleekydz86.backend.global.exception

import org.springframework.boot.web.reactive.error.ErrorWebExceptionHandler
import org.springframework.core.annotation.Order
import org.springframework.core.io.buffer.DataBufferFactory
import org.springframework.http.HttpStatus
import org.springframework.http.MediaType
import org.springframework.stereotype.Component
import org.springframework.web.server.ServerWebExchange
import org.springframework.web.server.ResponseStatusException
import reactor.core.publisher.Mono
import com.fasterxml.jackson.databind.ObjectMapper
import org.slf4j.LoggerFactory
import java.time.LocalDateTime

@Order(-2)
@Component
class WebFluxExceptionHandler(
    private val objectMapper: ObjectMapper
) : ErrorWebExceptionHandler {

    private val logger = LoggerFactory.getLogger(WebFluxExceptionHandler::class.java)

    override fun handle(exchange: ServerWebExchange, ex: Throwable): Mono<Void> {
        val response = exchange.response
        val bufferFactory = response.bufferFactory()

        val path = try {
            exchange.request.path.toString().takeIf { it.isNotBlank() } ?: exchange.request.uri.path
        } catch (e: Exception) {
            logger.warn("Error extracting path from request: ${e.message}")
            exchange.request.uri?.path ?: "unknown"
        }
        
        logger.error("Global error handler caught exception for path: $path", ex)
        logger.error("Exception type: ${ex.javaClass.name}, message: ${ex.message}", ex)
        if (ex.cause != null) {
            logger.error("Exception cause: ${ex.cause?.javaClass?.name}, message: ${ex.cause?.message}", ex.cause)
        }

        val errorResponse = when (ex) {
            is ResponseStatusException -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = ex.statusCode.value(),
                    error = ex.statusCode.toString(),
                    message = ex.reason ?: ex.message ?: "Error occurred",
                    path = path
                )
            }
            is ExternalApiException -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = 503,
                    error = "External API Error",
                    message = ex.message ?: "External service unavailable",
                    path = path
                )
            }
            is DataProcessingException -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = 500,
                    error = "Data Processing Error",
                    message = ex.message ?: "Error processing data",
                    path = path
                )
            }
            is InvalidSymbolException -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = 400,
                    error = "Invalid Symbol",
                    message = ex.message ?: "Invalid stock symbol",
                    path = path
                )
            }
            is StockNotFoundException -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = 404,
                    error = "Stock Not Found",
                    message = ex.message ?: "Stock not found",
                    path = path
                )
            }
            else -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = 500,
                    error = "Internal Server Error",
                    message = ex.message ?: ex.javaClass.simpleName ?: "An unexpected error occurred",
                    path = path
                )
            }
        }

        response.statusCode = HttpStatus.valueOf(errorResponse.status)
        response.headers.contentType = MediaType.APPLICATION_JSON

        return try {
            val errorResponseBody = objectMapper.writeValueAsBytes(errorResponse)
            val buffer = bufferFactory.wrap(errorResponseBody)
            response.writeWith(Mono.just(buffer))
        } catch (e: Exception) {
            logger.error("Error serializing error response", e)
            response.writeWith(Mono.empty())
        }
    }
}

