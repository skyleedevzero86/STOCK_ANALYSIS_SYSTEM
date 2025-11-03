package com.sleekydz86.backend.domain.model

import java.time.LocalDateTime

data class AdminUser(
    val id: Long? = null,
    val email: String,
    val password: String,
    val createdAt: LocalDateTime = LocalDateTime.now(),
    val isActive: Boolean = true
)

