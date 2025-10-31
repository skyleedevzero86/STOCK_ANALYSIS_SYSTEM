package com.sleekydz86.backend.application.mapper

import com.sleekydz86.backend.domain.model.EmailSubscription

object EmailSubscriptionMapper {
    fun toMaskedSubscriptionMap(subscription: EmailSubscription, maskEmail: (String) -> String, maskPhone: (String?) -> String): Map<String, Any> {
        return mapOf(
            "id" to subscription.id,
            "name" to subscription.name,
            "email" to maskEmail(subscription.email),
            "phone" to maskPhone(subscription.phone),
            "isEmailConsent" to subscription.isEmailConsent,
            "isPhoneConsent" to subscription.isPhoneConsent,
            "createdAt" to subscription.createdAt,
            "isActive" to subscription.isActive
        )
    }

    fun toEmailConsentSubscriptionMap(subscription: EmailSubscription, maskPhone: (String?) -> String): Map<String, Any> {
        return mapOf(
            "id" to subscription.id,
            "name" to subscription.name,
            "email" to subscription.email,
            "phone" to maskPhone(subscription.phone),
            "isEmailConsent" to subscription.isEmailConsent,
            "isPhoneConsent" to subscription.isPhoneConsent,
            "createdAt" to subscription.createdAt
        )
    }
}

