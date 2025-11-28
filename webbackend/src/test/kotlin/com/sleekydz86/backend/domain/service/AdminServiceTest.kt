package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.AdminLoginRequest
import com.sleekydz86.backend.infrastructure.entity.AdminUserEntity
import com.sleekydz86.backend.infrastructure.repository.AdminUserRepository
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder
import reactor.test.StepVerifier
import java.time.LocalDateTime

class AdminServiceTest {

    private lateinit var adminUserRepository: AdminUserRepository
    private lateinit var passwordEncoder: BCryptPasswordEncoder
    private lateinit var adminService: AdminService

    @BeforeEach
    fun setUp() {
        adminUserRepository = mockk()
        passwordEncoder = BCryptPasswordEncoder()
        adminService = AdminService(adminUserRepository, passwordEncoder)
    }

    @Test
    fun `login - should return token when credentials are valid`() {

        val email = "admin@example.com"
        val password = "admin123"
        val hashedPassword = passwordEncoder.encode(password)
        val request = AdminLoginRequest(email, password)
        
        val adminEntity = AdminUserEntity(
            id = 1L,
            email = email,
            passwordHash = hashedPassword,
            isActive = true,
            createdAt = LocalDateTime.now()
        )

        every { adminUserRepository.findByEmailAndIsActive(email, true) } returns adminEntity

        val result = adminService.login(request)

        StepVerifier.create(result)
            .expectNextMatches { response ->
                response.token.isNotBlank() && response.expiresAt.isAfter(LocalDateTime.now())
            }
            .verifyComplete()
        verify(exactly = 1) { adminUserRepository.findByEmailAndIsActive(email, true) }
    }

    @Test
    fun `login - should throw exception when admin not found`() {

        val email = "nonexistent@example.com"
        val password = "password123"
        val request = AdminLoginRequest(email, password)

        every { adminUserRepository.findByEmailAndIsActive(email, true) } returns null

        val result = adminService.login(request)

        StepVerifier.create(result)
            .expectErrorMatches { it is IllegalArgumentException && it.message?.contains("관리자 계정??찾을 ???�습?�다") == true }
            .verify()
        verify(exactly = 1) { adminUserRepository.findByEmailAndIsActive(email, true) }
    }

    @Test
    fun `login - should throw exception when password is incorrect`() {

        val email = "admin@example.com"
        val correctPassword = "correctPassword"
        val wrongPassword = "wrongPassword"
        val hashedPassword = passwordEncoder.encode(correctPassword)
        val request = AdminLoginRequest(email, wrongPassword)
        
        val adminEntity = AdminUserEntity(
            id = 1L,
            email = email,
            passwordHash = hashedPassword,
            isActive = true,
            createdAt = LocalDateTime.now()
        )

        every { adminUserRepository.findByEmailAndIsActive(email, true) } returns adminEntity

        val result = adminService.login(request)

        StepVerifier.create(result)
            .expectErrorMatches { it is IllegalArgumentException && it.message?.contains("비�?번호가 ?�치?��? ?�습?�다") == true }
            .verify()
        verify(exactly = 1) { adminUserRepository.findByEmailAndIsActive(email, true) }
    }

    @Test
    fun `validateToken - should return true for valid token`() {

        val email = "admin@example.com"
        val timestamp = System.currentTimeMillis()
        val token = java.util.Base64.getEncoder().encodeToString("$email:$timestamp".toByteArray())
        
        val adminEntity = AdminUserEntity(
            id = 1L,
            email = email,
            passwordHash = passwordEncoder.encode("password"),
            isActive = true,
            createdAt = LocalDateTime.now()
        )

        every { adminUserRepository.findByEmailAndIsActive(email, true) } returns adminEntity

        val result = adminService.validateToken(token)

        StepVerifier.create(result)
            .expectNext(true)
            .verifyComplete()
        verify(exactly = 1) { adminUserRepository.findByEmailAndIsActive(email, true) }
    }

    @Test
    fun `validateToken - should return false for invalid token format`() {

        val invalidToken = "invalid.token"

        val result = adminService.validateToken(invalidToken)

        StepVerifier.create(result)
            .expectNext(false)
            .verifyComplete()
    }

    @Test
    fun `validateToken - should return false when admin not found`() {

        val email = "nonexistent@example.com"
        val timestamp = System.currentTimeMillis()
        val token = java.util.Base64.getEncoder().encodeToString("$email:$timestamp".toByteArray())

        every { adminUserRepository.findByEmailAndIsActive(email, true) } returns null

        val result = adminService.validateToken(token)

        StepVerifier.create(result)
            .expectNext(false)
            .verifyComplete()
        verify(exactly = 1) { adminUserRepository.findByEmailAndIsActive(email, true) }
    }

    @Test
    fun `validateToken - should return false for expired token`() {

        val email = "admin@example.com"
        val expiredTimestamp = System.currentTimeMillis() - (25 * 60 * 60 * 1000)
        val token = java.util.Base64.getEncoder().encodeToString("$email:$expiredTimestamp".toByteArray())

        val result = adminService.validateToken(token)

        StepVerifier.create(result)
            .expectNext(false)
            .verifyComplete()
    }
}
