package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.AIAnalysisRequest
import com.sleekydz86.backend.domain.model.AIAnalysisResult
import com.sleekydz86.backend.domain.model.TechnicalAnalysis
import com.sleekydz86.backend.infrastructure.client.PythonApiClient
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import java.time.LocalDateTime

@Service
class AIAnalysisService(
    private val pythonApiClient: PythonApiClient
) {

    fun generateAIAnalysis(request: AIAnalysisRequest): Mono<AIAnalysisResult> {
        return pythonApiClient.getAnalysis(request.symbol)
            .map { analysis ->
                val aiSummary = generateAISummary(analysis)
                val marketSentiment = determineMarketSentiment(analysis)
                val riskLevel = calculateRiskLevel(analysis)
                val recommendation = generateRecommendation(analysis)
                val confidenceScore = calculateConfidenceScore(analysis)

                AIAnalysisResult(
                    symbol = request.symbol,
                    analysisType = request.analysisType,
                    aiSummary = aiSummary,
                    technicalAnalysis = mapOf<String, Any>(
                        "rsi" to (analysis.signals.rsi ?: 0.0),
                        "macd" to (analysis.signals.macd ?: 0.0),
                        "macdSignal" to (analysis.signals.macdSignal ?: 0.0),
                        "trend" to analysis.trend,
                        "trendStrength" to analysis.trendStrength
                    ),
                    marketSentiment = marketSentiment,
                    riskLevel = riskLevel,
                    recommendation = recommendation,
                    confidenceScore = confidenceScore
                )
            }
    }

    private fun generateAISummary(analysis: TechnicalAnalysis): String {
        val trend = analysis.trend
        val signal = analysis.signals.signal
        val confidence = analysis.signals.confidence
        val rsi = analysis.signals.rsi
        val macd = analysis.signals.macd

        return when {
            trend == "bullish" && signal == "buy" -> {
                "현재 상승 추세가 강하게 나타나고 있으며, 매수 신호가 확인되었습니다. " +
                        "RSI 지표가 ${rsi?.let { r -> "%.1f".format(r) } ?: "N/A"}로 과매수 구간에 있지만 " +
                        "MACD가 ${macd?.let { m -> "%.4f".format(m) } ?: "N/A"}로 상승 모멘텀을 보이고 있습니다. " +
                        "단기적으로는 조정 가능성이 있지만 중장기적으로는 긍정적인 전망입니다."
            }
            trend == "bearish" && signal == "sell" -> {
                "현재 하락 추세가 지속되고 있으며, 매도 신호가 강하게 나타나고 있습니다. " +
                        "RSI 지표가 ${rsi?.let { r -> "%.1f".format(r) } ?: "N/A"}로 과매도 구간에 접근하고 있으며 " +
                        "MACD가 ${macd?.let { m -> "%.4f".format(m) } ?: "N/A"}로 하락 모멘텀을 보이고 있습니다. " +
                        "추가적인 하락 가능성이 높아 보이며 신중한 접근이 필요합니다."
            }
            else -> {
                "현재 중립적인 상황으로 명확한 방향성이 보이지 않습니다. " +
                        "RSI 지표가 ${rsi?.let { r -> "%.1f".format(r) } ?: "N/A"}로 중립 구간에 있으며 " +
                        "MACD가 ${macd?.let { m -> "%.4f".format(m) } ?: "N/A"}로 횡보 상태를 보이고 있습니다. " +
                        "추가적인 신호를 기다리거나 포지션 조정을 고려해볼 수 있습니다."
            }
        }
    }

    private fun determineMarketSentiment(analysis: TechnicalAnalysis): String {
        val trend = analysis.trend
        val trendStrength = analysis.trendStrength
        val confidence = analysis.signals.confidence

        return when {
            trend == "bullish" && trendStrength > 0.7 && confidence > 0.8 -> "매우 긍정적"
            trend == "bullish" && trendStrength > 0.5 -> "긍정적"
            trend == "bearish" && trendStrength > 0.7 && confidence > 0.8 -> "매우 부정적"
            trend == "bearish" && trendStrength > 0.5 -> "부정적"
            else -> "중립적"
        }
    }

    private fun calculateRiskLevel(analysis: TechnicalAnalysis): String {
        val anomalies = analysis.anomalies
        val trendStrength = analysis.trendStrength
        val confidence = analysis.signals.confidence

        val highRiskAnomalies = anomalies.count { anomaly -> anomaly.severity == "high" }
        val mediumRiskAnomalies = anomalies.count { anomaly -> anomaly.severity == "medium" }

        return when {
            highRiskAnomalies > 0 || (trendStrength > 0.8 && confidence < 0.6) -> "높음"
            mediumRiskAnomalies > 2 || (trendStrength > 0.6 && confidence < 0.7) -> "중간"
            else -> "낮음"
        }
    }

    private fun generateRecommendation(analysis: TechnicalAnalysis): String {
        val signal = analysis.signals.signal
        val confidence = analysis.signals.confidence
        val trend = analysis.trend

        return when {
            signal == "buy" && confidence > 0.8 && trend == "bullish" -> "강력 매수"
            signal == "buy" && confidence > 0.6 -> "매수"
            signal == "sell" && confidence > 0.8 && trend == "bearish" -> "강력 매도"
            signal == "sell" && confidence > 0.6 -> "매도"
            signal == "hold" && confidence > 0.7 -> "보유"
            else -> "관망"
        }
    }

    private fun calculateConfidenceScore(analysis: TechnicalAnalysis): Double {
        val baseConfidence = analysis.signals.confidence
        val trendStrength = analysis.trendStrength
        val anomalyPenalty = analysis.anomalies.size * 0.05

        return ((baseConfidence + trendStrength) / 2 - anomalyPenalty).coerceIn(0.0, 1.0)
    }
}
