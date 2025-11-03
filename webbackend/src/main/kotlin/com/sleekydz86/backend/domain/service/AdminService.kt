package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.AdminLoginRequest
import com.sleekydz86.backend.domain.model.AdminLoginResponse
import com.sleekydz86.backend.infrastructure.repository.AdminUserRepository
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import java.time.LocalDateTime
import java.util.*

@Service
class AdminService(
    private val adminUserRepository: AdminUserRepository,
    private val passwordEncoder: BCryptPasswordEncoder
) {

    fun login(request: AdminLoginRequest): Mono<AdminLoginResponse> {
        return Mono.fromCallable {
            val admin = adminUserRepository.findByEmailAndIsActive(request.email, true)
                ?: throw IllegalArgumentException("관리자 계정을 찾을 수 없습니다.")

            if (!passwordEncoder.matches(request.password, admin.passwordHash)) {
                throw IllegalArgumentException("비밀번호가 일치하지 않습니다.")
            }

            val token = Base64.getEncoder().encodeToString("${admin.email}:${System.currentTimeMillis()}".toByteArray())
            val expiresAt = LocalDateTime.now().plusHours(24)

            AdminLoginResponse(token = token, expiresAt = expiresAt)
        }
    }

    fun validateToken(token: String): Mono<Boolean> {
        return Mono.fromCallable {
            try {
                val decoded = String(Base64.getDecoder().decode(token))
                val parts = decoded.split(":")
                if (parts.size == 2) {
                    val email = parts[0]
                    val timestamp = parts[1].toLong()
                    val currentTime = System.currentTimeMillis()

                    // 24시간 유효
                    val isValid = (currentTime - timestamp) < (24 * 60 * 60 * 1000)
                    val admin = adminUserRepository.findByEmailAndIsActive(email, true)

                    isValid && admin != null
                } else {
                    false
                }
            } catch (e: Exception) {
                false
            }
        }
    }
}
