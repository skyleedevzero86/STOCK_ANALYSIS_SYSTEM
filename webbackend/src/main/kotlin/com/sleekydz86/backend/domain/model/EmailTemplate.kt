package com.sleekydz86.backend.domain.model

import java.time.LocalDateTime

data class EmailTemplate(
    val id: Long? = null,
    val name: String,
    val subject: String,
    val content: String,
    val isActive: Boolean = true,
    val createdAt: LocalDateTime = LocalDateTime.now(),
    val updatedAt: LocalDateTime = LocalDateTime.now()
)

