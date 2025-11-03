package com.sleekydz86.backend.domain.model

data class HistoricalData(
    val symbol: String,
    val data: List<ChartDataPoint>,
    val period: Int
)

