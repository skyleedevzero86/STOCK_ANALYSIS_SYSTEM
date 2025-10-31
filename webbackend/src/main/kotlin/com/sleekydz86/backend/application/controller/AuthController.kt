package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.*
import com.sleekydz86.backend.application.mapper.UserMapper
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/auth")
class AuthController(
    private val authService: AuthService,
    private val userService: UserService
) {

    @PostMapping("/login")
    fun login(@RequestBody request: LoginRequest): ResponseEntity<AuthResponse> {
        val authentication = authService.authenticate(request.username, request.password)
        val user = authentication.principal as User
        val tokens = authService.generateTokens(user)

        val response = AuthResponse(
            accessToken = tokens["access_token"]!!,
            refreshToken = tokens["refresh_token"]!!,
            tokenType = tokens["token_type"]!!,
            expiresIn = tokens["expires_in"]!!.toLong(),
            user = UserMapper.toUserInfo(user)
        )

        return ResponseEntity.ok(response)
    }

    @PostMapping("/register")
    fun register(@RequestBody request: RegisterRequest): ResponseEntity<AuthResponse> {
        if (userService.existsByUsername(request.username)) {
            return ResponseEntity.badRequest().build()
        }

        if (userService.existsByEmail(request.email)) {
            return ResponseEntity.badRequest().build()
        }

        val user = userService.createUser(
            username = request.username,
            email = request.email,
            password = request.password,
            firstName = request.firstName,
            lastName = request.lastName
        )

        val tokens = authService.generateTokens(user)

        val response = AuthResponse(
            accessToken = tokens["access_token"]!!,
            refreshToken = tokens["refresh_token"]!!,
            tokenType = tokens["token_type"]!!,
            expiresIn = tokens["expires_in"]!!.toLong(),
            user = UserMapper.toUserInfo(user)
        )

        return ResponseEntity.ok(response)
    }

    @PostMapping("/refresh")
    fun refreshToken(@RequestBody request: RefreshTokenRequest): ResponseEntity<AuthResponse> {
        val tokens = authService.refreshToken(request.refreshToken)
        val username = authService.extractUsername(tokens["access_token"]!!)
        val user = userService.findByUsername(username)!!

        val response = AuthResponse(
            accessToken = tokens["access_token"]!!,
            refreshToken = tokens["refresh_token"]!!,
            tokenType = tokens["token_type"]!!,
            expiresIn = tokens["expires_in"]!!.toLong(),
            user = UserMapper.toUserInfo(user)
        )

        return ResponseEntity.ok(response)
    }

    @PostMapping("/logout")
    fun logout(): ResponseEntity<Map<String, String>> {
        return ResponseEntity.ok(mapOf("message" to "Logout successful"))
    }
}