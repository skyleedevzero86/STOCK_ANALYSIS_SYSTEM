package com.sleekydz86.backend.domain.model

data class EmailWithTemplate(
    val templateId: Long,
    val subscriberId: Long,
    val symbol: String,
    val customData: Map<String, String>? = null
)

