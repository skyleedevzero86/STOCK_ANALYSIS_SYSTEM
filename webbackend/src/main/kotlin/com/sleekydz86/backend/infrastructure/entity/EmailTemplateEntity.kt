package com.sleekydz86.backend.infrastructure.entity

import jakarta.persistence.*
import java.time.LocalDateTime

@Entity
@Table(name = "email_templates")
data class EmailTemplateEntity(
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0,
    val name: String,
    val subject: String,
    val content: String,
    @Column(name = "is_active")
    val isActive: Boolean = true,
    @Column(name = "created_at")
    val createdAt: LocalDateTime = LocalDateTime.now(),
    @Column(name = "updated_at")
    val updatedAt: LocalDateTime = LocalDateTime.now()
) {
    fun toDomain(): com.stockanalysis.domain.model.EmailTemplate {
        return com.stockanalysis.domain.model.EmailTemplate(
            id = this.id,
            name = this.name,
            subject = this.subject,
            content = this.content,
            isActive = this.isActive,
            createdAt = this.createdAt,
            updatedAt = this.updatedAt
        )
    }

    companion object {
        fun fromDomain(domain: com.stockanalysis.domain.model.EmailTemplate): EmailTemplateEntity {
            return EmailTemplateEntity(
                id = domain.id ?: 0,
                name = domain.name,
                subject = domain.subject,
                content = domain.content,
                isActive = domain.isActive,
                createdAt = domain.createdAt,
                updatedAt = domain.updatedAt
            )
        }
    }
}