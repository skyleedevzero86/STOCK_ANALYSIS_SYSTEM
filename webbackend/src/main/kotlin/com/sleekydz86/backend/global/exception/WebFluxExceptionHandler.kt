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
import java.time.LocalDateTime
import reactor.netty.channel.AbortedException

@Order(-2)
@Component
class WebFluxExceptionHandler(
    private val objectMapper: ObjectMapper
) : ErrorWebExceptionHandler {

    override fun handle(exchange: ServerWebExchange, ex: Throwable): Mono<Void> {
        val response = exchange.response

        val path = try {
            exchange.request.path.toString().takeIf { it.isNotBlank() } ?: exchange.request.uri.path
        } catch (e: Exception) {
            exchange.request.uri?.path ?: "알 수 없음"
        }

        if (ex is AbortedException || ex.cause is AbortedException) {
            return Mono.empty()
        }

        if (response.isCommitted) {
            return Mono.empty()
        }

        val bufferFactory = response.bufferFactory()

        val errorResponse = when (ex) {
            is ResponseStatusException -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = ex.statusCode.value(),
                    error = ex.statusCode.toString(),
                    message = ex.reason ?: ex.message ?: "오류가 발생했습니다",
                    path = path
                )
            }
            is ExternalApiException -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = 503,
                    error = "외부 API 오류",
                    message = ex.message ?: "외부 서비스를 사용할 수 없습니다",
                    path = path
                )
            }
            is DataProcessingException -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = 500,
                    error = "데이터 처리 오류",
                    message = ex.message ?: "데이터 처리 중 오류가 발생했습니다",
                    path = path
                )
            }
            is InvalidSymbolException -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = 400,
                    error = "잘못된 심볼",
                    message = ex.message ?: "유효하지 않은 주식 심볼입니다",
                    path = path
                )
            }
            is StockNotFoundException -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = 404,
                    error = "주식을 찾을 수 없음",
                    message = ex.message ?: "주식을 찾을 수 없습니다",
                    path = path
                )
            }
            else -> {
                ErrorResponse(
                    timestamp = LocalDateTime.now(),
                    status = 500,
                    error = "내부 서버 오류",
                    message = ex.message ?: ex.javaClass.simpleName ?: "예상치 못한 오류가 발생했습니다",
                    path = path
                )
            }
        }

        return try {
            response.statusCode = HttpStatus.valueOf(errorResponse.status)
            response.headers.contentType = MediaType.APPLICATION_JSON

            val errorResponseBody = objectMapper.writeValueAsBytes(errorResponse)
            val buffer = bufferFactory.wrap(errorResponseBody)
            response.writeWith(Mono.just(buffer))
                .onErrorResume { writeError ->
                    if (writeError is AbortedException || writeError.cause is AbortedException) {
                        Mono.empty()
                    } else {
                        Mono.empty()
                    }
                }
        } catch (e: Exception) {
            if (e is AbortedException || e.cause is AbortedException) {
                Mono.empty()
            } else {
                Mono.empty()
            }
        }
    }
}

