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
        //given
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

        //when
        val result = adminService.login(request)

        //then
        StepVerifier.create(result)
            .expectNextMatches { response ->
                response.token.isNotBlank() && response.expiresAt.isAfter(LocalDateTime.now())
            }
            .verifyComplete()
        verify(exactly = 1) { adminUserRepository.findByEmailAndIsActive(email, true) }
    }

    @Test
    fun `login - should throw exception when admin not found`() {
        //given
        val email = "nonexistent@example.com"
        val password = "password123"
        val request = AdminLoginRequest(email, password)

        every { adminUserRepository.findByEmailAndIsActive(email, true) } returns null

        //when
        val result = adminService.login(request)

        //then
        StepVerifier.create(result)
            .expectErrorMatches { it is IllegalArgumentException && it.message?.contains("관리자 계정을 찾을 수 없습니다") == true }
            .verify()
        verify(exactly = 1) { adminUserRepository.findByEmailAndIsActive(email, true) }
    }

    @Test
    fun `login - should throw exception when password is incorrect`() {
        //given
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

        //when
        val result = adminService.login(request)

        //then
        StepVerifier.create(result)
            .expectErrorMatches { it is IllegalArgumentException && it.message?.contains("비밀번호가 일치하지 않습니다") == true }
            .verify()
        verify(exactly = 1) { adminUserRepository.findByEmailAndIsActive(email, true) }
    }

    @Test
    fun `validateToken - should return true for valid token`() {
        //given
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

        //when
        val result = adminService.validateToken(token)

        //then
        StepVerifier.create(result)
            .expectNext(true)
            .verifyComplete()
        verify(exactly = 1) { adminUserRepository.findByEmailAndIsActive(email, true) }
    }

    @Test
    fun `validateToken - should return false for invalid token format`() {
        //given
        val invalidToken = "invalid.token"

        //when
        val result = adminService.validateToken(invalidToken)

        //then
        StepVerifier.create(result)
            .expectNext(false)
            .verifyComplete()
    }

    @Test
    fun `validateToken - should return false when admin not found`() {
        //given
        val email = "nonexistent@example.com"
        val timestamp = System.currentTimeMillis()
        val token = java.util.Base64.getEncoder().encodeToString("$email:$timestamp".toByteArray())

        every { adminUserRepository.findByEmailAndIsActive(email, true) } returns null

        //when
        val result = adminService.validateToken(token)

        //then
        StepVerifier.create(result)
            .expectNext(false)
            .verifyComplete()
        verify(exactly = 1) { adminUserRepository.findByEmailAndIsActive(email, true) }
    }

    @Test
    fun `validateToken - should return false for expired token`() {
        //given
        val email = "admin@example.com"
        val expiredTimestamp = System.currentTimeMillis() - (25 * 60 * 60 * 1000)
        val token = java.util.Base64.getEncoder().encodeToString("$email:$expiredTimestamp".toByteArray())

        //when
        val result = adminService.validateToken(token)

        //then
        StepVerifier.create(result)
            .expectNext(false)
            .verifyComplete()
    }
}
