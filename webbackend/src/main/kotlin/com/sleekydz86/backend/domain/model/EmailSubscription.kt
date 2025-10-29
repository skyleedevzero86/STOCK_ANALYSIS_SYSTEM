package com.sleekydz86.backend.domain.model

import java.time.LocalDateTime

data class EmailSubscription(
    val id: Long? = null,
    val name: String,
    val email: String,
    val phone: String? = null,
    val isEmailConsent: Boolean,
    val isPhoneConsent: Boolean = false,
    val createdAt: LocalDateTime = LocalDateTime.now(),
    val isActive: Boolean = true
)

data class AdminUser(
    val id: Long? = null,
    val email: String,
    val password: String, // 암호화된 비밀번호
    val createdAt: LocalDateTime = LocalDateTime.now(),
    val isActive: Boolean = true
)

data class EmailSubscriptionRequest(
    val name: String,
    val email: String,
    val phone: String? = null,
    val isEmailConsent: Boolean,
    val isPhoneConsent: Boolean = false
)

data class AdminLoginRequest(
    val email: String,
    val password: String
)

data class AdminLoginResponse(
    val token: String,
    val expiresAt: LocalDateTime
)