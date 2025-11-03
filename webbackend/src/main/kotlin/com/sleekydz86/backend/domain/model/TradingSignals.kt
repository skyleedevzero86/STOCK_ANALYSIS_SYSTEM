package com.sleekydz86.backend.domain.model

data class TradingSignals(
    val signal: String,
    val confidence: Double,
    val rsi: Double?,
    val macd: Double?,
    val macdSignal: Double?
)

