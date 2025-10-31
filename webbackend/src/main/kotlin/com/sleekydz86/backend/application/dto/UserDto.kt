package com.sleekydz86.backend.application.dto

data class UserResponse(
    val id: Long,
    val username: String,
    val email: String,
    val firstName: String?,
    val lastName: String?,
    val isActive: Boolean,
    val isEmailVerified: Boolean,
    val roles: List<String>
)

data class UpdateUserRequest(
    val firstName: String? = null,
    val lastName: String? = null,
    val isActive: Boolean? = null
)

data class ChangePasswordRequest(
    val currentPassword: String,
    val newPassword: String
)

