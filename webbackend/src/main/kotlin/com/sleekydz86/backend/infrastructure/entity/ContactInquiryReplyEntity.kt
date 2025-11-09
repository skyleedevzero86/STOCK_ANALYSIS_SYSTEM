package com.sleekydz86.backend.infrastructure.entity

import com.sleekydz86.backend.domain.model.ContactInquiryReply
import jakarta.persistence.*
import java.time.LocalDateTime

@Entity
@Table(name = "contact_inquiry_replies")
data class ContactInquiryReplyEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long? = null,

    @Column(name = "inquiry_id", nullable = false)
    val inquiryId: Long,

    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    val content: String,

    @Column(name = "created_by", nullable = false, length = 100)
    val createdBy: String,

    @Column(name = "created_at")
    val createdAt: LocalDateTime = LocalDateTime.now()
) {
    fun toDomain(): ContactInquiryReply = ContactInquiryReply(
        id = id,
        inquiryId = inquiryId,
        content = content,
        createdBy = createdBy,
        createdAt = createdAt
    )

    companion object {
        fun fromDomain(reply: ContactInquiryReply): ContactInquiryReplyEntity = ContactInquiryReplyEntity(
            id = reply.id,
            inquiryId = reply.inquiryId,
            content = reply.content,
            createdBy = reply.createdBy,
            createdAt = reply.createdAt
        )
    }
}

