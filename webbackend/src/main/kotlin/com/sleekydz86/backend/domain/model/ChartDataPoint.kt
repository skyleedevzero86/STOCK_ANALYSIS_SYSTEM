package com.sleekydz86.backend.domain.model

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

