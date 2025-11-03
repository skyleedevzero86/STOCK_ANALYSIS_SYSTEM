package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.domain.model.EmailTemplate
import com.sleekydz86.backend.domain.model.TemplateRequest
import com.sleekydz86.backend.domain.service.EmailTemplateService
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono

@RestController
@RequestMapping("/api/templates")
class EmailTemplateController(
    private val emailTemplateService: EmailTemplateService
) {

    @PostMapping
    fun createTemplate(@RequestBody request: TemplateRequest): Mono<ResponseEntity<EmailTemplate>> {
        return emailTemplateService.createTemplate(request)
            .map { ResponseEntity.status(HttpStatus.CREATED).body(it) }
    }

    @GetMapping
    fun getAllTemplates(): Mono<List<EmailTemplate>> {
        return emailTemplateService.getAllTemplates()
    }

    @GetMapping("/{id}")
    fun getTemplateById(@PathVariable id: Long): Mono<ResponseEntity<EmailTemplate>> {
        return emailTemplateService.getTemplateById(id)
            .map { ResponseEntity.ok(it) }
            .onErrorResume(IllegalArgumentException::class.java) {
                Mono.just(ResponseEntity.notFound().build())
            }
    }

    @PutMapping("/{id}")
    fun updateTemplate(
        @PathVariable id: Long,
        @RequestBody request: TemplateRequest
    ): Mono<ResponseEntity<EmailTemplate>> {
        return emailTemplateService.updateTemplate(id, request)
            .map { ResponseEntity.ok(it) }
            .onErrorResume(IllegalArgumentException::class.java) {
                Mono.just(ResponseEntity.notFound().build())
            }
    }

    @DeleteMapping("/{id}")
    fun deleteTemplate(@PathVariable id: Long): Mono<ResponseEntity<Void>> {
        return emailTemplateService.deleteTemplate(id)
            .map { ResponseEntity.noContent().build<Void>() }
            .onErrorResume(IllegalArgumentException::class.java) {
                Mono.just(ResponseEntity.notFound().build())
            }
    }
}