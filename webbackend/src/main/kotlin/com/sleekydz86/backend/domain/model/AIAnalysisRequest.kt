package com.sleekydz86.backend.domain.model

data class AIAnalysisRequest(
    val symbol: String,
    val analysisType: String = "comprehensive"
)

