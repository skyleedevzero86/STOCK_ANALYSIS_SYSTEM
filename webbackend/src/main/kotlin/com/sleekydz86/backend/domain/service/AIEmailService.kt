package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.AIAnalysisRequest
import com.sleekydz86.backend.domain.model.AIAnalysisResult
import com.sleekydz86.backend.domain.model.EmailSubscription
import com.sleekydz86.backend.domain.model.EmailTemplate
import com.sleekydz86.backend.infrastructure.client.PythonApiClient
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
    private val pythonApiClient: PythonApiClient
) {

    fun sendAIEmailToSubscribers(templateId: Long, symbol: String): Mono<Map<String, Any>> {
        return emailTemplateService.getTemplateById(templateId)
            .flatMap { template: EmailTemplate ->
                emailSubscriptionService.getAllActiveSubscriptions()
                    .flatMap { subscribers: List<EmailSubscription> ->
                        aiAnalysisService.generateAIAnalysis(
                            AIAnalysisRequest(symbol = symbol)
                        ).flatMap { aiResult: AIAnalysisResult ->
                            val emailSubscribers = subscribers.filter { subscription: EmailSubscription -> subscription.isEmailConsent }
                            
                            if (emailSubscribers.isEmpty()) {
                                return@flatMap Mono.just(mapOf(
                                    "template" to template.name,
                                    "symbol" to symbol,
                                    "totalSubscribers" to 0,
                                    "results" to emptyList<String>(),
                                    "aiAnalysis" to (aiResult.aiSummary ?: "분석 결과 없음"),
                                    "message" to "이메일 동의한 구독자가 없습니다."
                                ))
                            }
                            
                            Flux.fromIterable(emailSubscribers)
                                .flatMap { subscriber: EmailSubscription ->
                                    val variables = createEmailVariables(subscriber, aiResult, symbol)
                                    val renderedContent = buildEmailContent(template, variables, aiResult)
                                    
                                    sendEmailViaPythonAPI(subscriber.email, template.subject, renderedContent)
                                        .map { success: Boolean ->
                                            if (success) {
                                                "성공 ${subscriber.email}"
                                            } else {
                                                "실패 ${subscriber.email}"
                                            }
                                        }
                                        .onErrorReturn("오류 ${subscriber.email}")
                                }
                                .collectList()
                                .map { results: List<String> ->
                                    mapOf(
                                        "template" to template.name,
                                        "symbol" to symbol,
                                        "totalSubscribers" to emailSubscribers.size,
                                        "results" to results,
                                        "aiAnalysis" to (aiResult.aiSummary ?: "분석 결과 없음")
                                    )
                                }
                        }
                        .onErrorResume { error ->
                            Mono.just(mapOf(
                                "template" to template.name,
                                "symbol" to symbol,
                                "totalSubscribers" to 0,
                                "results" to emptyList<String>(),
                                "aiAnalysis" to "분석 생성 중 오류 발생",
                                "error" to (error.message ?: "알 수 없는 오류")
                            ))
                        }
                    }
                    .onErrorResume { error ->
                        Mono.just(mapOf(
                            "template" to "알 수 없음",
                            "symbol" to symbol,
                            "totalSubscribers" to 0,
                            "results" to emptyList<String>(),
                            "aiAnalysis" to "구독자 조회 중 오류 발생",
                            "error" to (error.message ?: "알 수 없는 오류")
                        ))
                    }
            }
            .onErrorResume { error ->
                Mono.just(mapOf(
                    "template" to "알 수 없음",
                    "symbol" to symbol,
                    "totalSubscribers" to 0,
                    "results" to emptyList<String>(),
                    "aiAnalysis" to "템플릿 조회 중 오류 발생",
                    "error" to (error.message ?: "알 수 없는 오류")
                ))
            }
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
                                                .map { success: Boolean ->
                                                    mapOf(
                                                        "symbol" to symbol,
                                                        "subscriber" to subscriber.email,
                                                        "success" to success,
                                                        "aiSummary" to aiResult.aiSummary
                                                    )
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
