package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.domain.service.AIEmailService
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono

@RestController
@RequestMapping("/api/ai-email")
class AIEmailController(
    private val aiEmailService: AIEmailService
) {

    @PostMapping("/send/{templateId}/{symbol}")
    fun sendAIEmailToSubscribers(
        @PathVariable templateId: Long,
        @PathVariable symbol: String
    ): Mono<ResponseEntity<Map<String, Any>>> {
        return aiEmailService.sendAIEmailToSubscribers(templateId, symbol)
            .map { ResponseEntity.ok(it) }
    }

    @PostMapping("/send-bulk/{templateId}")
    fun sendBulkAIEmails(
        @PathVariable templateId: Long,
        @RequestBody symbols: List<String>
    ): Mono<ResponseEntity<Map<String, Any>>> {
        return aiEmailService.sendBulkAIEmails(templateId, symbols)
            .map { ResponseEntity.ok(it) }
    }
}
