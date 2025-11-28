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
    @DisplayName("?∏Ï¶ù - ?†Ìö®???êÍ≤©Ï¶ùÎ™Ö?????∏Ï¶ù Í∞ùÏ≤¥ Î∞òÌôò")
    fun `authenticate - should return authentication when credentials are valid`() {

        val username = "testuser"
        val password = "password123"
        val authenticationToken = UsernamePasswordAuthenticationToken(username, password)
        val expectedAuthentication: Authentication = mockk()

        every { authenticationManager.authenticate(authenticationToken) } returns expectedAuthentication

        val result = authService.authenticate(username, password)

        assertEquals(expectedAuthentication, result)
        verify(exactly = 1) { authenticationManager.authenticate(authenticationToken) }
    }

    @Test
    @DisplayName("?∏Ï¶ù - ?†Ìö®?òÏ? ?äÏ? ?êÍ≤©Ï¶ùÎ™Ö?????àÏô∏ Î∞úÏÉù")
    fun `authenticate - should throw exception when credentials are invalid`() {

        val username = "testuser"
        val password = "wrongpassword"
        val authenticationToken = UsernamePasswordAuthenticationToken(username, password)

        every { authenticationManager.authenticate(authenticationToken) } throws BadCredentialsException("Bad credentials")

        assertThrows(BadCredentialsException::class.java) {
            authService.authenticate(username, password)
        }
        verify(exactly = 1) { authenticationManager.authenticate(authenticationToken) }
    }

    @Test
    @DisplayName("?†ÌÅ∞ ?ùÏÑ± - Access TokenÍ≥?Refresh Token???¨Ìï®??Îß?Î∞òÌôò")
    fun `generateTokens - should return tokens map with access and refresh token`() {

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

        val result = authService.generateTokens(user)

        assertNotNull(result)
        assertEquals(expectedAccessToken, result["access_token"])
        assertEquals(expectedRefreshToken, result["refresh_token"])
        assertEquals("Bearer", result["token_type"])
        assertEquals("3600", result["expires_in"])
        verify(exactly = 1) { jwtUtil.generateToken(username, listOf("ROLE_USER")) }
        verify(exactly = 1) { jwtUtil.generateRefreshToken(username) }
    }

    @Test
    @DisplayName("?†ÌÅ∞ ?ùÏÑ± - ?¨Îü¨ ??ï†??Í∞ÄÏß??¨Ïö©??Ï≤òÎ¶¨")
    fun `generateTokens - should handle user with multiple roles`() {

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

        val result = authService.generateTokens(user)

        assertNotNull(result)
        assertEquals(expectedAccessToken, result["access_token"])
        assertEquals(expectedRefreshToken, result["refresh_token"])
        verify(exactly = 1) { jwtUtil.generateToken(username, listOf("ROLE_USER", "ROLE_ADMIN")) }
    }

    @Test
    @DisplayName("?†ÌÅ∞ Í∞±Ïã† - ?†Ìö®??Refresh Token???????†ÌÅ∞ Î∞òÌôò")
    fun `refreshToken - should return new tokens when refresh token is valid`() {

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

        val result = authService.refreshToken(refreshToken)

        assertNotNull(result)
        assertEquals(expectedAccessToken, result["access_token"])
        assertEquals(expectedRefreshToken, result["refresh_token"])
        verify(exactly = 1) { jwtUtil.validateToken(refreshToken) }
        verify(exactly = 1) { jwtUtil.extractUsername(refreshToken) }
        verify(exactly = 1) { userService.findByUsername(username) }
    }

    @Test
    @DisplayName("?†ÌÅ∞ Í∞±Ïã† - ?†Ìö®?òÏ? ?äÏ? Refresh Token?????àÏô∏ Î∞úÏÉù")
    fun `refreshToken - should throw exception when refresh token is invalid`() {

        val invalidRefreshToken = "invalid.refresh.token"

        every { jwtUtil.validateToken(invalidRefreshToken) } returns false

        assertThrows(IllegalArgumentException::class.java) {
            authService.refreshToken(invalidRefreshToken)
        }
        verify(exactly = 1) { jwtUtil.validateToken(invalidRefreshToken) }
        verify(exactly = 0) { jwtUtil.extractUsername(any()) }
        verify(exactly = 0) { userService.findByUsername(any()) }
    }

    @Test
    @DisplayName("?†ÌÅ∞ Í∞±Ïã† - ?¨Ïö©?êÎ? Ï∞æÏùÑ ???ÜÏùÑ ???àÏô∏ Î∞úÏÉù")
    fun `refreshToken - should throw exception when user not found`() {

        val refreshToken = "valid.refresh.token"
        val username = "nonexistent"

        every { jwtUtil.validateToken(refreshToken) } returns true
        every { jwtUtil.extractUsername(refreshToken) } returns username
        every { userService.findByUsername(username) } returns null

        assertThrows(IllegalArgumentException::class.java) {
            authService.refreshToken(refreshToken)
        }
        verify(exactly = 1) { jwtUtil.validateToken(refreshToken) }
        verify(exactly = 1) { jwtUtil.extractUsername(refreshToken) }
        verify(exactly = 1) { userService.findByUsername(username) }
    }

    @Test
    @DisplayName("?†ÌÅ∞ Í≤ÄÏ¶?- ?†Ìö®???†ÌÅ∞????true Î∞òÌôò")
    fun `validateToken - should return true when token is valid`() {

        val token = "valid.token"

        every { jwtUtil.validateToken(token) } returns true

        val result = authService.validateToken(token)

        assertTrue(result)
        verify(exactly = 1) { jwtUtil.validateToken(token) }
    }

    @Test
    @DisplayName("?†ÌÅ∞ Í≤ÄÏ¶?- ?†Ìö®?òÏ? ?äÏ? ?†ÌÅ∞????false Î∞òÌôò")
    fun `validateToken - should return false when token is invalid`() {

        val token = "invalid.token"

        every { jwtUtil.validateToken(token) } returns false

        val result = authService.validateToken(token)

        assertFalse(result)
        verify(exactly = 1) { jwtUtil.validateToken(token) }
    }

    @Test
    @DisplayName("?¨Ïö©?êÎ™Ö Ï∂îÏ∂ú - ?†ÌÅ∞?êÏÑú ?¨Ïö©?êÎ™Ö Î∞òÌôò")
    fun `extractUsername - should return username from token`() {

        val token = "valid.token"
        val expectedUsername = "testuser"

        every { jwtUtil.extractUsername(token) } returns expectedUsername

        val result = authService.extractUsername(token)

        assertEquals(expectedUsername, result)
        verify(exactly = 1) { jwtUtil.extractUsername(token) }
    }

    @Test
    @DisplayName("??ï† Ï∂îÏ∂ú - ?†ÌÅ∞?êÏÑú ??ï† Î™©Î°ù Î∞òÌôò")
    fun `extractRoles - should return roles from token`() {

        val token = "valid.token"
        val expectedRoles = listOf("ROLE_USER", "ROLE_ADMIN")

        every { jwtUtil.extractRoles(token) } returns expectedRoles

        val result = authService.extractRoles(token)

        assertEquals(expectedRoles, result)
        verify(exactly = 1) { jwtUtil.extractRoles(token) }
    }
}
