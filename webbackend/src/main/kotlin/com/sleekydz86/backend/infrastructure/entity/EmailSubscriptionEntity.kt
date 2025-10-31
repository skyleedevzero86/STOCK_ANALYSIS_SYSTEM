package com.sleekydz86.backend.infrastructure.entity

import jakarta.persistence.*
import java.time.LocalDateTime

@Entity
@Table(name = "email_subscriptions")
data class EmailSubscriptionEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long? = null,

    @Column(name = "name", nullable = false, length = 100)
    val name: String,

    @Column(name = "email", nullable = false, unique = true, length = 255)
    val email: String,

    @Column(name = "phone", length = 20)
    val phone: String? = null,

    @Column(name = "is_email_consent", nullable = false)
    val isEmailConsent: Boolean = false,

    @Column(name = "is_phone_consent", nullable = false)
    val isPhoneConsent: Boolean = false,

    @Column(name = "created_at")
    val createdAt: LocalDateTime = LocalDateTime.now(),

    @Column(name = "is_active", nullable = false)
    val isActive: Boolean = true
) {
    fun toDomain(): EmailSubscription = EmailSubscription(
        id = id,
        name = name,
        email = email,
        phone = phone,
        isEmailConsent = isEmailConsent,
        isPhoneConsent = isPhoneConsent,
        createdAt = createdAt,
        isActive = isActive
    )

    companion object {
        fun fromDomain(subscription: EmailSubscription): EmailSubscriptionEntity = EmailSubscriptionEntity(
            id = subscription.id,
            name = subscription.name,
            email = subscription.email,
            phone = subscription.phone,
            isEmailConsent = subscription.isEmailConsent,
            isPhoneConsent = subscription.isPhoneConsent,
            createdAt = subscription.createdAt,
            isActive = subscription.isActive
        )
    }
}