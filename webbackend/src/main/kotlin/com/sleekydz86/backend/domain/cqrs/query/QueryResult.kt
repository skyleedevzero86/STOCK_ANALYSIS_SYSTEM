package com.sleekydz86.backend.domain.cqrs.query

import java.time.LocalDateTime

data class QueryResult<T>(
    val data: T,
    val timestamp: LocalDateTime = LocalDateTime.now(),
    val success: Boolean = true
)

