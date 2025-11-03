package com.sleekydz86.backend.application.controller

import com.fasterxml.jackson.databind.ObjectMapper
import com.sleekydz86.backend.application.dto.ApiResponse
import com.sleekydz86.backend.application.mapper.EmailSubscriptionMapper
import com.sleekydz86.backend.domain.model.AdminLoginRequest
import com.sleekydz86.backend.domain.model.AdminLoginResponse
import com.sleekydz86.backend.domain.model.EmailSubscription
import com.sleekydz86.backend.domain.service.AdminService
import com.sleekydz86.backend.domain.service.EmailSubscriptionService
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import org.springframework.http.MediaType
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.*
import org.springframework.test.web.servlet.setup.MockMvcBuilders
import reactor.core.publisher.Mono
import java.time.LocalDateTime

class AdminControllerTest {

    private lateinit var adminService: AdminService
    private lateinit var emailSubscriptionService: EmailSubscriptionService
    private lateinit var adminController: AdminController
    private lateinit var mockMvc: MockMvc
    private lateinit var objectMapper: ObjectMapper

    @BeforeEach
    fun setUp() {
        adminService = mockk()
        emailSubscriptionService = mockk()
        adminController = AdminController(adminService, emailSubscriptionService)
        mockMvc = MockMvcBuilders.standaloneSetup(adminController).build()
        objectMapper = ObjectMapper()
    }

    @Test
    fun `login - should return success response when credentials are valid`() {
        //given
        val request = AdminLoginRequest("admin@example.com", "password123")
        val response = AdminLoginResponse(
            token = "token123",
            expiresAt = LocalDateTime.now().plusHours(24)
        )

        every { adminService.login(request) } returns Mono.just(response)

        //when & then
        mockMvc.perform(
            post("/api/admin/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request))
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.success").value(true))
            .andExpect(jsonPath("$.data.token").exists())
            .andExpect(jsonPath("$.data.expiresAt").exists())

        verify(exactly = 1) { adminService.login(request) }
    }

    @Test
    fun `login - should return failure response when credentials are invalid`() {
        //given
        val request = AdminLoginRequest("admin@example.com", "wrongPassword")

        every { adminService.login(request) } returns Mono.error(IllegalArgumentException("로그인에 실패했습니다."))

        //when & then
        mockMvc.perform(
            post("/api/admin/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request))
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.success").value(false))

        verify(exactly = 1) { adminService.login(request) }
    }

    @Test
    fun `getSubscriptions - should return subscriptions when token is valid`() {
        //given
        val token = "Bearer validToken"
        val subscriptions = listOf(
            EmailSubscription(
                id = 1L,
                name = "User 1",
                email = "user1@example.com",
                isEmailConsent = true,
                isActive = true,
                createdAt = LocalDateTime.now()
            )
        )

        every { adminService.validateToken(token) } returns Mono.just(true)
        every { emailSubscriptionService.getAllActiveSubscriptions() } returns Mono.just(subscriptions)
        every { emailSubscriptionService.maskEmail(any()) } answers { callOriginal<EmailSubscriptionService>().maskEmail(firstArg()) }
        every { emailSubscriptionService.maskPhone(any<String?>()) } answers { callOriginal<EmailSubscriptionService>().maskPhone(firstArg()) }

        //when & then
        mockMvc.perform(
            get("/api/admin/subscriptions")
                .header("Authorization", token)
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.success").value(true))
            .andExpect(jsonPath("$.data.total").value(1))

        verify(exactly = 1) { adminService.validateToken(token) }
        verify(exactly = 1) { emailSubscriptionService.getAllActiveSubscriptions() }
    }

    @Test
    fun `getSubscriptions - should return failure when token is invalid`() {
        //given
        val token = "Bearer invalidToken"

        every { adminService.validateToken(token) } returns Mono.just(false)

        //when & then
        mockMvc.perform(
            get("/api/admin/subscriptions")
                .header("Authorization", token)
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.success").value(false))
            .andExpect(jsonPath("$.message").value("인증이 필요합니다."))

        verify(exactly = 1) { adminService.validateToken(token) }
        verify(exactly = 0) { emailSubscriptionService.getAllActiveSubscriptions() }
    }

    @Test
    fun `getEmailConsentList - should return subscriptions with email consent when token is valid`() {
        //given
        val token = "Bearer validToken"
        val subscriptions = listOf(
            EmailSubscription(
                id = 1L,
                name = "User 1",
                email = "user1@example.com",
                isEmailConsent = true,
                isActive = true,
                createdAt = LocalDateTime.now()
            )
        )

        every { adminService.validateToken(token) } returns Mono.just(true)
        every { emailSubscriptionService.getActiveSubscriptionsWithEmailConsent() } returns Mono.just(subscriptions)
        every { emailSubscriptionService.maskPhone(any<String?>()) } answers { callOriginal<EmailSubscriptionService>().maskPhone(firstArg()) }

        //when & then
        mockMvc.perform(
            get("/api/admin/email-consent-list")
                .header("Authorization", token)
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.success").value(true))
            .andExpect(jsonPath("$.data.total").value(1))

        verify(exactly = 1) { adminService.validateToken(token) }
        verify(exactly = 1) { emailSubscriptionService.getActiveSubscriptionsWithEmailConsent() }
    }

    @Test
    fun `getEmailConsentList - should return failure when token is invalid`() {
        //given
        val token = "Bearer invalidToken"

        every { adminService.validateToken(token) } returns Mono.just(false)

        //when & then
        mockMvc.perform(
            get("/api/admin/email-consent-list")
                .header("Authorization", token)
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.success").value(false))
            .andExpect(jsonPath("$.message").value("인증이 필요합니다."))

        verify(exactly = 1) { adminService.validateToken(token) }
        verify(exactly = 0) { emailSubscriptionService.getActiveSubscriptionsWithEmailConsent() }
    }
}
