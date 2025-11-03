package com.sleekydz86.backend.domain.model

import java.time.LocalDateTime

data class Anomaly(
    val type: String,
    val severity: String,
    val message: String,
    val timestamp: LocalDateTime
)

