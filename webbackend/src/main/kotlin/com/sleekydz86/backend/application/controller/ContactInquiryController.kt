package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.ApiResponse
import com.sleekydz86.backend.application.dto.ApiResponseBuilder
import com.sleekydz86.backend.domain.model.ContactInquiryRequest
import com.sleekydz86.backend.domain.model.ContactInquiryReplyRequest
import com.sleekydz86.backend.domain.service.ContactInquiryService
import com.sleekydz86.backend.domain.service.AdminService
import com.sleekydz86.backend.domain.service.NotificationLogService
import com.sleekydz86.backend.infrastructure.client.PythonApiClient
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono
import org.slf4j.LoggerFactory

@RestController
@RequestMapping("/api/contact")
class ContactInquiryController(
    private val contactInquiryService: ContactInquiryService,
    private val adminService: AdminService,
    private val notificationLogService: NotificationLogService,
    private val pythonApiClient: PythonApiClient
) {
    private val logger = LoggerFactory.getLogger(ContactInquiryController::class.java)

    @PostMapping("/inquiry")
    fun createInquiry(@RequestBody request: ContactInquiryRequest): Mono<ApiResponse<Map<String, Any>>> {
        return contactInquiryService.createInquiry(request)
            .map { inquiry ->
                ApiResponseBuilder.success(
                    "문의사항이 성공적으로 등록되었습니다.",
                    mapOf(
                        "id" to inquiry.id,
                        "name" to inquiry.name,
                        "email" to inquiry.email,
                        "subject" to inquiry.subject,
                        "createdAt" to inquiry.createdAt.toString()
                    )
                )
            }
            .onErrorResume { error ->
                Mono.just(ApiResponseBuilder.failure(error.message ?: "문의사항 등록에 실패했습니다.", null))
            }
    }

    @GetMapping("/inquiries")
    fun getInquiries(
        @RequestHeader("Authorization") authHeader: String,
        @RequestParam(defaultValue = "0") page: Int,
        @RequestParam(defaultValue = "10") size: Int,
        @RequestParam(required = false) keyword: String?,
        @RequestParam(required = false) category: String?
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
        logger.info("문의사항 목록 조회 요청 - 토큰: ${token.take(20)}...")
        
        return adminService.validateToken(token)
            .flatMap { isValid ->
                logger.info("토큰 검증 결과: $isValid")
                if (isValid) {
                    contactInquiryService.getAllInquiries(page, size, keyword, category)
                        .map { (inquiries, total) ->
                            val totalPages = if (total > 0) ((total + size - 1) / size).toInt() else 0
                            ApiResponseBuilder.success(
                                "문의사항 목록을 성공적으로 조회했습니다.",
                                mapOf(
                                    "inquiries" to inquiries.map { inquiry ->
                                        mapOf(
                                            "id" to inquiry.id,
                                            "name" to inquiry.name,
                                            "email" to inquiry.email,
                                            "phone" to inquiry.phone,
                                            "category" to inquiry.category,
                                            "subject" to inquiry.subject,
                                            "message" to inquiry.message,
                                            "isRead" to inquiry.isRead,
                                            "createdAt" to inquiry.createdAt.toString(),
                                            "updatedAt" to inquiry.updatedAt.toString()
                                        )
                                    },
                                    "total" to total,
                                    "page" to page,
                                    "size" to size,
                                    "totalPages" to totalPages
                                )
                            )
                        }
                } else {
                    logger.warn("토큰 검증 실패 - 토큰: ${token.take(20)}...")
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
    }

    @GetMapping("/inquiries/{id}")
    fun getInquiryById(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
        
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    contactInquiryService.getInquiryById(id)
                        .flatMap { inquiry ->
                            contactInquiryService.getRepliesByInquiryId(id)
                                .map { replies ->
                                    contactInquiryService.markAsRead(id)
                                        .map { updatedInquiry ->
                                            ApiResponseBuilder.success(
                                                "문의사항을 성공적으로 조회했습니다.",
                                                mapOf(
                                                    "inquiry" to mapOf(
                                                        "id" to updatedInquiry.id,
                                                        "name" to updatedInquiry.name,
                                                        "email" to updatedInquiry.email,
                                                        "phone" to updatedInquiry.phone,
                                                        "category" to updatedInquiry.category,
                                                        "subject" to updatedInquiry.subject,
                                                        "message" to updatedInquiry.message,
                                                        "isRead" to updatedInquiry.isRead,
                                                        "createdAt" to updatedInquiry.createdAt.toString(),
                                                        "updatedAt" to updatedInquiry.updatedAt.toString()
                                                    ),
                                                    "replies" to replies.map { reply ->
                                                        mapOf(
                                                            "id" to reply.id,
                                                            "inquiryId" to reply.inquiryId,
                                                            "content" to reply.content,
                                                            "createdBy" to reply.createdBy,
                                                            "createdAt" to reply.createdAt.toString()
                                                        )
                                                    }
                                                )
                                            )
                                        }
                                }
                        }
                        .flatMap { it }
                } else {
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
            .onErrorResume { error ->
                Mono.just(ApiResponseBuilder.failure(error.message ?: "문의사항 조회에 실패했습니다.", null))
            }
    }

    @DeleteMapping("/inquiries/{id}")
    fun deleteInquiry(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
        
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    contactInquiryService.deleteInquiry(id)
                        .map {
                            ApiResponseBuilder.success("문의사항이 성공적으로 삭제되었습니다.", null)
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
            .onErrorResume { error ->
                Mono.just(ApiResponseBuilder.failure(error.message ?: "문의사항 삭제에 실패했습니다.", null))
            }
    }

    @PostMapping("/inquiries/{id}/reply")
    fun addReply(
        @RequestHeader("Authorization") authHeader: String,
        @PathVariable id: Long,
        @RequestBody request: Map<String, String>
    ): Mono<ApiResponse<Map<String, Any>>> {
        val token = authHeader.removePrefix("Bearer ").trim()
        val content = request["content"] ?: ""
        val createdBy = request["createdBy"] ?: "관리자"
        
        return adminService.validateToken(token)
            .flatMap { isValid ->
                if (isValid) {
                    val replyRequest = ContactInquiryReplyRequest(
                        inquiryId = id,
                        content = content,
                        createdBy = createdBy
                    )
                    
                    contactInquiryService.addReply(replyRequest)
                        .flatMap { reply ->
                            contactInquiryService.getInquiryById(id)
                                .flatMap { inquiry ->
                                    val emailSubject = "문의사항 답변: ${inquiry.subject}"
                                    val emailBody = """
안녕하세요 ${inquiry.name}님,

문의해주신 내용에 대한 답변을 드립니다.

문의 내용:
${inquiry.message}

답변:
${reply.content}

추가 문의사항이 있으시면 언제든지 연락주시기 바랍니다.

감사합니다.
                                    """.trimIndent()

                                    pythonApiClient.sendEmail(inquiry.email, emailSubject, emailBody)
                                        .flatMap { success ->
                                            if (success) {
                                                notificationLogService.saveEmailLog(
                                                    userEmail = inquiry.email,
                                                    subject = emailSubject,
                                                    message = emailBody,
                                                    status = "sent",
                                                    source = "inquiry_reply"
                                                ).map { true }
                                            } else {
                                                notificationLogService.saveEmailLog(
                                                    userEmail = inquiry.email,
                                                    subject = emailSubject,
                                                    message = emailBody,
                                                    status = "failed",
                                                    errorMessage = "이메일 발송에 실패했습니다.",
                                                    source = "inquiry_reply"
                                                ).map { false }
                                            }
                                        }
                                        .doOnSuccess { success ->
                                            if (success) {
                                                logger.info("답변 이메일 발송 완료: ${inquiry.email}")
                                            } else {
                                                logger.error("답변 이메일 발송 실패: ${inquiry.email}")
                                            }
                                        }
                                        .doOnError { error ->
                                            logger.error("답변 이메일 발송 오류: ${inquiry.email}", error)
                                        }
                                        .onErrorReturn(false)
                                        .then(
                                            Mono.just(
                                                ApiResponseBuilder.success(
                                                    "답변이 성공적으로 등록되었습니다.",
                                                    mapOf(
                                                        "reply" to mapOf(
                                                            "id" to reply.id,
                                                            "inquiryId" to reply.inquiryId,
                                                            "content" to reply.content,
                                                            "createdBy" to reply.createdBy,
                                                            "createdAt" to reply.createdAt.toString()
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                }
                        }
                } else {
                    Mono.just(ApiResponseBuilder.failure("인증이 필요합니다.", null))
                }
            }
            .onErrorResume { error ->
                Mono.just(ApiResponseBuilder.failure(error.message ?: "답변 등록에 실패했습니다.", null))
            }
    }
}

