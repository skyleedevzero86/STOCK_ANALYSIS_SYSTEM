package com.sleekydz86.backend.domain.cqrs.command

import java.time.LocalDateTime

data class CommandResult(
    val success: Boolean,
    val message: String,
    val data: Any? = null,
    val timestamp: LocalDateTime = LocalDateTime.now()
)

