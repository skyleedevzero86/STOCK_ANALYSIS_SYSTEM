package com.sleekydz86.backend.domain.model

data class SupportResistance(
    val support: List<SupportResistanceLevel>,
    val resistance: List<SupportResistanceLevel>
)

