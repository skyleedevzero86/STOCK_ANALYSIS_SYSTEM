package com.sleekydz86.backend.domain.cqrs.query

import java.time.LocalDateTime

sealed class StockQuery {
    data class GetStockAnalysis(val symbol: String) : StockQuery()
    data class GetRealtimeData(val symbol: String) : StockQuery()
    data class GetHistoricalData(val symbol: String, val days: Int = 30) : StockQuery()
    data class GetAllAnalysis(val symbols: List<String>? = null) : StockQuery()
    data class GetTradingSignals(val symbol: String) : StockQuery()
    data class GetAnomalies(val symbol: String, val fromDate: LocalDateTime? = null) : StockQuery()
    object GetAvailableSymbols : StockQuery()
    data class GetMarketTrend(val timeframe: String = "daily") : StockQuery()
}