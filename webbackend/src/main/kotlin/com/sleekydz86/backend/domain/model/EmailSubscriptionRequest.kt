package com.sleekydz86.backend.domain.model

data class EmailSubscriptionRequest(
    val name: String,
    val email: String,
    val phone: String? = null,
    val isEmailConsent: Boolean,
    val isPhoneConsent: Boolean = false
)

