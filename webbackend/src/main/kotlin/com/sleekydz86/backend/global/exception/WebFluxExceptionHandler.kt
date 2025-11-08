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
import reactor.netty.channel.AbortedException

@Order(-2)
@Component
class WebFluxExceptionHandler(
    private val objectMapper: ObjectMapper
) : ErrorWebExceptionHandler {

    private val logger = LoggerFactory.getLogger(WebFluxExceptionHandler::class.java)

    override fun handle(exchange: ServerWebExchange, ex: Throwable): Mono<Void> {
        val response = exchange.response

        val path = try {
            exchange.request.path.toString().takeIf { it.isNotBlank() } ?: exchange.request.uri.path
        } catch (e: Exception) {
            logger.warn("요청에서 경로 추출 오류: ${e.message}")
            exchange.request.uri?.path ?: "unknown"
        }

        if (ex is AbortedException || ex.cause is AbortedException) {
            logger.debug("연결 중단됨: path=$path (정상 종료 중일 가능성)")
            return Mono.empty()
        }

        if (response.isCommitted) {
            logger.warn("응답이 이미 커밋됨: path=$path, 오류 응답을 보낼 수 없습니다")
            return Mono.empty()
        }

        val bufferFactory = response.bufferFactory()
        
        logger.error("전역 오류 핸들러가 예외를 처리함: path=$path", ex)
        logger.error("예외 타입: ${ex.javaClass.name}, 메시지: ${ex.message}", ex)
        if (ex.cause != null) {
            logger.error("예외 원인: ${ex.cause?.javaClass?.name}, 메시지: ${ex.cause?.message}", ex.cause)
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

        return try {
            response.statusCode = HttpStatus.valueOf(errorResponse.status)
            response.headers.contentType = MediaType.APPLICATION_JSON

            val errorResponseBody = objectMapper.writeValueAsBytes(errorResponse)
            val buffer = bufferFactory.wrap(errorResponseBody)
            response.writeWith(Mono.just(buffer))
                .onErrorResume { writeError ->
                    if (writeError is AbortedException || writeError.cause is AbortedException) {
                        logger.debug("오류 응답 작성 중 연결 중단됨: path=$path")
                        Mono.empty()
                    } else {
                        logger.error("오류 응답 작성 실패: path=$path", writeError)
                        Mono.empty()
                    }
                }
        } catch (e: Exception) {
            if (e is AbortedException || e.cause is AbortedException) {
                logger.debug("오류 처리 중 연결 중단됨: path=$path")
                Mono.empty()
            } else {
                logger.error("오류 응답 직렬화 실패: path=$path", e)
                Mono.empty()
            }
        }
    }
}

