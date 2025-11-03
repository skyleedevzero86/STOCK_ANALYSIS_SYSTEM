package com.sleekydz86.backend.infrastructure.entity

import com.sleekydz86.backend.domain.model.AIAnalysisResult
import jakarta.persistence.*
import java.time.LocalDateTime

@Entity
@Table(name = "ai_analysis_results")
data class AIAnalysisResultEntity(
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0,
    val symbol: String,
    @Column(name = "analysis_type")
    val analysisType: String,
    @Column(name = "ai_summary", columnDefinition = "TEXT")
    val aiSummary: String,
    @Column(name = "technical_analysis", columnDefinition = "JSON")
    val technicalAnalysis: String? = null,
    @Column(name = "market_sentiment")
    val marketSentiment: String? = null,
    @Column(name = "risk_level")
    val riskLevel: String? = null,
    val recommendation: String? = null,
    @Column(name = "confidence_score")
    val confidenceScore: Double? = null,
    @Column(name = "created_at")
    val createdAt: LocalDateTime = LocalDateTime.now()
) {
    fun toDomain(): AIAnalysisResult {
        return AIAnalysisResult(
            id = this.id,
            symbol = this.symbol,
            analysisType = this.analysisType,
            aiSummary = this.aiSummary,
            technicalAnalysis = null, // JSON 파싱은 필요시 구현
            marketSentiment = this.marketSentiment,
            riskLevel = this.riskLevel,
            recommendation = this.recommendation,
            confidenceScore = this.confidenceScore,
            createdAt = this.createdAt
        )
    }

    companion object {
        fun fromDomain(domain: AIAnalysisResult): AIAnalysisResultEntity {
            return AIAnalysisResultEntity(
                id = domain.id ?: 0,
                symbol = domain.symbol,
                analysisType = domain.analysisType,
                aiSummary = domain.aiSummary,
                technicalAnalysis = null, // JSON 직렬화는 필요시 구현
                marketSentiment = domain.marketSentiment,
                riskLevel = domain.riskLevel,
                recommendation = domain.recommendation,
                confidenceScore = domain.confidenceScore,
                createdAt = domain.createdAt
            )
        }
    }
}