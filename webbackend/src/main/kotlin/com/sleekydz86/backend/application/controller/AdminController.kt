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
import org.slf4j.LoggerFactory

@RestController
@RequestMapping("/api/admin")
class AdminController(
    private val adminService: AdminService,
    private val emailSubscriptionService: EmailSubscriptionService,
    private val notificationLogService: NotificationLogService,
    private val pythonApiClient: PythonApiClient
) {
    private val logger = LoggerFactory.getLogger(AdminController::class.java)

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
        @RequestHeader("Authorization") authHeader: String,
        @RequestParam(defaultValue = "0") page: Int,
        @RequestParam(defaultValue = "10") size: Int,
        @RequestParam(required = false) name: String?
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
        logger.info("구독자 목록 조회 요청 - 토큰: ${token.take(20)}...")
        
        return adminService.validateToken(token)
            .flatMap { isValid ->
                logger.info("토큰 검증 결과: $isValid")
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
                    logger.warn("토큰 검증 실패 - 토큰: ${token.take(20)}...")
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
    }

    @PutMapping("/subscriptions/{id}/consent")
    fun updateSubscriptionConsent(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long,
        @RequestBody request: Map<String, Boolean?>
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
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
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long,
        @RequestBody request: Map<String, Boolean>
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
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
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    emailSubscriptionService.getSubscriptionById(id)
                        .map { subscription ->
                            val subscriptionMap = mapOf<String, Any>(
                                "id" to (subscription.id ?: 0L),
                                "name" to subscription.name,
                                "email" to emailSubscriptionService.maskEmail(subscription.email),
                                "phone" to (subscription.phone ?: ""),
                                "isEmailConsent" to subscription.isEmailConsent,
                                "isPhoneConsent" to subscription.isPhoneConsent,
                                "createdAt" to subscription.createdAt,
                                "isActive" to subscription.isActive
                            )
                            ApiResponseBuilder.success(
                                "구독자 정보를 성공적으로 조회했습니다.",
                                subscriptionMap
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
    fun getEmailConsentList(@RequestHeader("Authorization") authHeader: String): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
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
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long,
        @RequestParam(defaultValue = "0") page: Int,
        @RequestParam(defaultValue = "20") size: Int
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
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
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long,
        @RequestBody request: Map<String, String>
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    val toEmail = request["toEmail"] ?: ""
                    val subject = request["subject"] ?: ""
                    val body = request["body"] ?: ""
                    
                    if (toEmail.isBlank() || subject.isBlank() || body.isBlank()) {
                        return@flatMap Mono.just(ApiResponseBuilder.failure<Map<String, Any>>("이메일 주소, 제목, 내용은 필수입니다.", null))
                    }
                    
                    logger.info("수기 이메일 발송 시도: toEmail={}, subject={}", toEmail, subject)
                    
                    pythonApiClient.sendEmail(toEmail, subject, body)
                        .flatMap { success ->
                            if (success) {
                                logger.info("수기 이메일 발송 성공: toEmail={}, subject={}", toEmail, subject)
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
                                logger.error("수기 이메일 발송 실패: toEmail={}, subject={} - Python API가 false를 반환했습니다.", toEmail, subject)
                                notificationLogService.saveEmailLog(
                                    userEmail = toEmail,
                                    subject = subject,
                                    message = body,
                                    status = "failed",
                                    errorMessage = "Python API가 이메일 발송에 실패했습니다. Python API 서버 로그를 확인하세요.",
                                    source = "manual"
                                ).map {
                                    ApiResponseBuilder.failure<Map<String, Any>>(
                                        "이메일 발송에 실패했습니다. Python API 서버 로그를 확인하세요.", 
                                        null
                                    )
                                }
                            }
                        }
                        .onErrorResume { error ->
                            logger.error("수기 이메일 발송 중 예외 발생: toEmail={}, subject={}, error={}", 
                                toEmail, subject, error.message, error)
                            val errorMessage = when (error) {
                                is com.sleekydz86.backend.global.exception.ExternalApiException -> 
                                    error.message ?: "Python API 서버 오류"
                                else -> error.message ?: "이메일 발송 중 오류 발생"
                            }
                            notificationLogService.saveEmailLog(
                                userEmail = toEmail,
                                subject = subject,
                                message = body,
                                status = "failed",
                                errorMessage = errorMessage,
                                source = "manual"
                            ).map {
                                ApiResponseBuilder.failure<Map<String, Any>>(
                                    errorMessage, 
                                    null
                                )
                            }
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure<Map<String, Any>>("인증이 필요합니다.", null))
                }
            }
    }

    @GetMapping("/check-welcome-email")
    fun checkWelcomeEmailSent(@RequestParam email: String): Mono<ApiResponse<Map<String, Any>>> {
        return notificationLogService.getEmailHistoryByUserEmail(email)
            .map { logs ->
                val welcomeEmailSent = logs.any { log ->
                    val message = log["message"] as? String ?: ""
                    val notificationType = (log["notificationType"] as? String ?: "").lowercase()
                    notificationType == "email" && 
                    (message.contains("환영") || message.contains("주식 분석 시스템에 오신 것을 환영합니다"))
                }
                ApiResponseBuilder.success(
                    "환영 메일 발송 여부 확인 완료",
                    mapOf("sent" to welcomeEmailSent, "email" to email) as Map<String, Any>
                )
            }
            .onErrorResume { error ->
                Mono.just(ApiResponseBuilder.failure<Map<String, Any>>(error.message ?: "확인 실패", null))
            }
    }

    @GetMapping("/check-daily-email")
    fun checkDailyEmailSentToday(@RequestParam email: String): Mono<ApiResponse<Map<String, Any>>> {
        return notificationLogService.getEmailHistoryByUserEmail(email)
            .map { logs ->
                val today = java.time.LocalDate.now()
                val dailyEmailSentToday = logs.any { log ->
                    val sentAtStr = log["sentAt"] as? String ?: ""
                    val message = log["message"] as? String ?: ""
                    val notificationType = (log["notificationType"] as? String ?: "").lowercase()
                    
                    try {
                        val sentAt = java.time.LocalDateTime.parse(sentAtStr.substring(0, 19))
                        val sentDate = sentAt.toLocalDate()
                        notificationType == "email" && 
                        sentDate == today &&
                        (message.contains("주식 분석 리포트") || message.contains("일일 주식 분석"))
                    } catch (e: Exception) {
                        false
                    }
                }
                ApiResponseBuilder.success(
                    "일일 분석 메일 발송 여부 확인 완료",
                    mapOf("sent" to dailyEmailSentToday, "email" to email) as Map<String, Any>
                )
            }
            .onErrorResume { error ->
                Mono.just(ApiResponseBuilder.failure<Map<String, Any>>(error.message ?: "확인 실패", null))
            }
    }

    @GetMapping("/check-daily-sms")
    fun checkDailySmsSentToday(@RequestParam phone: String): Mono<ApiResponse<Map<String, Any>>> {
        return notificationLogService.getEmailHistoryByUserEmail(phone)
            .map { logs ->
                val today = java.time.LocalDate.now()
                val dailySmsSentToday = logs.any { log ->
                    val sentAtStr = log["sentAt"] as? String ?: ""
                    val message = log["message"] as? String ?: ""
                    val notificationType = (log["notificationType"] as? String ?: "").lowercase()
                    
                    try {
                        val sentAt = java.time.LocalDateTime.parse(sentAtStr.substring(0, 19))
                        val sentDate = sentAt.toLocalDate()
                        notificationType == "sms" && 
                        sentDate == today &&
                        (message.contains("주식분석") || message.contains("일일 주식 분석"))
                    } catch (e: Exception) {
                        false
                    }
                }
                ApiResponseBuilder.success(
                    "일일 분석 SMS 발송 여부 확인 완료",
                    mapOf("sent" to dailySmsSentToday, "phone" to phone) as Map<String, Any>
                )
            }
            .onErrorResume { error ->
                Mono.just(ApiResponseBuilder.failure<Map<String, Any>>(error.message ?: "확인 실패", null))
            }
    }

    @GetMapping("/check-welcome-sms")
    fun checkWelcomeSmsSent(@RequestParam phone: String): Mono<ApiResponse<Map<String, Any>>> {
        return notificationLogService.getEmailHistoryByUserEmail(phone)
            .map { logs ->
                val welcomeSmsSent = logs.any { log ->
                    val message = log["message"] as? String ?: ""
                    val notificationType = (log["notificationType"] as? String ?: "").lowercase()
                    notificationType == "sms" && 
                    (message.contains("환영") || message.contains("주식 분석 시스템에 오신 것을 환영합니다"))
                }
                ApiResponseBuilder.success(
                    "환영 SMS 발송 여부 확인 완료",
                    mapOf("sent" to welcomeSmsSent, "phone" to phone) as Map<String, Any>
                )
            }
            .onErrorResume { error ->
                Mono.just(ApiResponseBuilder.failure<Map<String, Any>>(error.message ?: "확인 실패", null))
            }
    }

    @PostMapping("/subscriptions/{id}/send-sms")
    fun sendSms(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long,
        @RequestBody request: Map<String, String>
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    val toPhone = request["toPhone"] ?: ""
                    val message = request["message"] ?: ""
                    
                    if (toPhone.isBlank() || message.isBlank()) {
                        return@flatMap Mono.just(ApiResponseBuilder.failure<Map<String, Any>>("전화번호와 메시지는 필수입니다.", null))
                    }
                    
                    emailSubscriptionService.getSubscriptionById(id)
                        .flatMap { subscription ->
                            pythonApiClient.sendSms(toPhone, message)
                                .flatMap { success ->
                                    if (success) {
                                        notificationLogService.saveEmailLog(
                                            userEmail = subscription.email,
                                            subject = null,
                                            message = message,
                                            status = "sent",
                                            source = "manual",
                                            notificationType = "sms"
                                        )
                                    .doOnSuccess { 
                                        logger.info("문자 발송 이력 저장 완료: $toPhone - sent")
                                    }
                                    .doOnError { error ->
                                        logger.error("문자 발송 이력 저장 실패: $toPhone", error)
                                    }
                                    .map {
                                        ApiResponseBuilder.success<Map<String, Any>>(
                                            "문자가 성공적으로 발송되었습니다.",
                                            mapOf("phone" to toPhone) as Map<String, Any>
                                        )
                                    }
                                    .onErrorReturn(
                                        ApiResponseBuilder.success<Map<String, Any>>(
                                            "문자가 성공적으로 발송되었습니다.",
                                            mapOf("phone" to toPhone) as Map<String, Any>
                                        )
                                    )
                            } else {
                                notificationLogService.saveEmailLog(
                                    userEmail = subscription.email,
                                    subject = null,
                                    message = message,
                                    status = "failed",
                                    errorMessage = "문자 발송에 실패했습니다.",
                                    source = "manual",
                                    notificationType = "sms"
                                )
                                    .doOnSuccess { 
                                        logger.info("문자 발송 이력 저장 완료: ${subscription.email} - failed")
                                    }
                                    .doOnError { error ->
                                        logger.error("문자 발송 이력 저장 실패: ${subscription.email}", error)
                                    }
                                    .map {
                                        ApiResponseBuilder.failure<Map<String, Any>>("문자 발송에 실패했습니다.", null)
                                    }
                                    .onErrorReturn(
                                        ApiResponseBuilder.failure<Map<String, Any>>("문자 발송에 실패했습니다.", null)
                                    )
                            }
                        }
                        .onErrorResume { error ->
                            emailSubscriptionService.getSubscriptionById(id)
                                .flatMap { subscription ->
                                    notificationLogService.saveEmailLog(
                                        userEmail = subscription.email,
                                        subject = null,
                                        message = message,
                                        status = "failed",
                                        errorMessage = error.message ?: "문자 발송 중 오류 발생",
                                        source = "manual",
                                        notificationType = "sms"
                                    )
                                        .doOnSuccess { 
                                            logger.info("문자 발송 이력 저장 완료: ${subscription.email} - failed (error)")
                                        }
                                        .doOnError { saveError ->
                                            logger.error("문자 발송 이력 저장 실패: ${subscription.email}", saveError)
                                        }
                                        .map {
                                            ApiResponseBuilder.failure<Map<String, Any>>(error.message ?: "문자 발송에 실패했습니다.", null)
                                        }
                                        .onErrorReturn(
                                            ApiResponseBuilder.failure<Map<String, Any>>(error.message ?: "문자 발송에 실패했습니다.", null)
                                        )
                                }
                                .onErrorResume { 
                                    Mono.just(ApiResponseBuilder.failure<Map<String, Any>>(error.message ?: "문자 발송에 실패했습니다.", null))
                                }
                        }
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure<Map<String, Any>>("인증이 필요합니다.", null))
                }
            }
    }

    @PostMapping("/save-notification-log")
    fun saveNotificationLog(@RequestBody request: Map<String, String>): Mono<ApiResponse<Map<String, Any>>> {
        return Mono.fromCallable {
            val userEmail = request["userEmail"] ?: ""
            val subject = request["subject"]
            val message = request["message"] ?: ""
            val status = request["status"] ?: "sent"
            val source = request["source"] ?: "airflow"
            val notificationType = request["notificationType"] ?: "email"
            val errorMessage = request["errorMessage"]
            
            notificationLogService.saveEmailLog(
                userEmail = userEmail,
                subject = subject,
                message = message,
                status = status,
                errorMessage = errorMessage,
                source = source,
                notificationType = notificationType
            ).block()
            
            ApiResponseBuilder.success(
                "알림 로그 저장 완료",
                mapOf("email" to userEmail) as Map<String, Any>
            )
        }
        .onErrorResume { error ->
            Mono.just(ApiResponseBuilder.failure<Map<String, Any>>(error.message ?: "로그 저장 실패", null))
        }
    }

    @GetMapping("/sms-config")
    fun getSmsConfig(
        @RequestHeader("Authorization") authHeader: String
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    pythonApiClient.getFromPhone()
                        .map { fromPhone ->
                            ApiResponseBuilder.success(
                                "SMS 설정을 성공적으로 조회했습니다.",
                                mapOf("fromPhone" to fromPhone) as Map<String, Any>
                            )
                        }
                        .onErrorResume { error ->
                            Mono.just(ApiResponseBuilder.failure("발신번호 조회에 실패했습니다.", null))
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
    }
}