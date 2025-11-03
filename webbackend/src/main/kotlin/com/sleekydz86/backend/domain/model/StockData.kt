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