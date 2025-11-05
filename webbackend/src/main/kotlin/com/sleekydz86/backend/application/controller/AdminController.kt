package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.ApiResponse
import com.sleekydz86.backend.application.dto.ApiResponseBuilder
import com.sleekydz86.backend.application.mapper.EmailSubscriptionMapper
import com.sleekydz86.backend.domain.model.AdminLoginRequest
import com.sleekydz86.backend.domain.service.AdminService
import com.sleekydz86.backend.domain.service.EmailSubscriptionService
import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono

@RestController
@RequestMapping("/api/admin")
class AdminController(
    private val adminService: AdminService,
    private val emailSubscriptionService: EmailSubscriptionService
) {

    @PostMapping("/login")
    fun login(@RequestBody request: AdminLoginRequest): Mono<ApiResponse<Map<String, Any>>> {
        return adminService.login(request)
            .map { response ->
                ApiResponseBuilder.success(
                    "로그인이 성공했습니다.",
                    mapOf<String, Any>(
                        "token" to response.token,
                        "expiresAt" to response.expiresAt.toString()
                    )
                )
            }
            .onErrorResume { error ->
                Mono.just(ApiResponseBuilder.failure(error.message ?: "로그인에 실패했습니다.", null))
            }
    }

    @GetMapping("/subscriptions")
    fun getSubscriptions(@RequestHeader("Authorization") token: String): Mono<ApiResponse<Map<String, Any>>> {
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailSubscriptionService.getAllActiveSubscriptions()
                        .map { subscriptions ->
                            val maskedSubscriptions = subscriptions.map { subscription ->
                                EmailSubscriptionMapper.toMaskedSubscriptionMap(
                                    subscription,
                                    { email: String -> emailSubscriptionService.maskEmail(email) },
                                    { phone: String? -> emailSubscriptionService.maskPhone(phone) ?: "" }
                                )
                            }

                            ApiResponseBuilder.success(
                                "구독 목록을 성공적으로 조회했습니다.",
                                mapOf(
                                    "subscriptions" to maskedSubscriptions,
                                    "total" to subscriptions.size
                                )
                            )
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
    }

    @GetMapping("/email-consent-list")
    fun getEmailConsentList(@RequestHeader("Authorization") token: String): Mono<ApiResponse<Map<String, Any>>> {
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailSubscriptionService.getActiveSubscriptionsWithEmailConsent()
                        .map { subscriptions ->
                            val maskedSubscriptions = subscriptions.map { subscription ->
                                EmailSubscriptionMapper.toEmailConsentSubscriptionMap(
                                    subscription,
                                    { phone: String? -> emailSubscriptionService.maskPhone(phone) ?: "" }
                                )
                            }

                            ApiResponseBuilder.success(
                                "이메일 동의 구독 목록을 성공적으로 조회했습니다.",
                                mapOf(
                                    "subscriptions" to maskedSubscriptions,
                                    "total" to subscriptions.size
                                )
                            )
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
    }
}