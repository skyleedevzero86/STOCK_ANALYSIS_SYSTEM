package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.Role
import com.sleekydz86.backend.domain.model.User
import com.sleekydz86.backend.global.security.JwtUtil
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.springframework.security.authentication.AuthenticationManager
import org.springframework.security.authentication.BadCredentialsException
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken
import org.springframework.security.core.Authentication

class AuthServiceTest {

    private lateinit var userService: UserService
    private lateinit var jwtUtil: JwtUtil
    private lateinit var authenticationManager: AuthenticationManager
    private lateinit var authService: AuthService

    @BeforeEach
    fun setUp() {
        userService = mockk()
        jwtUtil = mockk()
        authenticationManager = mockk()
        authService = AuthService(userService, jwtUtil, authenticationManager)
    }

    @Test
    @DisplayName("인증 - 유효한 자격증명일 때 인증 객체 반환")
    fun `authenticate - should return authentication when credentials are valid`() {
        //given
        val username = "testuser"
        val password = "password123"
        val authenticationToken = UsernamePasswordAuthenticationToken(username, password)
        val expectedAuthentication: Authentication = mockk()

        every { authenticationManager.authenticate(authenticationToken) } returns expectedAuthentication

        //when
        val result = authService.authenticate(username, password)

        //then
        assertEquals(expectedAuthentication, result)
        verify(exactly = 1) { authenticationManager.authenticate(authenticationToken) }
    }

    @Test
    @DisplayName("인증 - 유효하지 않은 자격증명일 때 예외 발생")
    fun `authenticate - should throw exception when credentials are invalid`() {
        //given
        val username = "testuser"
        val password = "wrongpassword"
        val authenticationToken = UsernamePasswordAuthenticationToken(username, password)

        every { authenticationManager.authenticate(authenticationToken) } throws BadCredentialsException("Bad credentials")

        //when & then
        assertThrows(BadCredentialsException::class.java) {
            authService.authenticate(username, password)
        }
        verify(exactly = 1) { authenticationManager.authenticate(authenticationToken) }
    }

    @Test
    @DisplayName("토큰 생성 - Access Token과 Refresh Token을 포함한 맵 반환")
    fun `generateTokens - should return tokens map with access and refresh token`() {
        //given
        val username = "testuser"
        val role = Role(name = "ROLE_USER")
        val user = User(
            id = 1L,
            username = username,
            email = "test@example.com",
            password = "encodedPassword",
            roles = setOf(role)
        )
        val expectedAccessToken = "access.token.here"
        val expectedRefreshToken = "refresh.token.here"

        every { jwtUtil.generateToken(username, listOf("ROLE_USER")) } returns expectedAccessToken
        every { jwtUtil.generateRefreshToken(username) } returns expectedRefreshToken

        //when
        val result = authService.generateTokens(user)

        //then
        assertNotNull(result)
        assertEquals(expectedAccessToken, result["access_token"])
        assertEquals(expectedRefreshToken, result["refresh_token"])
        assertEquals("Bearer", result["token_type"])
        assertEquals("3600", result["expires_in"])
        verify(exactly = 1) { jwtUtil.generateToken(username, listOf("ROLE_USER")) }
        verify(exactly = 1) { jwtUtil.generateRefreshToken(username) }
    }

    @Test
    @DisplayName("토큰 생성 - 여러 역할을 가진 사용자 처리")
    fun `generateTokens - should handle user with multiple roles`() {
        //given
        val username = "testuser"
        val role1 = Role(name = "ROLE_USER")
        val role2 = Role(name = "ROLE_ADMIN")
        val user = User(
            id = 1L,
            username = username,
            email = "test@example.com",
            password = "encodedPassword",
            roles = setOf(role1, role2)
        )
        val expectedAccessToken = "access.token.here"
        val expectedRefreshToken = "refresh.token.here"

        every { jwtUtil.generateToken(username, listOf("ROLE_USER", "ROLE_ADMIN")) } returns expectedAccessToken
        every { jwtUtil.generateRefreshToken(username) } returns expectedRefreshToken

        //when
        val result = authService.generateTokens(user)

        //then
        assertNotNull(result)
        assertEquals(expectedAccessToken, result["access_token"])
        assertEquals(expectedRefreshToken, result["refresh_token"])
        verify(exactly = 1) { jwtUtil.generateToken(username, listOf("ROLE_USER", "ROLE_ADMIN")) }
    }

    @Test
    @DisplayName("토큰 갱신 - 유효한 Refresh Token일 때 새 토큰 반환")
    fun `refreshToken - should return new tokens when refresh token is valid`() {
        //given
        val refreshToken = "valid.refresh.token"
        val username = "testuser"
        val role = Role(name = "ROLE_USER")
        val user = User(
            id = 1L,
            username = username,
            email = "test@example.com",
            password = "encodedPassword",
            roles = setOf(role)
        )
        val expectedAccessToken = "new.access.token"
        val expectedRefreshToken = "new.refresh.token"

        every { jwtUtil.validateToken(refreshToken) } returns true
        every { jwtUtil.extractUsername(refreshToken) } returns username
        every { userService.findByUsername(username) } returns user
        every { jwtUtil.generateToken(username, listOf("ROLE_USER")) } returns expectedAccessToken
        every { jwtUtil.generateRefreshToken(username) } returns expectedRefreshToken

        //when
        val result = authService.refreshToken(refreshToken)

        //then
        assertNotNull(result)
        assertEquals(expectedAccessToken, result["access_token"])
        assertEquals(expectedRefreshToken, result["refresh_token"])
        verify(exactly = 1) { jwtUtil.validateToken(refreshToken) }
        verify(exactly = 1) { jwtUtil.extractUsername(refreshToken) }
        verify(exactly = 1) { userService.findByUsername(username) }
    }

    @Test
    @DisplayName("토큰 갱신 - 유효하지 않은 Refresh Token일 때 예외 발생")
    fun `refreshToken - should throw exception when refresh token is invalid`() {
        //given
        val invalidRefreshToken = "invalid.refresh.token"

        every { jwtUtil.validateToken(invalidRefreshToken) } returns false

        //when & then
        assertThrows(IllegalArgumentException::class.java) {
            authService.refreshToken(invalidRefreshToken)
        }
        verify(exactly = 1) { jwtUtil.validateToken(invalidRefreshToken) }
        verify(exactly = 0) { jwtUtil.extractUsername(any()) }
        verify(exactly = 0) { userService.findByUsername(any()) }
    }

    @Test
    @DisplayName("토큰 갱신 - 사용자를 찾을 수 없을 때 예외 발생")
    fun `refreshToken - should throw exception when user not found`() {
        //given
        val refreshToken = "valid.refresh.token"
        val username = "nonexistent"

        every { jwtUtil.validateToken(refreshToken) } returns true
        every { jwtUtil.extractUsername(refreshToken) } returns username
        every { userService.findByUsername(username) } returns null

        //when & then
        assertThrows(IllegalArgumentException::class.java) {
            authService.refreshToken(refreshToken)
        }
        verify(exactly = 1) { jwtUtil.validateToken(refreshToken) }
        verify(exactly = 1) { jwtUtil.extractUsername(refreshToken) }
        verify(exactly = 1) { userService.findByUsername(username) }
    }

    @Test
    @DisplayName("토큰 검증 - 유효한 토큰일 때 true 반환")
    fun `validateToken - should return true when token is valid`() {
        //given
        val token = "valid.token"

        every { jwtUtil.validateToken(token) } returns true

        //when
        val result = authService.validateToken(token)

        //then
        assertTrue(result)
        verify(exactly = 1) { jwtUtil.validateToken(token) }
    }

    @Test
    @DisplayName("토큰 검증 - 유효하지 않은 토큰일 때 false 반환")
    fun `validateToken - should return false when token is invalid`() {
        //given
        val token = "invalid.token"

        every { jwtUtil.validateToken(token) } returns false

        //when
        val result = authService.validateToken(token)

        //then
        assertFalse(result)
        verify(exactly = 1) { jwtUtil.validateToken(token) }
    }

    @Test
    @DisplayName("사용자명 추출 - 토큰에서 사용자명 반환")
    fun `extractUsername - should return username from token`() {
        //given
        val token = "valid.token"
        val expectedUsername = "testuser"

        every { jwtUtil.extractUsername(token) } returns expectedUsername

        //when
        val result = authService.extractUsername(token)

        //then
        assertEquals(expectedUsername, result)
        verify(exactly = 1) { jwtUtil.extractUsername(token) }
    }

    @Test
    @DisplayName("역할 추출 - 토큰에서 역할 목록 반환")
    fun `extractRoles - should return roles from token`() {
        //given
        val token = "valid.token"
        val expectedRoles = listOf("ROLE_USER", "ROLE_ADMIN")

        every { jwtUtil.extractRoles(token) } returns expectedRoles

        //when
        val result = authService.extractRoles(token)

        //then
        assertEquals(expectedRoles, result)
        verify(exactly = 1) { jwtUtil.extractRoles(token) }
    }
}
