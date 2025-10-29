package com.sleekydz86.backend.domain.model

import java.time.LocalDateTime

data class StockData(
    val symbol: String,
    val currentPrice: Double,
    val volume: Long,
    val changePercent: Double,
    val timestamp: LocalDateTime,
    val confidenceScore: Double? = null
)

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

data class TradingSignals(
    val signal: String,
    val confidence: Double,
    val rsi: Double?,
    val macd: Double?,
    val macdSignal: Double?
)

data class Anomaly(
    val type: String,
    val severity: String,
    val message: String,
    val timestamp: LocalDateTime
)

data class HistoricalData(
    val symbol: String,
    val data: List<ChartDataPoint>,
    val period: Int
)

data class ChartDataPoint(
    val date: String,
    val close: Double,
    val volume: Long,
    val rsi: Double?,
    val macd: Double?,
    val bbUpper: Double?,
    val bbLower: Double?,
    val sma20: Double?
)

data class ChartPattern(
    val type: String,
    val confidence: Double,
    val signal: String,
    val description: String? = null
)

data class SupportResistance(
    val support: List<SupportResistanceLevel>,
    val resistance: List<SupportResistanceLevel>
)

data class SupportResistanceLevel(
    val level: Double,
    val touches: Int,
    val strength: Double
)

data class FibonacciLevels(
    val levels: Map<String, Double>,
    val nearestLevel: String,
    val distanceToNearest: Double
)