package com.sleekydz86.backend.global.websocket

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

    override fun handle(session: WebSocketSession): Mono<Void> =
        stockAnalysisService.getRealtimeAnalysisStream()
            .onErrorResume { error ->
                handleWebSocketError(session, error)
                Flux.empty()
            }
            .map { analysis ->
                try {
                    analysis.toJsonMessage()
                } catch (e: Exception) {
                    throw WebSocketException("Failed to serialize analysis data", e)
                }
            }
            .map { json -> session.textMessage(json) }
            .let { messages ->
                session.send(messages)
                    .onErrorResume { error ->
                        handleWebSocketError(session, error)
                        Mono.empty()
                    }
            }
            .timeout(Duration.ofMinutes(30))
            .onErrorResume { error ->
                handleWebSocketError(session, error)
                Mono.empty()
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
