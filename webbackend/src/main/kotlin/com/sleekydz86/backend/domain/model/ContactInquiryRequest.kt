package com.sleekydz86.backend.domain.model

data class ContactInquiryRequest(
    val name: String,
    val email: String,
    val phone: String? = null,
    val category: String,
    val subject: String,
    val message: String
)



