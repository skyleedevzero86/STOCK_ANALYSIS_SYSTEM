package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.*
import com.sleekydz86.backend.application.mapper.UserMapper
import com.sleekydz86.backend.domain.model.User
import com.sleekydz86.backend.domain.service.AuthService
import com.sleekydz86.backend.domain.service.UserService
import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.responses.ApiResponse
import io.swagger.v3.oas.annotations.responses.ApiResponses
import io.swagger.v3.oas.annotations.tags.Tag
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/auth")
@Tag(name = "인증 API", description = "사용자 인증 및 토큰 관리 API")
class AuthController(
    private val authService: AuthService,
    private val userService: UserService
) {

    @PostMapping("/login")
    @Operation(summary = "사용자 로그인", description = "사용자명과 비밀번호로 로그인하여 JWT 토큰을 발급받습니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "로그인 성공"),
            ApiResponse(responseCode = "401", description = "인증 실패 (잘못된 사용자명 또는 비밀번호)")
        ]
    )
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
    @Operation(summary = "사용자 회원가입", description = "새로운 사용자 계정을 생성하고 JWT 토큰을 발급받습니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "회원가입 성공"),
            ApiResponse(responseCode = "400", description = "잘못된 요청 (이미 존재하는 사용자명 또는 이메일)")
        ]
    )
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
    @Operation(summary = "토큰 갱신", description = "리프레시 토큰을 사용하여 새로운 액세스 토큰을 발급받습니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "토큰 갱신 성공"),
            ApiResponse(responseCode = "401", description = "유효하지 않은 리프레시 토큰")
        ]
    )
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
    @Operation(summary = "사용자 로그아웃", description = "사용자를 로그아웃 처리합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "로그아웃 성공")
        ]
    )
    fun logout(): ResponseEntity<Map<String, String>> {
        return ResponseEntity.ok(mapOf("message" to "Logout successful"))
    }
}