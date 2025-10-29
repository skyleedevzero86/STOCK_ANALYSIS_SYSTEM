package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.User
import com.sleekydz86.backend.global.security.JwtUtil
import org.springframework.security.authentication.AuthenticationManager
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken
import org.springframework.security.core.Authentication
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional

@Service
@Transactional
class AuthService(
    private val userService: UserService,
    private val jwtUtil: JwtUtil,
    private val authenticationManager: AuthenticationManager
) {

    fun authenticate(username: String, password: String): Authentication {
        val authentication = UsernamePasswordAuthenticationToken(username, password)
        return authenticationManager.authenticate(authentication)
    }

    fun generateTokens(user: User): Map<String, String> {
        val roles = user.roles.map { it.name }
        val accessToken = jwtUtil.generateToken(user.username, roles)
        val refreshToken = jwtUtil.generateRefreshToken(user.username)

        return mapOf(
            "access_token" to accessToken,
            "refresh_token" to refreshToken,
            "token_type" to "Bearer",
            "expires_in" to "3600"
        )
    }

    fun refreshToken(refreshToken: String): Map<String, String> {
        if (!jwtUtil.validateToken(refreshToken)) {
            throw IllegalArgumentException("Invalid refresh token")
        }

        val username = jwtUtil.extractUsername(refreshToken)
        val user = userService.findByUsername(username)
            ?: throw IllegalArgumentException("User not found")

        return generateTokens(user)
    }

    fun validateToken(token: String): Boolean {
        return jwtUtil.validateToken(token)
    }

    fun extractUsername(token: String): String {
        return jwtUtil.extractUsername(token)
    }

    fun extractRoles(token: String): List<String> {
        return jwtUtil.extractRoles(token)
    }
}
