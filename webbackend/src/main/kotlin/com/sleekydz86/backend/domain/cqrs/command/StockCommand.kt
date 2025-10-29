package com.sleekydz86.backend.domain.cqrs.command

import java.time.LocalDateTime

sealed class StockCommand {
    data class AnalyzeStock(val symbol: String, val analysisType: String = "comprehensive") : StockCommand()
    data class UpdateStockPrice(val symbol: String, val price: Double, val volume: Long, val timestamp: LocalDateTime) : StockCommand()
    data class GenerateTradingSignal(val symbol: String, val signalType: String) : StockCommand()
    data class ProcessAnomaly(val symbol: String, val anomalyType: String, val severity: String) : StockCommand()
    data class SendNotification(val symbol: String, val message: String, val recipients: List<String>) : StockCommand()
}

data class CommandResult(
    val success: Boolean,
    val message: String,
    val data: Any? = null,
    val timestamp: LocalDateTime = LocalDateTime.now()
)