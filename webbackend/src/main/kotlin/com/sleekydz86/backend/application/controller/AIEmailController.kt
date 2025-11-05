package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.domain.service.AdminService
import com.sleekydz86.backend.domain.service.AIEmailService
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

    @PostMapping("/send/{templateId}/{symbol}")
    fun sendAIEmailToSubscribers(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable templateId: Long,
        @PathVariable symbol: String
    ): Mono<ResponseEntity<Any>> {
        val token = extractToken(authHeader)
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    aiEmailService.sendAIEmailToSubscribers(templateId, symbol)
                        .map { ResponseEntity.ok(it) }
                } else {
                    Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(mapOf("message" to "인증이 필요합니다.")))
                }
            }
    }

    @PostMapping("/send-bulk/{templateId}")
    fun sendBulkAIEmails(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable templateId: Long,
        @RequestBody symbols: List<String>
    ): Mono<ResponseEntity<Any>> {
        val token = extractToken(authHeader)
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    aiEmailService.sendBulkAIEmails(templateId, symbols)
                        .map { ResponseEntity.ok(it) }
                } else {
                    Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(mapOf("message" to "인증이 필요합니다.")))
                }
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
