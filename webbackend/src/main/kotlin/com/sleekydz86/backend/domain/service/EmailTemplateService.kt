package com.sleekydz86.backend.domain.service

import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import reactor.kotlin.core.publisher.toMono
import java.time.LocalDateTime

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

        return emailTemplateRepository.save(entity).toDomain().toMono()
    }

    fun getAllTemplates(): Mono<List<EmailTemplate>> {
        return emailTemplateRepository.findAllByIsActiveTrue()
            .map { it.toDomain() }
            .toMono()
    }

    fun getTemplateById(id: Long): Mono<EmailTemplate> {
        return emailTemplateRepository.findById(id)
            ?.toDomain()
            ?.toMono()
            ?: Mono.error(IllegalArgumentException("Template not found with id: $id"))
    }

    fun updateTemplate(id: Long, request: TemplateRequest): Mono<EmailTemplate> {
        return emailTemplateRepository.findById(id)
            ?.let { existing ->
                val updated = existing.copy(
                    name = request.name,
                    subject = request.subject,
                    content = request.content,
                    updatedAt = LocalDateTime.now()
                )
                emailTemplateRepository.save(updated).toDomain().toMono()
            }
            ?: Mono.error(IllegalArgumentException("Template not found with id: $id"))
    }

    fun deleteTemplate(id: Long): Mono<Void> {
        return emailTemplateRepository.findById(id)
            ?.let { existing ->
                val deactivated = existing.copy(
                    isActive = false,
                    updatedAt = LocalDateTime.now()
                )
                emailTemplateRepository.save(deactivated).then()
            }
            ?: Mono.error(IllegalArgumentException("Template not found with id: $id"))
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
