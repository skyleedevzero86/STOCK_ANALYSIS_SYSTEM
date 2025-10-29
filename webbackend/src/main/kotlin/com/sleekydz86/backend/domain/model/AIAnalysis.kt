package com.sleekydz86.backend.domain.model

import java.time.LocalDateTime

data class EmailTemplate(
    val id: Long? = null,
    val name: String,
    val subject: String,
    val content: String,
    val isActive: Boolean = true,
    val createdAt: LocalDateTime = LocalDateTime.now(),
    val updatedAt: LocalDateTime = LocalDateTime.now()
)

data class AIAnalysisResult(
    val id: Long? = null,
    val symbol: String,
    val analysisType: String,
    val aiSummary: String,
    val technicalAnalysis: Map<String, Any>? = null,
    val marketSentiment: String? = null,
    val riskLevel: String? = null,
    val recommendation: String? = null,
    val confidenceScore: Double? = null,
    val createdAt: LocalDateTime = LocalDateTime.now()
)

data class TemplateRequest(
    val name: String,
    val subject: String,
    val content: String
)

data class AIAnalysisRequest(
    val symbol: String,
    val analysisType: String = "comprehensive"
)

data class EmailWithTemplate(
    val templateId: Long,
    val subscriberId: Long,
    val symbol: String,
    val customData: Map<String, String>? = null
)