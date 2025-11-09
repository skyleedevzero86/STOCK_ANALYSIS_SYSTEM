package com.sleekydz86.backend.domain.model

data class ContactInquiryReplyRequest(
    val inquiryId: Long,
    val content: String,
    val createdBy: String
)

