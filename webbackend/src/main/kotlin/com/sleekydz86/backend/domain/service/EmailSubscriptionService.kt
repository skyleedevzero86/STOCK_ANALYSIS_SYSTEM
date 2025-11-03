package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.EmailSubscription
import com.sleekydz86.backend.domain.model.EmailSubscriptionRequest
import com.sleekydz86.backend.infrastructure.entity.EmailSubscriptionEntity
import com.sleekydz86.backend.infrastructure.repository.EmailSubscriptionRepository
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import java.time.LocalDateTime

@Service
class EmailSubscriptionService(
    private val emailSubscriptionRepository: EmailSubscriptionRepository,
    private val passwordEncoder: BCryptPasswordEncoder
) {

    fun subscribe(request: EmailSubscriptionRequest): Mono<EmailSubscription> {
        return Mono.fromCallable {

            val existing = emailSubscriptionRepository.findByEmail(request.email)
            if (existing != null) {
                throw IllegalArgumentException("이미 등록된 이메일입니다.")
            }

            val subscription = EmailSubscriptionEntity(
                name = request.name,
                email = request.email,
                phone = request.phone,
                isEmailConsent = request.isEmailConsent,
                isPhoneConsent = request.isPhoneConsent,
                createdAt = LocalDateTime.now(),
                isActive = true
            )

            val saved = emailSubscriptionRepository.save(subscription)
            saved.toDomain()
        }
    }

    fun getAllActiveSubscriptions(): Mono<List<EmailSubscription>> {
        return Mono.fromCallable {
            emailSubscriptionRepository.findAllActive()
                .map { entity: EmailSubscriptionEntity -> entity.toDomain() }
        }
    }

    fun getActiveSubscriptionsWithEmailConsent(): Mono<List<EmailSubscription>> {
        return Mono.fromCallable {
            emailSubscriptionRepository.findAllActiveWithEmailConsent()
                .map { entity: EmailSubscriptionEntity -> entity.toDomain() }
        }
    }

    fun unsubscribe(email: String): Mono<Boolean> {
        return Mono.fromCallable {
            val subscription = emailSubscriptionRepository.findByEmail(email)
            if (subscription != null) {
                val updated = subscription.copy(isActive = false)
                emailSubscriptionRepository.save(updated)
                true
            } else {
                false
            }
        }
    }

    fun maskEmail(email: String): String {
        val parts = email.split("@")
        if (parts.size != 2) return email

        val username = parts[0]
        val domain = parts[1]

        return when {
            username.length <= 2 -> "*@$domain"
            username.length <= 4 -> "${username[0]}***@$domain"
            else -> "${username[0]}${"*".repeat(username.length - 2)}${username.last()}@$domain"
        }
    }

    fun maskPhone(phone: String?): String? {
        if (phone.isNullOrBlank()) return phone
        return when {
            phone.length <= 4 -> "*".repeat(phone.length)
            else -> "${phone.substring(0, 2)}${"*".repeat(phone.length - 4)}${phone.substring(phone.length - 2)}"
        }
    }
}
