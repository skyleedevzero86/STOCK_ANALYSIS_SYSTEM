package com.sleekydz86.backend.domain.model

import java.time.LocalDateTime

data class AdminLoginResponse(
    val token: String,
    val expiresAt: LocalDateTime
)

