package com.sleekydz86.backend.infrastructure.entity

import com.sleekydz86.backend.domain.model.ContactInquiry
import jakarta.persistence.*
import java.time.LocalDateTime

@Entity
@Table(name = "contact_inquiries")
data class ContactInquiryEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long? = null,

    @Column(name = "name", nullable = false, length = 100)
    val name: String,

    @Column(name = "email", nullable = false, length = 255)
    val email: String,

    @Column(name = "phone", length = 20)
    val phone: String? = null,

    @Column(name = "category", nullable = false, length = 50)
    val category: String,

    @Column(name = "subject", nullable = false, length = 500)
    val subject: String,

    @Column(name = "message", nullable = false, columnDefinition = "TEXT")
    val message: String,

    @Column(name = "is_read", nullable = false)
    val isRead: Boolean = false,

    @Column(name = "created_at")
    val createdAt: LocalDateTime = LocalDateTime.now(),

    @Column(name = "updated_at")
    val updatedAt: LocalDateTime = LocalDateTime.now()
) {
    fun toDomain(): ContactInquiry = ContactInquiry(
        id = id,
        name = name,
        email = email,
        phone = phone,
        category = category,
        subject = subject,
        message = message,
        isRead = isRead,
        createdAt = createdAt,
        updatedAt = updatedAt
    )

    companion object {
        fun fromDomain(inquiry: ContactInquiry): ContactInquiryEntity = ContactInquiryEntity(
            id = inquiry.id,
            name = inquiry.name,
            email = inquiry.email,
            phone = inquiry.phone,
            category = inquiry.category,
            subject = inquiry.subject,
            message = inquiry.message,
            isRead = inquiry.isRead,
            createdAt = inquiry.createdAt,
            updatedAt = inquiry.updatedAt
        )
    }
}



