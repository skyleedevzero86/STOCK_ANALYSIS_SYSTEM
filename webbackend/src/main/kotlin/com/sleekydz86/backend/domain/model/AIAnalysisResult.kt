package com.sleekydz86.backend.domain.model

import java.time.LocalDateTime

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

