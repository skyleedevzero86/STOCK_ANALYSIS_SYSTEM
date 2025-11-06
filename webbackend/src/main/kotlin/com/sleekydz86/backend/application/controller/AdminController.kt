package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.ApiResponse
import com.sleekydz86.backend.application.dto.ApiResponseBuilder
import com.sleekydz86.backend.application.mapper.EmailSubscriptionMapper
import com.sleekydz86.backend.domain.model.AdminLoginRequest
import com.sleekydz86.backend.domain.service.AdminService
import com.sleekydz86.backend.domain.service.EmailSubscriptionService
import com.sleekydz86.backend.domain.service.NotificationLogService
import com.sleekydz86.backend.infrastructure.client.PythonApiClient
import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono

@RestController
@RequestMapping("/api/admin")
class AdminController(
    private val adminService: AdminService,
    private val emailSubscriptionService: EmailSubscriptionService,
    private val notificationLogService: NotificationLogService,
    private val pythonApiClient: PythonApiClient
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

    @GetMapping("/subscriptions/{id}")
    fun getSubscription(
        @RequestHeader("Authorization") token: String,
        @PathVariable id: Long
    ): Mono<ApiResponse<Map<String, Any>>> {
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailSubscriptionService.getSubscriptionById(id)
                        .map { subscription ->
                            val maskedSubscription = EmailSubscriptionMapper.toMaskedSubscriptionMap(
                                subscription,
                                { email: String -> subscription.email },
                                { phone: String? -> emailSubscriptionService.maskPhone(phone) ?: "" }
                            )
                            ApiResponseBuilder.success(
                                "구독자 정보를 성공적으로 조회했습니다.",
                                maskedSubscription
                            )
                        }
                        .onErrorResume { error ->
                            Mono.just(ApiResponseBuilder.failure(error.message ?: "조회에 실패했습니다.", null))
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

    @PostMapping("/subscriptions/{id}/send-email")
    fun sendEmail(
        @RequestHeader("Authorization") token: String,
        @PathVariable id: Long,
        @RequestBody request: Map<String, String>
    ): Mono<ApiResponse<Map<String, Any>>> {
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    val toEmail = request["toEmail"] ?: ""
                    val subject = request["subject"] ?: ""
                    val body = request["body"] ?: ""
                    
                    if (toEmail.isBlank() || subject.isBlank() || body.isBlank()) {
                        return@flatMap Mono.just(ApiResponseBuilder.failure<Map<String, Any>>("이메일 주소, 제목, 내용은 필수입니다.", null))
                    }
                    
                    pythonApiClient.sendEmail(toEmail, subject, body)
                        .flatMap { success ->
                            if (success) {
                                notificationLogService.saveEmailLog(
                                    userEmail = toEmail,
                                    subject = subject,
                                    message = body,
                                    status = "sent",
                                    source = "manual"
                                ).map {
                                    ApiResponseBuilder.success<Map<String, Any>>(
                                        "이메일이 성공적으로 발송되었습니다.",
                                        mapOf("email" to toEmail) as Map<String, Any>
                                    )
                                }
                            } else {
                                notificationLogService.saveEmailLog(
                                    userEmail = toEmail,
                                    subject = subject,
                                    message = body,
                                    status = "failed",
                                    errorMessage = "이메일 발송에 실패했습니다.",
                                    source = "manual"
                                ).map {
                                    ApiResponseBuilder.failure<Map<String, Any>>("이메일 발송에 실패했습니다.", null)
                                }
                            }
                        }
                        .onErrorResume { error ->
                            notificationLogService.saveEmailLog(
                                userEmail = toEmail,
                                subject = subject,
                                message = body,
                                status = "failed",
                                errorMessage = error.message ?: "이메일 발송 중 오류 발생",
                                source = "manual"
                            ).map {
                                ApiResponseBuilder.failure<Map<String, Any>>(error.message ?: "이메일 발송에 실패했습니다.", null)
                            }
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure<Map<String, Any>>("인증이 필요합니다.", null))
                }
            }
    }

    @PostMapping("/subscriptions/{id}/send-sms")
    fun sendSms(
        @RequestHeader("Authorization") token: String,
        @PathVariable id: Long,
        @RequestBody request: Map<String, String>
    ): Mono<ApiResponse<Map<String, Any>>> {
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    val toPhone = request["toPhone"] ?: ""
                    val message = request["message"] ?: ""
                    val fromPhone = pythonApiClient.getFromPhone()
                    
                    if (toPhone.isBlank() || message.isBlank()) {
                        return@flatMap Mono.just(ApiResponseBuilder.failure<Map<String, Any>>("전화번호와 메시지는 필수입니다.", null))
                    }
                    
                    if (fromPhone.isBlank()) {
                        return@flatMap Mono.just(ApiResponseBuilder.failure<Map<String, Any>>("발신번호가 설정되지 않았습니다. 환경 변수 SOLAPI_FROM_PHONE을 설정해주세요.", null))
                    }
                    
                    pythonApiClient.sendSms(fromPhone, toPhone, message)
                        .flatMap { success ->
                            if (success) {
                                notificationLogService.saveEmailLog(
                                    userEmail = toPhone,
                                    subject = null,
                                    message = message,
                                    status = "sent",
                                    source = "manual",
                                    notificationType = "sms"
                                ).map {
                                    ApiResponseBuilder.success<Map<String, Any>>(
                                        "문자가 성공적으로 발송되었습니다.",
                                        mapOf("phone" to toPhone) as Map<String, Any>
                                    )
                                }
                            } else {
                                notificationLogService.saveEmailLog(
                                    userEmail = toPhone,
                                    subject = null,
                                    message = message,
                                    status = "failed",
                                    errorMessage = "문자 발송에 실패했습니다.",
                                    source = "manual",
                                    notificationType = "sms"
                                ).map {
                                    ApiResponseBuilder.failure<Map<String, Any>>("문자 발송에 실패했습니다.", null)
                                }
                            }
                        }
                        .onErrorResume { error ->
                            notificationLogService.saveEmailLog(
                                userEmail = toPhone,
                                subject = null,
                                message = message,
                                status = "failed",
                                errorMessage = error.message ?: "문자 발송 중 오류 발생",
                                source = "manual",
                                notificationType = "sms"
                            ).map {
                                ApiResponseBuilder.failure<Map<String, Any>>(error.message ?: "문자 발송에 실패했습니다.", null)
                            }
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure<Map<String, Any>>("인증이 필요합니다.", null))
                }
            }
    }

    @GetMapping("/sms-config")
    fun getSmsConfig(
        @RequestHeader("Authorization") token: String
    ): Mono<ApiResponse<Map<String, Any>>> {
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    Mono.just(ApiResponseBuilder.success(
                        "SMS 설정을 성공적으로 조회했습니다.",
                        mapOf("fromPhone" to pythonApiClient.getFromPhone()) as Map<String, Any>
                    ))
                } else {
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
    }
}