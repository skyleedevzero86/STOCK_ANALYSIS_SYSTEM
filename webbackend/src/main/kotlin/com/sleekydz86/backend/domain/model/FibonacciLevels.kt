package com.sleekydz86.backend.domain.model

data class FibonacciLevels(
    val levels: Map<String, Double>,
    val nearestLevel: String,
    val distanceToNearest: Double
)

