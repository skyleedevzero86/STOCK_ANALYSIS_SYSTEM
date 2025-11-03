package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.ApiResponse
import com.sleekydz86.backend.application.dto.ApiResponseBuilder
import com.sleekydz86.backend.application.mapper.EmailSubscriptionMapper
import com.sleekydz86.backend.domain.model.EmailSubscriptionRequest
import com.sleekydz86.backend.domain.service.EmailSubscriptionService
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono

@RestController
@RequestMapping("/api/email-subscriptions")
class EmailSubscriptionController(
    private val emailSubscriptionService: EmailSubscriptionService
) {

    @PostMapping("/subscribe")
    fun subscribe(@RequestBody request: EmailSubscriptionRequest): Mono<ApiResponse<Map<String, Any>>> {
        return emailSubscriptionService.subscribe(request)
            .map { subscription ->
                ApiResponseBuilder.success(
                    "구독이 성공적으로 등록되었습니다.",
                    mapOf(
                        "id" to subscription.id,
                        "name" to subscription.name,
                        "email" to subscription.email,
                        "isEmailConsent" to subscription.isEmailConsent,
                        "isPhoneConsent" to subscription.isPhoneConsent
                    )
                )
            }
            .onErrorResume { error ->
                Mono.just(ApiResponseBuilder.failure(error.message ?: "구독 등록에 실패했습니다.", null))
            }
    }

    @GetMapping("/list")
    fun getAllSubscriptions(): Mono<ApiResponse<Map<String, Any>>> {
        return emailSubscriptionService.getAllActiveSubscriptions()
            .map { subscriptions ->
                val maskedSubscriptions = subscriptions.map { subscription ->
                    EmailSubscriptionMapper.toMaskedSubscriptionMap(
                        subscription,
                        emailSubscriptionService::maskEmail,
                        emailSubscriptionService::maskPhone
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
    }

    @GetMapping("/email-consent")
    fun getEmailConsentSubscriptions(): Mono<ApiResponse<Map<String, Any>>> {
        return emailSubscriptionService.getActiveSubscriptionsWithEmailConsent()
            .map { subscriptions ->
                val maskedSubscriptions = subscriptions.map { subscription ->
                    EmailSubscriptionMapper.toEmailConsentSubscriptionMap(
                        subscription,
                        emailSubscriptionService::maskPhone
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
    }

    @PostMapping("/unsubscribe")
    fun unsubscribe(@RequestParam email: String): Mono<ApiResponse<Nothing?>> {
        return emailSubscriptionService.unsubscribe(email)
            .map { success ->
                if (success) {
                    ApiResponseBuilder.success("구독이 성공적으로 해지되었습니다.", null)
                } else {
                    ApiResponseBuilder.failure("구독을 찾을 수 없습니다.", null)
                }
            }
    }
}