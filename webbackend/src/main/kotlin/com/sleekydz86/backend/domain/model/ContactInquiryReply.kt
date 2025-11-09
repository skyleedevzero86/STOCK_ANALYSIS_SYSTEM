package com.sleekydz86.backend.domain.model

import java.time.LocalDateTime

data class ContactInquiryReply(
    val id: Long? = null,
    val inquiryId: Long,
    val content: String,
    val createdBy: String,
    val createdAt: LocalDateTime = LocalDateTime.now()
)

