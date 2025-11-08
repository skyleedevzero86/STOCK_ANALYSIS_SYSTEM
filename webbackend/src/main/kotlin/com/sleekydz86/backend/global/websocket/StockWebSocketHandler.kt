package com.sleekydz86.backend.global.websocket

import com.fasterxml.jackson.databind.ObjectMapper
import com.sleekydz86.backend.domain.model.TechnicalAnalysis
import com.sleekydz86.backend.domain.service.StockAnalysisService
import com.sleekydz86.backend.global.exception.WebSocketException
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Component
import org.springframework.web.reactive.socket.WebSocketHandler
import org.springframework.web.reactive.socket.WebSocketMessage
import org.springframework.web.reactive.socket.WebSocketSession
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration

@Component
class StockWebSocketHandler(
    private val stockAnalysisService: StockAnalysisService,
    private val objectMapper: ObjectMapper
) : WebSocketHandler {
    
    private val logger = LoggerFactory.getLogger(StockWebSocketHandler::class.java)

    override fun handle(session: WebSocketSession): Mono<Void> {
        logger.info("WebSocket 연결 시도: session=${session.id}")
        
        return Mono.defer {
            logger.debug("WebSocket 핸들러 시작: session=${session.id}")

            val welcomeMessage = createWelcomeMessage()

            val analysisStreamJson: Flux<String> = try {
                stockAnalysisService.getRealtimeAnalysisStream()
                    .map { analysis ->
                        try {
                            analysis.toJsonMessage()
                        } catch (e: Exception) {
                            logger.error("분석 데이터 직렬화 실패: session=${session.id}", e)
                            createErrorMessage("Serialization error: ${e.message ?: "Unknown error"}")
                        }
                    }
                    .onErrorResume { error ->
                        logger.error("주식 분석 스트림 오류: session=${session.id}", error)

                        Flux.interval(Duration.ofSeconds(5))
                            .map { createErrorMessage("Analysis stream error: ${error.message ?: error.javaClass.simpleName}") }
                    }
            } catch (e: Exception) {
                logger.error("분석 스트림 생성 실패: session=${session.id}", e)

                Flux.interval(Duration.ofSeconds(10))
                    .map { createErrorMessage("Analysis service unavailable: ${e.message ?: e.javaClass.simpleName}") }
            }

            val messageStream = Flux.concat(
                Flux.just(welcomeMessage),
                analysisStreamJson
            )
            .map { json -> session.textMessage(json) }
            .doOnError { error ->
                logger.error("WebSocket 메시지 스트림 오류: session=${session.id}", error)
            }
            
            session.send(messageStream)
                .doOnSubscribe { 
                    logger.info("WebSocket 세션 시작됨: session=${session.id}")
                }
                .doOnSuccess {
                    logger.debug("WebSocket 세션 성공적으로 설정됨: session=${session.id}")
                }
                .doOnError { error ->
                    logger.error("WebSocket 전송 오류: session=${session.id}", error)
                }
                .doOnTerminate {
                    logger.info("WebSocket 세션 종료됨: session=${session.id}")
                }
                .timeout(Duration.ofMinutes(30))
                .onErrorResume { error ->
                    logger.warn("WebSocket 타임아웃: session=${session.id}", error)

                    Mono.empty()
                }
        }
        .onErrorResume { error ->
            logger.error("WebSocket 핸들러 오류: session=${session.id}", error)

            try {
                val errorMessage = createErrorMessage("WebSocket handler error: ${error.message ?: error.javaClass.simpleName}")
                session.send(Mono.just(session.textMessage(errorMessage)))
                    .timeout(Duration.ofSeconds(5))
                    .onErrorResume {
                        Mono.empty()
                    }
            } catch (e: Exception) {
                logger.error("오류 메시지 전송 실패: session=${session.id}", e)
                Mono.empty()
            }
        }
    }
    
    private fun createErrorMessage(message: String): String {
        return try {
            objectMapper.writeValueAsString(
                mapOf(
                    "type" to "error",
                    "message" to message,
                    "timestamp" to System.currentTimeMillis()
                )
            )
        } catch (e: Exception) {
            logger.error("오류 메시지 JSON 생성 실패", e)
            """{"type":"error","message":"$message","timestamp":${System.currentTimeMillis()}}"""
        }
    }
    
    private fun createWelcomeMessage(): String {
        return try {
            objectMapper.writeValueAsString(
                mapOf(
                    "type" to "welcome",
                    "message" to "WebSocket connection established",
                    "timestamp" to System.currentTimeMillis()
                )
            )
        } catch (e: Exception) {
            logger.error("환영 메시지 JSON 생성 실패", e)
            """{"type":"welcome","message":"WebSocket connected","timestamp":${System.currentTimeMillis()}}"""
        }
    }

    private fun TechnicalAnalysis.toJsonMessage(): String =
        try {
            objectMapper.writeValueAsString(this)
        } catch (e: Exception) {
            throw WebSocketException("JSON serialization failed", e)
        }

    private fun handleWebSocketError(session: WebSocketSession, error: Throwable): Mono<Void> {
        return try {
            val errorMessage = when (error) {
                is WebSocketException -> error.message ?: "WebSocket error occurred"
                is IllegalStateException -> "WebSocket session is not active"
                is java.util.concurrent.TimeoutException -> "WebSocket connection timeout"
                else -> "Internal WebSocket error"
            }

            val errorJson = objectMapper.writeValueAsString(
                mapOf(
                    "type" to "error",
                    "message" to errorMessage,
                    "timestamp" to System.currentTimeMillis()
                )
            )

            session.send(Mono.just(session.textMessage(errorJson)))
                .onErrorResume {
                    Mono.empty()
                }
        } catch (e: Exception) {
            Mono.empty()
        }
    }
}
