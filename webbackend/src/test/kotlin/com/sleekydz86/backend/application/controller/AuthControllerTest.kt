package com.sleekydz86.backend.application.controller

import com.fasterxml.jackson.databind.ObjectMapper
import com.sleekydz86.backend.application.dto.*
import com.sleekydz86.backend.domain.model.Role
import com.sleekydz86.backend.domain.model.User
import com.sleekydz86.backend.domain.service.AuthService
import com.sleekydz86.backend.domain.service.UserService
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.springframework.http.MediaType
import org.springframework.http.ResponseEntity
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken
import org.springframework.security.core.Authentication
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.*
import org.springframework.test.web.servlet.setup.MockMvcBuilders

class AuthControllerTest {

    private lateinit var authService: AuthService
    private lateinit var userService: UserService
    private lateinit var authController: AuthController
    private lateinit var mockMvc: MockMvc
    private lateinit var objectMapper: ObjectMapper

    @BeforeEach
    fun setUp() {
        authService = mockk()
        userService = mockk()
        authController = AuthController(authService, userService)
        mockMvc = MockMvcBuilders.standaloneSetup(authController).build()
        objectMapper = ObjectMapper()
    }

    @Test
    @DisplayName("Î°úÍ∑∏??- ?†Ìö®???êÍ≤©Ï¶ùÎ™Ö?????†ÌÅ∞ Î∞òÌôò")
    fun `login - should return tokens when credentials are valid`() {

        val loginRequest = LoginRequest(username = "testuser", password = "password123")
        val role = Role(name = "ROLE_USER")
        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            firstName = "John",
            lastName = "Doe",
            roles = setOf(role)
        )
        val authentication: Authentication = UsernamePasswordAuthenticationToken(user, null, user.authorities)
        val tokens = mapOf(
            "access_token" to "access.token",
            "refresh_token" to "refresh.token",
            "token_type" to "Bearer",
            "expires_in" to "3600"
        )

        every { authService.authenticate("testuser", "password123") } returns authentication
        every { authService.generateTokens(user) } returns tokens

        mockMvc.perform(
            post("/api/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginRequest))
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.accessToken").value("access.token"))
            .andExpect(jsonPath("$.refreshToken").value("refresh.token"))
            .andExpect(jsonPath("$.tokenType").value("Bearer"))
            .andExpect(jsonPath("$.expiresIn").value(3600L))
            .andExpect(jsonPath("$.user.username").value("testuser"))

        verify(exactly = 1) { authService.authenticate("testuser", "password123") }
        verify(exactly = 1) { authService.generateTokens(user) }
    }

    @Test
    @DisplayName("?åÏõêÍ∞Ä??- ???¨Ïö©???±Î°ù ?±Í≥µ")
    fun `register - should register new user successfully`() {

        val registerRequest = RegisterRequest(
            username = "newuser",
            email = "new@example.com",
            password = "password123",
            firstName = "Jane",
            lastName = "Smith"
        )
        val role = Role(name = "ROLE_USER")
        val user = User(
            id = 1L,
            username = "newuser",
            email = "new@example.com",
            password = "encodedPassword",
            firstName = "Jane",
            lastName = "Smith",
            roles = setOf(role)
        )
        val tokens = mapOf(
            "access_token" to "access.token",
            "refresh_token" to "refresh.token",
            "token_type" to "Bearer",
            "expires_in" to "3600"
        )

        every { userService.existsByUsername("newuser") } returns false
        every { userService.existsByEmail("new@example.com") } returns false
        every { userService.createUser("newuser", "new@example.com", "password123", "Jane", "Smith") } returns user
        every { authService.generateTokens(user) } returns tokens

        mockMvc.perform(
            post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest))
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.accessToken").value("access.token"))
            .andExpect(jsonPath("$.user.username").value("newuser"))

        verify(exactly = 1) { userService.existsByUsername("newuser") }
        verify(exactly = 1) { userService.existsByEmail("new@example.com") }
        verify(exactly = 1) { userService.createUser("newuser", "new@example.com", "password123", "Jane", "Smith") }
    }

    @Test
    @DisplayName("?åÏõêÍ∞Ä??- ?¥Î? Ï°¥Ïû¨?òÎäî ?¨Ïö©?êÎ™Ö????400 ?êÎü¨ Î∞òÌôò")
    fun `register - should return 400 when username already exists`() {

        val registerRequest = RegisterRequest(
            username = "existinguser",
            email = "new@example.com",
            password = "password123"
        )

        every { userService.existsByUsername("existinguser") } returns true

        mockMvc.perform(
            post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest))
        )
            .andExpect(status().isBadRequest)

        verify(exactly = 1) { userService.existsByUsername("existinguser") }
        verify(exactly = 0) { userService.existsByEmail(any()) }
        verify(exactly = 0) { userService.createUser(any(), any(), any(), any(), any()) }
    }

    @Test
    @DisplayName("?åÏõêÍ∞Ä??- ?¥Î? Ï°¥Ïû¨?òÎäî ?¥Î©î?ºÏùº ??400 ?êÎü¨ Î∞òÌôò")
    fun `register - should return 400 when email already exists`() {

        val registerRequest = RegisterRequest(
            username = "newuser",
            email = "existing@example.com",
            password = "password123"
        )

        every { userService.existsByUsername("newuser") } returns false
        every { userService.existsByEmail("existing@example.com") } returns true

        mockMvc.perform(
            post("/api/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(registerRequest))
        )
            .andExpect(status().isBadRequest)

        verify(exactly = 1) { userService.existsByUsername("newuser") }
        verify(exactly = 1) { userService.existsByEmail("existing@example.com") }
        verify(exactly = 0) { userService.createUser(any(), any(), any(), any(), any()) }
    }

    @Test
    @DisplayName("?†ÌÅ∞ Í∞±Ïã† - ?†Ìö®??Refresh Token?ºÎ°ú ???†ÌÅ∞ Î∞úÍ∏â")
    fun `refreshToken - should return new tokens with valid refresh token`() {

        val refreshTokenRequest = RefreshTokenRequest(refreshToken = "valid.refresh.token")
        val role = Role(name = "ROLE_USER")
        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            roles = setOf(role)
        )
        val tokens = mapOf(
            "access_token" to "new.access.token",
            "refresh_token" to "new.refresh.token",
            "token_type" to "Bearer",
            "expires_in" to "3600"
        )

        every { authService.refreshToken("valid.refresh.token") } returns tokens
        every { authService.extractUsername("new.access.token") } returns "testuser"
        every { userService.findByUsername("testuser") } returns user

        mockMvc.perform(
            post("/api/auth/refresh")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(refreshTokenRequest))
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.accessToken").value("new.access.token"))
            .andExpect(jsonPath("$.refreshToken").value("new.refresh.token"))

        verify(exactly = 1) { authService.refreshToken("valid.refresh.token") }
        verify(exactly = 1) { authService.extractUsername("new.access.token") }
        verify(exactly = 1) { userService.findByUsername("testuser") }
    }

    @Test
    @DisplayName("Î°úÍ∑∏?ÑÏõÉ - Î°úÍ∑∏?ÑÏõÉ ?±Í≥µ Î©îÏãúÏßÄ Î∞òÌôò")
    fun `logout - should return logout success message`() {

        mockMvc.perform(
            post("/api/auth/logout")
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.message").value("Logout successful"))
    }
}
