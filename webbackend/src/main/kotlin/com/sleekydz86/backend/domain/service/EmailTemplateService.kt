package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.EmailTemplate
import com.sleekydz86.backend.domain.model.TemplateRequest
import com.sleekydz86.backend.infrastructure.entity.EmailTemplateEntity
import com.sleekydz86.backend.infrastructure.repository.EmailTemplateRepository
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
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

        return Mono.just(emailTemplateRepository.save(entity).toDomain())
    }

    fun getAllTemplates(): Mono<List<EmailTemplate>> {
        return Mono.just(emailTemplateRepository.findAllByIsActiveTrue()
            .map { entity: EmailTemplateEntity -> entity.toDomain() })
    }

    fun getTemplateById(id: Long): Mono<EmailTemplate> {
        return emailTemplateRepository.findById(id)
            ?.let { entity: EmailTemplateEntity -> Mono.just(entity.toDomain()) }
            ?: Mono.error(IllegalArgumentException("Template not found with id: $id"))
    }

    fun updateTemplate(id: Long, request: TemplateRequest): Mono<EmailTemplate> {
        return emailTemplateRepository.findById(id)
            ?.let { existing: EmailTemplateEntity ->
                val updated = existing.copy(
                    name = request.name,
                    subject = request.subject,
                    content = request.content,
                    updatedAt = LocalDateTime.now()
                )
                Mono.just(emailTemplateRepository.save(updated).toDomain())
            }
            ?: Mono.error(IllegalArgumentException("Template not found with id: $id"))
    }

    fun deleteTemplate(id: Long): Mono<Void> {
        return Mono.fromCallable {
            emailTemplateRepository.findById(id)
                ?.let { existing: EmailTemplateEntity ->
                    val deactivated = existing.copy(
                        isActive = false,
                        updatedAt = LocalDateTime.now()
                    )
                    emailTemplateRepository.save(deactivated)
                }
                ?: throw IllegalArgumentException("Template not found with id: $id")
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
