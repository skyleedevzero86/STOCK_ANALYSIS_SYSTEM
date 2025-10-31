package com.sleekydz86.backend.application.dto

data class PermissionResponse(
    val id: Long,
    val name: String,
    val description: String?,
    val resource: String,
    val action: String,
    val isActive: Boolean
)

data class CreatePermissionRequest(
    val name: String,
    val resource: String,
    val action: String,
    val description: String? = null
)

data class UpdatePermissionRequest(
    val description: String? = null
)

