package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.AIAnalysisRequest
import com.sleekydz86.backend.domain.model.AIAnalysisResult
import com.sleekydz86.backend.domain.model.EmailSubscription
import com.sleekydz86.backend.domain.model.EmailTemplate
import com.sleekydz86.backend.infrastructure.client.PythonApiClient
import org.slf4j.LoggerFactory
import org.springframework.stereotype.Service
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

@Service
class AIEmailService(
    private val emailTemplateService: EmailTemplateService,
    private val emailSubscriptionService: EmailSubscriptionService,
    private val aiAnalysisService: AIAnalysisService,
    private val pythonApiClient: PythonApiClient,
    private val notificationLogService: NotificationLogService
) {
    private val logger = LoggerFactory.getLogger(AIEmailService::class.java)

    fun sendAIEmailToSubscribers(templateId: Long, symbol: String): Mono<Map<String, Any>> {
        logger.info("AI 이메일 발송 시작: templateId={}, symbol={}", templateId, symbol)
        return emailTemplateService.getTemplateById(templateId)
            .doOnNext { template -> logger.info("템플릿 조회 성공: templateId={}, name={}", templateId, template.name) }
            .doOnError { error -> logger.error("템플릿 조회 실패: templateId={}, error={}", templateId, error.message, error) }
            .flatMap { template: EmailTemplate ->
                emailSubscriptionService.getAllActiveSubscriptions()
                    .doOnNext { subscribers -> logger.info("구독자 조회 성공: count={}", subscribers.size) }
                    .doOnError { error -> logger.error("구독자 조회 실패: error={}", error.message, error) }
                    .flatMap { subscribers: List<EmailSubscription> ->
                        logger.info("AI 분석 생성 시작: symbol={}", symbol)
                        aiAnalysisService.generateAIAnalysis(
                            AIAnalysisRequest(symbol = symbol)
                        )
                        .doOnNext { aiResult -> logger.info("AI 분석 생성 성공: symbol={}, summary={}", symbol, aiResult.aiSummary?.take(50)) }
                        .doOnError { error -> logger.error("AI 분석 생성 실패: symbol={}, error={}", symbol, error.message, error) }
                        .switchIfEmpty(
                            Mono.defer {
                                logger.warn("AI 분석 생성: 빈 결과 반환, 기본값 사용: symbol={}", symbol)
                                Mono.just(
                                    AIAnalysisResult(
                                        symbol = symbol,
                                        analysisType = "default",
                                        aiSummary = "분석 데이터를 가져올 수 없습니다.",
                                        technicalAnalysis = emptyMap(),
                                        marketSentiment = "알 수 없음",
                                        riskLevel = "알 수 없음",
                                        recommendation = "데이터 부족",
                                        confidenceScore = 0.0
                                    )
                                )
                            }
                        )
                        .onErrorResume { error ->
                            logger.error("AI 분석 생성 중 예외 발생: symbol={}, error={}", symbol, error.message, error)
                            Mono.just(
                                AIAnalysisResult(
                                    symbol = symbol,
                                    analysisType = "error",
                                    aiSummary = "분석 생성 중 오류 발생: ${error.message}",
                                    technicalAnalysis = emptyMap(),
                                    marketSentiment = "알 수 없음",
                                    riskLevel = "알 수 없음",
                                    recommendation = "오류 발생",
                                    confidenceScore = 0.0
                                )
                            )
                        }
                        .flatMap { aiResult: AIAnalysisResult ->
                            val emailSubscribers = subscribers.filter { subscription: EmailSubscription -> subscription.isEmailConsent }
                            logger.info("이메일 동의 구독자 수: total={}, emailConsent={}", subscribers.size, emailSubscribers.size)
                            
                            if (emailSubscribers.isEmpty()) {
                                logger.warn("이메일 동의한 구독자가 없음: templateId={}, symbol={}", templateId, symbol)
                                return@flatMap Mono.just(mapOf(
                                    "template" to template.name,
                                    "symbol" to symbol,
                                    "totalSubscribers" to 0,
                                    "results" to emptyList<String>(),
                                    "aiAnalysis" to (aiResult.aiSummary ?: "분석 결과 없음"),
                                    "message" to "이메일 동의한 구독자가 없습니다."
                                ))
                            }
                            
                            logger.info("이메일 발송 시작: count={}", emailSubscribers.size)
                            Flux.fromIterable(emailSubscribers)
                                .flatMap { subscriber: EmailSubscription ->
                                    val variables = createEmailVariables(subscriber, aiResult, symbol)
                                    val renderedContent = buildEmailContent(template, variables, aiResult)
                                    
                                    logger.info("이메일 발송 시도: email={}, subject={}", subscriber.email, template.subject)
                                    sendEmailViaPythonAPI(subscriber.email, template.subject, renderedContent)
                                        .doOnNext { success -> 
                                            logger.info("이메일 발송 결과 수신: email={}, success={}", subscriber.email, success)
                                        }
                                        .doOnError { error ->
                                            logger.error("이메일 발송 API 호출 오류: email={}, error={}, errorType={}", 
                                                subscriber.email, error.message, error.javaClass.simpleName, error)
                                        }
                                        .flatMap { success: Boolean ->
                                            logger.info("이메일 발송 결과 처리 시작: email={}, success={}", subscriber.email, success)
                                            val status = if (success) "sent" else "failed"
                                            val errorMsg = if (success) null else "이메일 발송에 실패했습니다."
                                            
                                            notificationLogService.saveEmailLog(
                                                userEmail = subscriber.email,
                                                subject = template.subject,
                                                message = renderedContent,
                                                status = status,
                                                errorMessage = errorMsg,
                                                source = "ai_email",
                                                notificationType = "email",
                                                symbol = symbol
                                            )
                                            .doOnSuccess {
                                                if (success) {
                                                    logger.info("이메일 발송 성공 및 로그 저장 완료: email={}", subscriber.email)
                                                } else {
                                                    logger.warn("이메일 발송 실패 및 로그 저장 완료: email={}", subscriber.email)
                                                }
                                            }
                                            .doOnError { logError ->
                                                logger.error("이메일 발송 로그 저장 실패: email={}, error={}", subscriber.email, logError.message)
                                            }
                                            .map {
                                                if (success) {
                                                    "성공 ${subscriber.email}"
                                                } else {
                                                    "실패 ${subscriber.email}"
                                                }
                                            }
                                        }
                                        .onErrorResume { error ->
                                            logger.error("이메일 발송 오류: email={}, error={}, errorType={}", 
                                                subscriber.email, error.message, error.javaClass.simpleName, error)
                                            notificationLogService.saveEmailLog(
                                                userEmail = subscriber.email,
                                                subject = template.subject,
                                                message = renderedContent,
                                                status = "failed",
                                                errorMessage = error.message,
                                                source = "ai_email",
                                                notificationType = "email",
                                                symbol = symbol
                                            )
                                            .doOnError { logError ->
                                                logger.error("이메일 발송 오류 로그 저장 실패: email={}, error={}", subscriber.email, logError.message)
                                            }
                                            .map {
                                                "오류 ${subscriber.email}: ${error.message}"
                                            }
                                        }
                                }
                                .collectList()
                                .map { results: List<String> ->
                                    logger.info("이메일 발송 완료: templateId={}, symbol={}, total={}, success={}", 
                                        templateId, symbol, emailSubscribers.size, results.count { it.startsWith("성공") })
                                    mapOf(
                                        "template" to template.name,
                                        "symbol" to symbol,
                                        "totalSubscribers" to emailSubscribers.size,
                                        "results" to results,
                                        "aiAnalysis" to (aiResult.aiSummary ?: "분석 결과 없음")
                                    )
                                }
                                .onErrorResume { error ->
                                    logger.error("이메일 발송 수집 중 오류: templateId={}, symbol={}, error={}", templateId, symbol, error.message, error)
                                    Mono.just(mapOf(
                                        "template" to template.name,
                                        "symbol" to symbol,
                                        "totalSubscribers" to emailSubscribers.size,
                                        "results" to emptyList<String>(),
                                        "aiAnalysis" to (aiResult.aiSummary ?: "분석 결과 없음"),
                                        "error" to (error.message ?: "이메일 발송 중 오류 발생"),
                                        "errorType" to error.javaClass.simpleName
                                    ))
                                }
                        }
                    }
            }
            .onErrorResume { error ->
                logger.error("AI 이메일 발송 중 오류: templateId={}, symbol={}, error={}", templateId, symbol, error.message, error)
                val errorMessage = when {
                    error.message?.contains("Template not found") == true -> "템플릿을 찾을 수 없습니다."
                    error.message?.contains("구독자") == true -> "구독자 조회 중 오류 발생"
                    error.message?.contains("분석") == true -> "AI 분석 생성 중 오류 발생"
                    else -> error.message ?: "알 수 없는 오류"
                }
                Mono.just(mapOf(
                    "template" to "알 수 없음",
                    "symbol" to symbol,
                    "totalSubscribers" to 0,
                    "results" to emptyList<String>(),
                    "aiAnalysis" to "오류 발생",
                    "error" to errorMessage,
                    "errorType" to error.javaClass.simpleName
                ))
            }
            .doOnNext { result -> logger.info("AI 이메일 발송 완료: templateId={}, symbol={}, totalSubscribers={}", 
                templateId, symbol, result["totalSubscribers"]) }
            .doOnError { error -> logger.error("AI 이메일 발송 최종 오류: templateId={}, symbol={}, error={}", 
                templateId, symbol, error.message, error) }
    }

    private fun createEmailVariables(
        subscriber: EmailSubscription,
        aiResult: AIAnalysisResult,
        symbol: String
    ): Map<String, String> {
        val now = LocalDateTime.now()
        val formatter = DateTimeFormatter.ofPattern("yyyy년 MM월 dd일")

        return mapOf<String, String>(
            "name" to subscriber.name,
            "email" to subscriber.email,
            "symbol" to symbol,
            "date" to now.format(formatter),
            "ai_analysis" to aiResult.aiSummary,
            "current_price" to "N/A",
            "change_percent" to "N/A",
            "rsi" to (aiResult.technicalAnalysis?.get("rsi")?.toString() ?: "N/A"),
            "macd" to (aiResult.technicalAnalysis?.get("macd")?.toString() ?: "N/A"),
            "trend" to (aiResult.technicalAnalysis?.get("trend")?.toString() ?: "N/A"),
            "market_sentiment" to (aiResult.marketSentiment ?: "N/A"),
            "risk_level" to (aiResult.riskLevel ?: "N/A"),
            "recommendation" to (aiResult.recommendation ?: "N/A"),
            "confidence_score" to (aiResult.confidenceScore?.let { score: Double -> "%.1f".format(score * 100) } ?: "N/A")
        )
    }

    private fun buildEmailContent(template: EmailTemplate, variables: Map<String, String>, aiResult: AIAnalysisResult): String {
        var templateContent = template.content
        
        val personalizedContent = personalizeTemplateContent(templateContent, variables)
        
        val aiAnalysisSection = buildAIAnalysisSection(aiResult, variables)
        
        return "$personalizedContent\n\n$aiAnalysisSection"
    }
    
    private fun personalizeTemplateContent(content: String, variables: Map<String, String>): String {
        var personalized = content
        
        val name = variables["name"] ?: "고객"
        val symbol = variables["symbol"] ?: ""
        val date = variables["date"] ?: ""
        
        personalized = personalized.replace("{name}", name)
        personalized = personalized.replace("{email}", variables["email"] ?: "")
        personalized = personalized.replace("{symbol}", symbol)
        personalized = personalized.replace("{date}", date)
        
        personalized = personalized.replace("{ai_analysis}", "")
        personalized = personalized.replace("{current_price}", variables["current_price"] ?: "")
        personalized = personalized.replace("{change_percent}", variables["change_percent"] ?: "")
        personalized = personalized.replace("{rsi}", variables["rsi"] ?: "")
        personalized = personalized.replace("{macd}", variables["macd"] ?: "")
        personalized = personalized.replace("{trend}", variables["trend"] ?: "")
        personalized = personalized.replace("{market_sentiment}", variables["market_sentiment"] ?: "")
        personalized = personalized.replace("{risk_level}", variables["risk_level"] ?: "")
        personalized = personalized.replace("{recommendation}", variables["recommendation"] ?: "")
        personalized = personalized.replace("{confidence_score}", variables["confidence_score"] ?: "")
        
        return personalized.trim()
    }
    
    private fun buildAIAnalysisSection(aiResult: AIAnalysisResult, variables: Map<String, String>): String {
        val sb = StringBuilder()
        sb.append("# 주식 분석 내용\n\n")
        
        if (aiResult.aiSummary != null && aiResult.aiSummary.isNotBlank()) {
            sb.append(aiResult.aiSummary)
            sb.append("\n\n")
        }
        
        val technicalAnalysis = aiResult.technicalAnalysis
        if (technicalAnalysis != null && technicalAnalysis.isNotEmpty()) {
            sb.append("## 기술적 분석\n\n")
            technicalAnalysis.forEach { (key, value) ->
                sb.append("- $key: $value\n")
            }
            sb.append("\n")
        }
        
        val symbol = variables["symbol"] ?: ""
        if (symbol.isNotBlank()) {
            sb.append("**종목**: $symbol\n")
        }
        
        val date = variables["date"] ?: ""
        if (date.isNotBlank()) {
            sb.append("**분석 일자**: $date\n")
        }
        
        if (aiResult.marketSentiment != null && aiResult.marketSentiment.isNotBlank()) {
            sb.append("**시장 심리**: ${aiResult.marketSentiment}\n")
        }
        if (aiResult.riskLevel != null && aiResult.riskLevel.isNotBlank()) {
            sb.append("**리스크 레벨**: ${aiResult.riskLevel}\n")
        }
        if (aiResult.recommendation != null && aiResult.recommendation.isNotBlank()) {
            sb.append("**투자 추천**: ${aiResult.recommendation}\n")
        }
        if (aiResult.confidenceScore != null) {
            sb.append("**신뢰도**: ${"%.1f".format(aiResult.confidenceScore * 100)}%\n")
        }
        
        return sb.toString().trim()
    }

    private fun sendEmailViaPythonAPI(toEmail: String, subject: String, content: String): Mono<Boolean> {
        return pythonApiClient.sendEmail(toEmail, subject, content)
    }

    fun sendBulkAIEmails(templateId: Long, symbols: List<String>): Mono<Map<String, Any>> {
        return emailTemplateService.getTemplateById(templateId)
            .flatMap { template: EmailTemplate ->
                emailSubscriptionService.getAllActiveSubscriptions()
                    .flatMap { subscribers: List<EmailSubscription> ->
                        val emailSubscribers = subscribers.filter { subscription: EmailSubscription -> subscription.isEmailConsent }
                        
                        Flux.fromIterable(symbols)
                            .flatMap { symbol: String ->
                                aiAnalysisService.generateAIAnalysis(
                                    AIAnalysisRequest(symbol = symbol)
                                ).flatMapMany { aiResult: AIAnalysisResult ->
                                    Flux.fromIterable(emailSubscribers)
                                        .flatMap { subscriber: EmailSubscription ->
                                            val variables = createEmailVariables(subscriber, aiResult, symbol)
                                            val renderedContent = buildEmailContent(template, variables, aiResult)
                                            
                                            sendEmailViaPythonAPI(subscriber.email, template.subject, renderedContent)
                                                .flatMap { success: Boolean ->
                                                    val status = if (success) "sent" else "failed"
                                                    val errorMsg = if (success) null else "이메일 발송에 실패했습니다."
                                                    
                                                    notificationLogService.saveEmailLog(
                                                        userEmail = subscriber.email,
                                                        subject = template.subject,
                                                        message = renderedContent,
                                                        status = status,
                                                        errorMessage = errorMsg,
                                                        source = "ai_email_bulk",
                                                        notificationType = "email",
                                                        symbol = symbol
                                                    )
                                                    .doOnError { logError ->
                                                        logger.error("대량 이메일 발송 로그 저장 실패: email={}, error={}", subscriber.email, logError.message)
                                                    }
                                                    .map {
                                                        mapOf(
                                                            "symbol" to symbol,
                                                            "subscriber" to subscriber.email,
                                                            "success" to success,
                                                            "aiSummary" to aiResult.aiSummary
                                                        )
                                                    }
                                                }
                                                .onErrorResume { error ->
                                                    logger.error("대량 이메일 발송 오류: email={}, error={}", subscriber.email, error.message, error)
                                                    val errorMessage = error.message ?: "알 수 없는 오류"
                                                    notificationLogService.saveEmailLog(
                                                        userEmail = subscriber.email,
                                                        subject = template.subject,
                                                        message = renderedContent,
                                                        status = "failed",
                                                        errorMessage = errorMessage,
                                                        source = "ai_email_bulk",
                                                        notificationType = "email",
                                                        symbol = symbol
                                                    )
                                                    .doOnError { logError ->
                                                        logger.error("대량 이메일 발송 오류 로그 저장 실패: email={}, error={}", subscriber.email, logError.message)
                                                    }
                                                    .map {
                                                        mapOf<String, Any>(
                                                            "symbol" to symbol,
                                                            "subscriber" to subscriber.email,
                                                            "success" to false,
                                                            "aiSummary" to (aiResult.aiSummary ?: ""),
                                                            "error" to errorMessage
                                                        )
                                                    }
                                                }
                                        }
                                }
                            }
                            .collectList()
                            .map { allResults: List<Map<String, Any>> ->
                                mapOf(
                                    "template" to template.name,
                                    "symbols" to symbols,
                                    "totalSubscribers" to emailSubscribers.size,
                                    "results" to allResults
                                )
                            }
                    }
            }
    }
}
