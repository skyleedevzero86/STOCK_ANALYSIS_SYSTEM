package com.sleekydz86.backend.domain.cqrs.event

import java.time.LocalDateTime

data class EventMetadata(
    val eventId: String,
    val aggregateId: String,
    val version: Long,
    val timestamp: LocalDateTime,
    val eventType: String
)

