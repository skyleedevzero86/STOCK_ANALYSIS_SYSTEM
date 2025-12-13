package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.EmailTemplate
import com.sleekydz86.backend.domain.model.TemplateRequest
import com.sleekydz86.backend.infrastructure.entity.EmailTemplateEntity
import com.sleekydz86.backend.infrastructure.repository.EmailTemplateRepository
import org.springframework.data.domain.Page
import org.springframework.data.domain.PageRequest
import org.springframework.data.domain.Pageable
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import java.time.LocalDateTime
import java.util.Optional

@Service
class EmailTemplateService(
    private val emailTemplateRepository: EmailTemplateRepository
) {

    fun createTemplate(request: TemplateRequest): Mono<EmailTemplate> {
        val entity = EmailTemplateEntity(
            name = request.name,
            subject = request.subject,
            content = request.content,
            isActive = true,
            createdAt = LocalDateTime.now(),
            updatedAt = LocalDateTime.now()
        )

        return Mono.just(emailTemplateRepository.save(entity).toDomain())
    }

    fun getAllTemplates(): Mono<List<EmailTemplate>> {
        return Mono.just(emailTemplateRepository.findAllByIsActiveTrue()
            .map { entity: EmailTemplateEntity -> entity.toDomain() })
    }
    
    fun getTemplates(page: Int, size: Int, keyword: String?): Mono<Map<String, Any>> {
        return Mono.fromCallable {
            val pageable: Pageable = PageRequest.of(page, size)
            val result: Page<EmailTemplateEntity> = if (keyword.isNullOrBlank()) {
                emailTemplateRepository.findAllActive(pageable)
            } else {
                emailTemplateRepository.findAllActiveByKeyword(keyword.trim(), pageable)
            }
            
            mapOf(
                "templates" to result.content.map { it.toDomain() },
                "totalElements" to result.totalElements,
                "totalPages" to result.totalPages,
                "currentPage" to result.number,
                "pageSize" to result.size,
                "hasNext" to result.hasNext(),
                "hasPrevious" to result.hasPrevious()
            )
        }
    }

    fun getTemplateById(id: Long): Mono<EmailTemplate> {
        return Mono.fromCallable {
            emailTemplateRepository.findById(id)
                .map { entity: EmailTemplateEntity -> entity.toDomain() }
                .orElseThrow { IllegalArgumentException("Template not found with id: $id") }
        }
    }

    fun updateTemplate(id: Long, request: TemplateRequest): Mono<EmailTemplate> {
        return Mono.fromCallable {
            emailTemplateRepository.findById(id)
                .map { existing: EmailTemplateEntity ->
                    val updated = existing.copy(
                        name = request.name,
                        subject = request.subject,
                        content = request.content,
                        updatedAt = LocalDateTime.now()
                    )
                    emailTemplateRepository.save(updated).toDomain()
                }
                .orElseThrow { IllegalArgumentException("Template not found with id: $id") }
        }
    }

    fun deleteTemplate(id: Long): Mono<Void> {
        return Mono.fromCallable {
            emailTemplateRepository.findById(id)
                .map { existing: EmailTemplateEntity ->
                    val deactivated = existing.copy(
                        isActive = false,
                        updatedAt = LocalDateTime.now()
                    )
                    emailTemplateRepository.save(deactivated)
                }
                .orElseThrow { IllegalArgumentException("Template not found with id: $id") }
        }.then()
    }

    fun renderTemplate(template: EmailTemplate, variables: Map<String, String>): String {
        var renderedContent = template.content
        var renderedSubject = template.subject

        variables.forEach { (key, value) ->
            val placeholder = "{$key}"
            renderedContent = renderedContent.replace(placeholder, value)
            renderedSubject = renderedSubject.replace(placeholder, value)
        }

        return renderedContent
    }
}
