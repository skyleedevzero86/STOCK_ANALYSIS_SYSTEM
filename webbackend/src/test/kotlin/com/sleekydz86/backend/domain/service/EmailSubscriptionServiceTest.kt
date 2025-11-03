package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.EmailSubscription
import com.sleekydz86.backend.domain.model.EmailSubscriptionRequest
import com.sleekydz86.backend.infrastructure.entity.EmailSubscriptionEntity
import com.sleekydz86.backend.infrastructure.repository.EmailSubscriptionRepository
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder
import reactor.test.StepVerifier
import java.time.LocalDateTime

class EmailSubscriptionServiceTest {

    private lateinit var emailSubscriptionRepository: EmailSubscriptionRepository
    private lateinit var passwordEncoder: BCryptPasswordEncoder
    private lateinit var emailSubscriptionService: EmailSubscriptionService

    @BeforeEach
    fun setUp() {
        emailSubscriptionRepository = mockk()
        passwordEncoder = BCryptPasswordEncoder()
        emailSubscriptionService = EmailSubscriptionService(emailSubscriptionRepository, passwordEncoder)
    }

    @Test
    fun `subscribe - should create subscription when email not exists`() {
        //given
        val request = EmailSubscriptionRequest(
            name = "John Doe",
            email = "john@example.com",
            phone = "010-1234-5678",
            isEmailConsent = true,
            isPhoneConsent = true
        )
        val entity = EmailSubscriptionEntity(
            id = 1L,
            name = request.name,
            email = request.email,
            phone = request.phone,
            isEmailConsent = request.isEmailConsent,
            isPhoneConsent = request.isPhoneConsent,
            isActive = true,
            createdAt = LocalDateTime.now()
        )

        every { emailSubscriptionRepository.findByEmail(request.email) } returns null
        every { emailSubscriptionRepository.save(any()) } returns entity

        //when
        val result = emailSubscriptionService.subscribe(request)

        //then
        StepVerifier.create(result)
            .expectNextMatches { subscription ->
                subscription.email == request.email &&
                subscription.name == request.name &&
                subscription.isEmailConsent == request.isEmailConsent &&
                subscription.isActive
            }
            .verifyComplete()
        verify(exactly = 1) { emailSubscriptionRepository.findByEmail(request.email) }
        verify(exactly = 1) { emailSubscriptionRepository.save(any()) }
    }

    @Test
    fun `subscribe - should throw exception when email already exists`() {
        //given
        val request = EmailSubscriptionRequest(
            name = "John Doe",
            email = "existing@example.com",
            isEmailConsent = true
        )
        val existingEntity = EmailSubscriptionEntity(
            id = 1L,
            name = "Existing User",
            email = request.email,
            isEmailConsent = true,
            isActive = true
        )

        every { emailSubscriptionRepository.findByEmail(request.email) } returns existingEntity

        //when
        val result = emailSubscriptionService.subscribe(request)

        //then
        StepVerifier.create(result)
            .expectErrorMatches { it is IllegalArgumentException && it.message?.contains("이미 등록된 이메일입니다") == true }
            .verify()
        verify(exactly = 1) { emailSubscriptionRepository.findByEmail(request.email) }
        verify(exactly = 0) { emailSubscriptionRepository.save(any()) }
    }

    @Test
    fun `getAllActiveSubscriptions - should return list of active subscriptions`() {
        //given
        val entities = listOf(
            EmailSubscriptionEntity(
                id = 1L,
                name = "User 1",
                email = "user1@example.com",
                isEmailConsent = true,
                isActive = true,
                createdAt = LocalDateTime.now()
            ),
            EmailSubscriptionEntity(
                id = 2L,
                name = "User 2",
                email = "user2@example.com",
                isEmailConsent = true,
                isActive = true,
                createdAt = LocalDateTime.now()
            )
        )

        every { emailSubscriptionRepository.findAllActive() } returns entities

        //when
        val result = emailSubscriptionService.getAllActiveSubscriptions()

        //then
        StepVerifier.create(result)
            .expectNextMatches { subscriptions ->
                subscriptions.size == 2 &&
                subscriptions.all { it.isActive }
            }
            .verifyComplete()
        verify(exactly = 1) { emailSubscriptionRepository.findAllActive() }
    }

    @Test
    fun `getActiveSubscriptionsWithEmailConsent - should return list with email consent`() {
        //given
        val entities = listOf(
            EmailSubscriptionEntity(
                id = 1L,
                name = "User 1",
                email = "user1@example.com",
                isEmailConsent = true,
                isActive = true,
                createdAt = LocalDateTime.now()
            )
        )

        every { emailSubscriptionRepository.findAllActiveWithEmailConsent() } returns entities

        //when
        val result = emailSubscriptionService.getActiveSubscriptionsWithEmailConsent()

        //then
        StepVerifier.create(result)
            .expectNextMatches { subscriptions ->
                subscriptions.size == 1 &&
                subscriptions.all { it.isEmailConsent && it.isActive }
            }
            .verifyComplete()
        verify(exactly = 1) { emailSubscriptionRepository.findAllActiveWithEmailConsent() }
    }

    @Test
    fun `unsubscribe - should deactivate subscription when exists`() {
        //given
        val email = "user@example.com"
        val entity = EmailSubscriptionEntity(
            id = 1L,
            name = "User",
            email = email,
            isEmailConsent = true,
            isActive = true,
            createdAt = LocalDateTime.now()
        )
        val deactivatedEntity = entity.copy(isActive = false)

        every { emailSubscriptionRepository.findByEmail(email) } returns entity
        every { emailSubscriptionRepository.save(any()) } returns deactivatedEntity

        //when
        val result = emailSubscriptionService.unsubscribe(email)

        //then
        StepVerifier.create(result)
            .expectNext(true)
            .verifyComplete()
        verify(exactly = 1) { emailSubscriptionRepository.findByEmail(email) }
        verify(exactly = 1) { emailSubscriptionRepository.save(any()) }
    }

    @Test
    fun `unsubscribe - should return false when subscription not found`() {
        //given
        val email = "nonexistent@example.com"

        every { emailSubscriptionRepository.findByEmail(email) } returns null

        //when
        val result = emailSubscriptionService.unsubscribe(email)

        //then
        StepVerifier.create(result)
            .expectNext(false)
            .verifyComplete()
        verify(exactly = 1) { emailSubscriptionRepository.findByEmail(email) }
        verify(exactly = 0) { emailSubscriptionRepository.save(any()) }
    }

    @Test
    fun `maskEmail - should mask email correctly for short username`() {
        //given
        val email = "ab@example.com"

        //when
        val result = emailSubscriptionService.maskEmail(email)

        //then
        assertEquals("*@example.com", result)
    }

    @Test
    fun `maskEmail - should mask email correctly for medium username`() {
        //given
        val email = "abcd@example.com"

        //when
        val result = emailSubscriptionService.maskEmail(email)

        //then
        assertEquals("a***@example.com", result)
    }

    @Test
    fun `maskEmail - should mask email correctly for long username`() {
        //given
        val email = "john.doe@example.com"

        //when
        val result = emailSubscriptionService.maskEmail(email)

        //then
        assertTrue(result.startsWith("j"))
        assertTrue(result.contains("*"))
        assertTrue(result.endsWith("@example.com"))
    }

    @Test
    fun `maskEmail - should return original email for invalid format`() {
        //given
        val email = "invalid-email"

        //when
        val result = emailSubscriptionService.maskEmail(email)

        //then
        assertEquals(email, result)
    }

    @Test
    fun `maskPhone - should return null for null phone`() {
        //given
        val phone: String? = null

        //when
        val result = emailSubscriptionService.maskPhone(phone)

        //then
        assertNull(result)
    }

    @Test
    fun `maskPhone - should return null for blank phone`() {
        //given
        val phone = "   "

        //when
        val result = emailSubscriptionService.maskPhone(phone)

        //then
        assertNull(result)
    }

    @Test
    fun `maskPhone - should mask phone correctly for short phone`() {
        //given
        val phone = "1234"

        //when
        val result = emailSubscriptionService.maskPhone(phone)

        //then
        assertEquals("****", result)
    }

    @Test
    fun `maskPhone - should mask phone correctly for long phone`() {
        //given
        val phone = "010-1234-5678"

        //when
        val result = emailSubscriptionService.maskPhone(phone)

        //then
        assertTrue(result!!.startsWith("01"))
        assertTrue(result.contains("*"))
        assertTrue(result.endsWith("78"))
    }
}
