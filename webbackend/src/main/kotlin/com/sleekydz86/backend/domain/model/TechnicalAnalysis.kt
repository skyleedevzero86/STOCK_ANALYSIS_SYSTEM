package com.sleekydz86.backend.domain.model

import java.time.LocalDateTime

data class TechnicalAnalysis(
    val symbol: String,
    val currentPrice: Double,
    val volume: Long,
    val changePercent: Double,
    val trend: String,
    val trendStrength: Double,
    val signals: TradingSignals,
    val anomalies: List<Anomaly>,
    val timestamp: LocalDateTime,
    val marketRegime: String? = null,
    val patterns: List<ChartPattern>? = null,
    val supportResistance: SupportResistance? = null,
    val fibonacciLevels: FibonacciLevels? = null,
    val riskScore: Double? = null,
    val confidence: Double? = null
)

