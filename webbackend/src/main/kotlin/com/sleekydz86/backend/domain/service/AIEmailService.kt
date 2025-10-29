package com.sleekydz86.backend.domain.service

import org.springframework.stereotype.Service
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
            .flatMap { template ->
                emailSubscriptionService.getAllActiveSubscriptions()
                    .flatMap { subscribers ->
                        aiAnalysisService.generateAIAnalysis(
                            com.stockanalysis.domain.model.AIAnalysisRequest(symbol = symbol)
                        ).flatMap { aiResult ->
                            val emailSubscribers = subscribers.filter { it.isEmailConsent }
                            val emailResults = mutableListOf<String>()

                            emailSubscribers.forEach { subscriber ->
                                val variables = createEmailVariables(subscriber, aiResult, symbol)
                                val renderedContent = emailTemplateService.renderTemplate(template, variables)

                                sendEmailViaPythonAPI(subscriber.email, template.subject, renderedContent)
                                    .subscribe { success ->
                                        if (success) {
                                            emailResults.add("O ${subscriber.email}")
                                        } else {
                                            emailResults.add("X ${subscriber.email}")
                                        }
                                    }
                            }

                            Mono.just(mapOf(
                                "template" to template.name,
                                "symbol" to symbol,
                                "totalSubscribers" to emailSubscribers.size,
                                "results" to emailResults,
                                "aiAnalysis" to aiResult.aiSummary
                            ))
                        }
                    }
            }
    }

    private fun createEmailVariables(
        subscriber: EmailSubscription,
        aiResult: AIAnalysisResult,
        symbol: String
    ): Map<String, String> {
        val now = LocalDateTime.now()
        val formatter = DateTimeFormatter.ofPattern("yyyy년 MM월 dd일")

        return mapOf(
            "name" to subscriber.name,
            "email" to subscriber.email,
            "symbol" to symbol,
            "date" to now.format(formatter),
            "ai_analysis" to aiResult.aiSummary,
            "current_price" to "N/A",
            "change_percent" to "N/A",
            "rsi" to aiResult.technicalAnalysis?.get("rsi")?.toString() ?: "N/A",
            "macd" to aiResult.technicalAnalysis?.get("macd")?.toString() ?: "N/A",
            "trend" to aiResult.technicalAnalysis?.get("trend")?.toString() ?: "N/A",
            "market_sentiment" to (aiResult.marketSentiment ?: "N/A"),
            "risk_level" to (aiResult.riskLevel ?: "N/A"),
            "recommendation" to (aiResult.recommendation ?: "N/A"),
            "confidence_score" to (aiResult.confidenceScore?.let { "%.1f".format(it * 100) } ?: "N/A")
        )
    }

    private fun sendEmailViaPythonAPI(toEmail: String, subject: String, content: String): Mono<Boolean> {
        return pythonApiClient.sendEmail(toEmail, subject, content)
    }

    fun sendBulkAIEmails(templateId: Long, symbols: List<String>): Mono<Map<String, Any>> {
        return emailTemplateService.getTemplateById(templateId)
            .flatMap { template ->
                emailSubscriptionService.getAllActiveSubscriptions()
                    .flatMap { subscribers ->
                        val emailSubscribers = subscribers.filter { it.isEmailConsent }
                        val allResults = mutableListOf<Map<String, Any>>()

                        symbols.forEach { symbol ->
                            aiAnalysisService.generateAIAnalysis(
                                com.stockanalysis.domain.model.AIAnalysisRequest(symbol = symbol)
                            ).subscribe { aiResult ->
                                emailSubscribers.forEach { subscriber ->
                                    val variables = createEmailVariables(subscriber, aiResult, symbol)
                                    val renderedContent = emailTemplateService.renderTemplate(template, variables)

                                    sendEmailViaPythonAPI(subscriber.email, template.subject, renderedContent)
                                        .subscribe { success ->
                                            allResults.add(mapOf(
                                                "symbol" to symbol,
                                                "subscriber" to subscriber.email,
                                                "success" to success,
                                                "aiSummary" to aiResult.aiSummary
                                            ))
                                        }
                                }
                            }
                        }

                        Mono.just(mapOf(
                            "template" to template.name,
                            "symbols" to symbols,
                            "totalSubscribers" to emailSubscribers.size,
                            "results" to allResults
                        ))
                    }
            }
    }
}
