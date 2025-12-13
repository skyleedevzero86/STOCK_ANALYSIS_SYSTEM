package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.domain.service.AdminService
import com.sleekydz86.backend.domain.service.AIEmailService
import org.slf4j.LoggerFactory
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono

@RestController
@RequestMapping("/api/ai-email")
class AIEmailController(
    private val aiEmailService: AIEmailService,
    private val adminService: AdminService
) {
    private val logger = LoggerFactory.getLogger(AIEmailController::class.java)

    @PostMapping("/send/{templateId}/{symbol}")
    fun sendAIEmailToSubscribers(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable templateId: Long,
        @PathVariable symbol: String
    ): Mono<ResponseEntity<Map<String, Any>>> {
        val token = extractToken(authHeader)
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    aiEmailService.sendAIEmailToSubscribers(templateId, symbol)
                        .map { result ->
                            logger.info("AI 이메일 발송 성공: templateId={}, symbol={}", templateId, symbol)
                            ResponseEntity.ok(result) as ResponseEntity<Map<String, Any>>
                        }
                        .onErrorResume { error ->
                            logger.error("AI 이메일 발송 중 오류 발생: templateId={}, symbol={}, error={}", 
                                templateId, symbol, error.message, error)
                            val errorMessage = error.message ?: "AI 이메일 발송 중 오류가 발생했습니다."
                            Mono.just(
                                ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                                    .body(mapOf("message" to errorMessage, "error" to error.javaClass.simpleName)) as ResponseEntity<Map<String, Any>>
                            )
                        }
                } else {
                    Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(mapOf("message" to "인증이 필요합니다.")) as ResponseEntity<Map<String, Any>>)
                }
            }
            .onErrorResume { error ->
                logger.error("AI 이메일 발송 요청 처리 중 오류: templateId={}, symbol={}, error={}", 
                    templateId, symbol, error.message, error)
                Mono.just(
                    ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body(mapOf("message" to (error.message ?: "서버 오류가 발생했습니다."), "error" to error.javaClass.simpleName)) as ResponseEntity<Map<String, Any>>
                )
            }
    }

    @PostMapping("/send-bulk/{templateId}")
    fun sendBulkAIEmails(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable templateId: Long,
        @RequestBody symbols: List<String>
    ): Mono<ResponseEntity<Map<String, Any>>> {
        val token = extractToken(authHeader)
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    aiEmailService.sendBulkAIEmails(templateId, symbols)
                        .map { result ->
                            logger.info("대량 AI 이메일 발송 성공: templateId={}, symbols={}", templateId, symbols)
                            ResponseEntity.ok(result) as ResponseEntity<Map<String, Any>>
                        }
                        .onErrorResume { error ->
                            logger.error("대량 AI 이메일 발송 중 오류 발생: templateId={}, symbols={}, error={}", 
                                templateId, symbols, error.message, error)
                            val errorMessage = error.message ?: "대량 AI 이메일 발송 중 오류가 발생했습니다."
                            Mono.just(
                                ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                                    .body(mapOf("message" to errorMessage, "error" to error.javaClass.simpleName)) as ResponseEntity<Map<String, Any>>
                            )
                        }
                } else {
                    Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(mapOf("message" to "인증이 필요합니다.")) as ResponseEntity<Map<String, Any>>)
                }
            }
            .onErrorResume { error ->
                logger.error("대량 AI 이메일 발송 요청 처리 중 오류: templateId={}, symbols={}, error={}", 
                    templateId, symbols, error.message, error)
                Mono.just(
                    ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body(mapOf("message" to (error.message ?: "서버 오류가 발생했습니다."), "error" to error.javaClass.simpleName)) as ResponseEntity<Map<String, Any>>
                )
            }
    }

    private fun extractToken(authHeader: String): String {
        return if (authHeader.startsWith("Bearer ")) {
            authHeader.substring(7)
        } else {
            authHeader
        }
    }
}
