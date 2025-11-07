package com.sleekydz86.backend.domain.model

data class News(
    val title: String,
    val description: String? = null,
    val url: String,
    val source: String? = null,
    val publishedAt: String? = null,
    val symbol: String,
    val provider: String,
    val sentiment: Double? = null
)

