package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.ApiResponse
import com.sleekydz86.backend.application.dto.ApiResponseBuilder
import com.sleekydz86.backend.application.mapper.EmailSubscriptionMapper
import com.sleekydz86.backend.domain.model.AdminLoginRequest
import com.sleekydz86.backend.domain.service.AdminService
import com.sleekydz86.backend.domain.service.EmailSubscriptionService
import com.sleekydz86.backend.domain.service.NotificationLogService
import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono

@RestController
@RequestMapping("/api/admin")
class AdminController(
    private val adminService: AdminService,
    private val emailSubscriptionService: EmailSubscriptionService,
    private val notificationLogService: NotificationLogService
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
    fun getSubscriptions(
        @RequestHeader("Authorization") token: String,
        @RequestParam(defaultValue = "0") page: Int,
        @RequestParam(defaultValue = "10") size: Int,
        @RequestParam(required = false) name: String?
    ): Mono<ApiResponse<Map<String, Any>>> {
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailSubscriptionService.getAllActiveSubscriptions(page, size, name)
                        .map { (subscriptions, total) ->
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
                                    "total" to total,
                                    "page" to page,
                                    "size" to size,
                                    "totalPages" to ((total + size - 1) / size).toInt()
                                )
                            )
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
    }

    @PutMapping("/subscriptions/{id}/consent")
    fun updateSubscriptionConsent(
        @RequestHeader("Authorization") token: String,
        @PathVariable id: Long,
        @RequestBody request: Map<String, Boolean?>
    ): Mono<ApiResponse<Map<String, Any>>> {
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailSubscriptionService.updateSubscriptionConsent(
                        id,
                        request["isEmailConsent"],
                        request["isPhoneConsent"]
                    )
                        .map { subscription ->
                            val maskedSubscription = EmailSubscriptionMapper.toMaskedSubscriptionMap(
                                subscription,
                                { email: String -> emailSubscriptionService.maskEmail(email) },
                                { phone: String? -> emailSubscriptionService.maskPhone(phone) ?: "" }
                            )
                            ApiResponseBuilder.success<Map<String, Any>>(
                                "구독자 동의 정보가 성공적으로 수정되었습니다.",
                                mapOf("subscription" to maskedSubscription) as Map<String, Any>
                            )
                        }
                        .onErrorResume { error ->
                            Mono.just(ApiResponseBuilder.failure(error.message ?: "수정에 실패했습니다.", null))
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
    }

    @PutMapping("/subscriptions/{id}/status")
    fun updateSubscriptionStatus(
        @RequestHeader("Authorization") token: String,
        @PathVariable id: Long,
        @RequestBody request: Map<String, Boolean>
    ): Mono<ApiResponse<Map<String, Any>>> {
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    val isActive = request["isActive"] ?: true
                    emailSubscriptionService.updateSubscriptionStatus(id, isActive)
                        .map { subscription ->
                            val maskedSubscription = EmailSubscriptionMapper.toMaskedSubscriptionMap(
                                subscription,
                                { email: String -> emailSubscriptionService.maskEmail(email) },
                                { phone: String? -> emailSubscriptionService.maskPhone(phone) ?: "" }
                            )
                            ApiResponseBuilder.success<Map<String, Any>>(
                                "구독자 상태가 성공적으로 수정되었습니다.",
                                mapOf("subscription" to maskedSubscription) as Map<String, Any>
                            )
                        }
                        .onErrorResume { error ->
                            Mono.just(ApiResponseBuilder.failure(error.message ?: "수정에 실패했습니다.", null))
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

    @GetMapping("/subscriptions/{id}/email-history")
    fun getEmailHistory(
        @RequestHeader("Authorization") token: String,
        @PathVariable id: Long,
        @RequestParam(defaultValue = "0") page: Int,
        @RequestParam(defaultValue = "20") size: Int
    ): Mono<ApiResponse<Map<String, Any>>> {
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailSubscriptionService.getSubscriptionById(id)
                        .flatMap { subscription ->
                            notificationLogService.getEmailHistoryByUserEmail(subscription.email, page, size)
                                .map { (logs, total) ->
                                    ApiResponseBuilder.success(
                                        "이메일 발송 이력을 성공적으로 조회했습니다.",
                                        mapOf(
                                            "logs" to logs,
                                            "total" to total,
                                            "page" to page,
                                            "size" to size,
                                            "totalPages" to ((total + size - 1) / size).toInt(),
                                            "userEmail" to subscription.email
                                        )
                                    )
                                }
                        }
                        .onErrorResume { error ->
                            Mono.just(ApiResponseBuilder.failure(error.message ?: "조회에 실패했습니다.", null))
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
    }
}