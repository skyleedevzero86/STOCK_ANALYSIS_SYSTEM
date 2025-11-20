package com.sleekydz86.backend.domain.model

import java.time.LocalDateTime

data class ContactInquiry(
    val id: Long? = null,
    val name: String,
    val email: String,
    val phone: String? = null,
    val category: String,
    val subject: String,
    val message: String,
    val isRead: Boolean = false,
    val createdAt: LocalDateTime = LocalDateTime.now(),
    val updatedAt: LocalDateTime = LocalDateTime.now()
)


