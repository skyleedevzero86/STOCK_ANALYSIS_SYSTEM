package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.ApiResponse
import com.sleekydz86.backend.application.dto.ApiResponseBuilder
import com.sleekydz86.backend.application.mapper.EmailSubscriptionMapper
import com.sleekydz86.backend.domain.model.EmailSubscription
import com.sleekydz86.backend.domain.model.EmailSubscriptionRequest
import com.sleekydz86.backend.domain.service.EmailSubscriptionService
import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.Parameter
import io.swagger.v3.oas.annotations.responses.ApiResponse as SwaggerApiResponse
import io.swagger.v3.oas.annotations.responses.ApiResponses
import io.swagger.v3.oas.annotations.tags.Tag
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono

@RestController
@RequestMapping("/api/email-subscriptions")
@Tag(name = "이메일 구독 API", description = "이메일 및 문자 알림 구독 관리 API")
class EmailSubscriptionController(
    private val emailSubscriptionService: EmailSubscriptionService
) {

    @PostMapping("/subscribe")
    @Operation(summary = "이메일 구독 등록", description = "이메일 및 문자 알림 구독을 등록합니다")
    @ApiResponses(
        SwaggerApiResponse(responseCode = "200", description = "구독이 성공적으로 등록되었습니다"),
        SwaggerApiResponse(responseCode = "400", description = "잘못된 요청 데이터입니다")
    )
    fun subscribe(@RequestBody request: EmailSubscriptionRequest): Mono<ApiResponse<Map<String, Any>>> {
        return emailSubscriptionService.subscribe(request)
            .map { subscription: EmailSubscription ->
                ApiResponseBuilder.success<Map<String, Any>>(
                    "구독이 성공적으로 등록되었습니다.",
                    mapOf<String, Any>(
                        "id" to (subscription.id ?: 0L),
                        "name" to subscription.name,
                        "email" to subscription.email,
                        "isEmailConsent" to subscription.isEmailConsent,
                        "isPhoneConsent" to subscription.isPhoneConsent
                    )
                )
            }
            .onErrorResume { error: Throwable ->
                Mono.just(ApiResponseBuilder.failure<Map<String, Any>>(error.message ?: "구독 등록에 실패했습니다.", null))
            }
    }

    @GetMapping("/list")
    @Operation(summary = "전체 구독 목록 조회", description = "모든 활성 구독 목록을 조회합니다 (개인정보 마스킹 처리)")
    @ApiResponses(
        SwaggerApiResponse(responseCode = "200", description = "성공적으로 구독 목록을 조회했습니다")
    )
    fun getAllSubscriptions(): Mono<ApiResponse<Map<String, Any>>> {
        return emailSubscriptionService.getAllActiveSubscriptions()
            .map { subscriptions: List<EmailSubscription> ->
                val maskedSubscriptions = subscriptions.map { subscription ->
                    EmailSubscriptionMapper.toMaskedSubscriptionMap(
                        subscription,
                        emailSubscriptionService::maskEmail,
                        { phone: String? -> emailSubscriptionService.maskPhone(phone) ?: "" }
                    )
                }

                ApiResponseBuilder.success<Map<String, Any>>(
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
            .map { subscriptions: List<EmailSubscription> ->
                val maskedSubscriptions = subscriptions.map { subscription ->
                    EmailSubscriptionMapper.toEmailConsentSubscriptionMap(
                        subscription,
                        { phone: String? -> emailSubscriptionService.maskPhone(phone) ?: "" }
                    )
                }

                ApiResponseBuilder.success<Map<String, Any>>(
                    "이메일 동의 구독 목록을 성공적으로 조회했습니다.",
                    mapOf(
                        "subscriptions" to maskedSubscriptions,
                        "total" to subscriptions.size
                    )
                )
            }
    }

    @GetMapping("/phone-consent")
    fun getPhoneConsentSubscriptions(): Mono<ApiResponse<Map<String, Any>>> {
        return emailSubscriptionService.getActiveSubscriptionsWithPhoneConsent()
            .map { subscriptions: List<EmailSubscription> ->
                val maskedSubscriptions = subscriptions.map { subscription ->
                    EmailSubscriptionMapper.toPhoneConsentSubscriptionMap(
                        subscription,
                        { email: String -> emailSubscriptionService.maskEmail(email) }
                    )
                }

                ApiResponseBuilder.success<Map<String, Any>>(
                    "문자 동의 구독 목록을 성공적으로 조회했습니다.",
                    mapOf(
                        "subscriptions" to maskedSubscriptions,
                        "total" to subscriptions.size
                    )
                )
            }
    }

    @PostMapping("/unsubscribe")
    @Operation(summary = "구독 해지", description = "이메일 주소를 통해 구독을 해지합니다")
    @ApiResponses(
        SwaggerApiResponse(responseCode = "200", description = "구독이 성공적으로 해지되었습니다"),
        SwaggerApiResponse(responseCode = "404", description = "구독을 찾을 수 없습니다")
    )
    fun unsubscribe(
        @Parameter(description = "구독 해지할 이메일 주소", required = true)
        @RequestParam email: String
    ): Mono<ApiResponse<Nothing?>> {
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