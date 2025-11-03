package com.sleekydz86.backend.domain.model

data class ChartPattern(
    val type: String,
    val confidence: Double,
    val signal: String,
    val description: String? = null
)

