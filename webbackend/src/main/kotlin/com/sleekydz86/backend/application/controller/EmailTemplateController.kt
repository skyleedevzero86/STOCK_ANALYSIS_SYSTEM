package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.domain.model.EmailTemplate
import com.sleekydz86.backend.domain.model.TemplateRequest
import com.sleekydz86.backend.domain.service.AdminService
import com.sleekydz86.backend.domain.service.EmailTemplateService
import com.sleekydz86.backend.domain.service.NotificationLogService
import com.sleekydz86.backend.application.dto.ApiResponse
import com.sleekydz86.backend.application.dto.ApiResponseBuilder
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono

@RestController
@RequestMapping("/api/templates")
class EmailTemplateController(
    private val emailTemplateService: EmailTemplateService,
    private val adminService: AdminService,
    private val notificationLogService: NotificationLogService
) {

    @PostMapping
    fun createTemplate(
        @RequestHeader("Authorization") authHeader: String,
        @RequestBody request: TemplateRequest
    ): Mono<ResponseEntity<Any>> {
        val token = extractToken(authHeader)
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailTemplateService.createTemplate(request)
                        .map { ResponseEntity.status(HttpStatus.CREATED).body(it) }
                } else {
                    Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(mapOf("message" to "인증이 필요합니다.")))
                }
            }
    }

    @GetMapping
    fun getAllTemplates(
        @RequestHeader(value = "Authorization", required = false) authHeader: String?,
        @RequestParam(defaultValue = "0") page: Int,
        @RequestParam(defaultValue = "10") size: Int,
        @RequestParam(required = false) keyword: String?
    ): Mono<ResponseEntity<Any>> {
        if (authHeader == null) {
            return Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(mapOf("message" to "인증이 필요합니다.")))
        }
        val token = extractToken(authHeader)
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailTemplateService.getTemplates(page, size, keyword)
                        .map { ResponseEntity.ok(it) }
                } else {
                    Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(mapOf("message" to "인증이 필요합니다.")))
                }
            }
    }

    @GetMapping("/{id}")
    fun getTemplateById(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long
    ): Mono<ResponseEntity<Any>> {
        val token = extractToken(authHeader)
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailTemplateService.getTemplateById(id)
                        .map { template: EmailTemplate -> ResponseEntity.ok(template) as ResponseEntity<Any> }
                        .onErrorResume(IllegalArgumentException::class.java) {
                            Mono.just(ResponseEntity.notFound().build<Any>())
                        }
                } else {
                    Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(mapOf("message" to "인증이 필요합니다.")))
                }
            }
    }

    @PutMapping("/{id}")
    fun updateTemplate(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long,
        @RequestBody request: TemplateRequest
    ): Mono<ResponseEntity<Any>> {
        val token = extractToken(authHeader)
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailTemplateService.updateTemplate(id, request)
                        .map { template: EmailTemplate -> ResponseEntity.ok(template) as ResponseEntity<Any> }
                        .onErrorResume(IllegalArgumentException::class.java) {
                            Mono.just(ResponseEntity.notFound().build<Any>())
                        }
                } else {
                    Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(mapOf("message" to "인증이 필요합니다.")))
                }
            }
    }

    @DeleteMapping("/{id}")
    fun deleteTemplate(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long
    ): Mono<ResponseEntity<Any>> {
        val token = extractToken(authHeader)
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailTemplateService.deleteTemplate(id)
                        .map { ResponseEntity.noContent().build<Any>() }
                        .onErrorResume(IllegalArgumentException::class.java) {
                            Mono.just(ResponseEntity.notFound().build<Any>())
                        }
                } else {
                    Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(mapOf("message" to "인증이 필요합니다.")))
                }
            }
    }

    @GetMapping("/{id}/email-history")
    fun getTemplateEmailHistory(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long,
        @RequestParam(defaultValue = "0") page: Int,
        @RequestParam(defaultValue = "20") size: Int
    ): Mono<ResponseEntity<Any>> {
        val token = extractToken(authHeader)
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailTemplateService.getTemplateById(id)
                        .flatMap { template ->
                            notificationLogService.getEmailHistoryBySubject(template.subject, page, size)
                                .map { (logs, total) ->
                                    ResponseEntity.ok(
                                        ApiResponseBuilder.success(
                                            "템플릿 발송 이력을 성공적으로 조회했습니다.",
                                            mapOf(
                                                "logs" to logs,
                                                "total" to total,
                                                "page" to page,
                                                "size" to size,
                                                "totalPages" to ((total + size - 1) / size).toInt(),
                                                "templateId" to id,
                                                "templateName" to template.name
                                            )
                                        ) as Any
                                    )
                                }
                        }
                        .onErrorResume(IllegalArgumentException::class.java) {
                            Mono.just(ResponseEntity.notFound().build<Any>())
                        }
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