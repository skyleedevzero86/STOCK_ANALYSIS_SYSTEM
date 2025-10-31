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
    @DisplayName("로그인 - 유효한 자격증명일 때 토큰 반환")
    fun `login - should return tokens when credentials are valid`() {
        //given
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

        //when & then
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
    @DisplayName("회원가입 - 새 사용자 등록 성공")
    fun `register - should register new user successfully`() {
        //given
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

        //when & then
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
    @DisplayName("회원가입 - 이미 존재하는 사용자명일 때 400 에러 반환")
    fun `register - should return 400 when username already exists`() {
        //given
        val registerRequest = RegisterRequest(
            username = "existinguser",
            email = "new@example.com",
            password = "password123"
        )

        every { userService.existsByUsername("existinguser") } returns true

        //when & then
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
    @DisplayName("회원가입 - 이미 존재하는 이메일일 때 400 에러 반환")
    fun `register - should return 400 when email already exists`() {
        //given
        val registerRequest = RegisterRequest(
            username = "newuser",
            email = "existing@example.com",
            password = "password123"
        )

        every { userService.existsByUsername("newuser") } returns false
        every { userService.existsByEmail("existing@example.com") } returns true

        //when & then
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
    @DisplayName("토큰 갱신 - 유효한 Refresh Token으로 새 토큰 발급")
    fun `refreshToken - should return new tokens with valid refresh token`() {
        //given
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

        //when & then
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
    @DisplayName("로그아웃 - 로그아웃 성공 메시지 반환")
    fun `logout - should return logout success message`() {
        //when & then
        mockMvc.perform(
            post("/api/auth/logout")
        )
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.message").value("Logout successful"))
    }
}
