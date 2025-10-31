package com.sleekydz86.backend.application.dto

data class ApiResponse<T>(
    val success: Boolean,
    val message: String,
    val data: T?
)

object ApiResponseBuilder {
    fun <T> success(message: String, data: T?): ApiResponse<T> {
        return ApiResponse(true, message, data)
    }

    fun <T> failure(message: String, data: T? = null): ApiResponse<T> {
        return ApiResponse(false, message, data)
    }
}

