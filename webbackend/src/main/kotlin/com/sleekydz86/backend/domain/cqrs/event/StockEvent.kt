package com.sleekydz86.backend.domain.cqrs.event

import java.time.LocalDateTime
import java.util.UUID

sealed class StockEvent {
    val eventId: String = UUID.randomUUID().toString()
    val timestamp: LocalDateTime = LocalDateTime.now()

    data class StockAnalyzed(
        val symbol: String,
        val analysisResult: Map<String, Any>,
        val confidence: Double
    ) : StockEvent()

    data class PriceUpdated(
        val symbol: String,
        val price: Double,
        val volume: Long,
        val changePercent: Double
    ) : StockEvent()

    data class TradingSignalGenerated(
        val symbol: String,
        val signal: String,
        val confidence: Double,
        val signalType: String
    ) : StockEvent()

    data class AnomalyDetected(
        val symbol: String,
        val anomalyType: String,
        val severity: String,
        val description: String
    ) : StockEvent()

    data class NotificationSent(
        val symbol: String,
        val message: String,
        val recipients: List<String>,
        val notificationType: String
    ) : StockEvent()

    data class MarketTrendChanged(
        val trend: String,
        val strength: Double,
        val affectedSymbols: List<String>
    ) : StockEvent()
}

data class EventMetadata(
    val eventId: String,
    val aggregateId: String,
    val version: Long,
    val timestamp: LocalDateTime,
    val eventType: String
)