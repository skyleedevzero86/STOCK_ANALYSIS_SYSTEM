package com.sleekydz86.backend.application.dto

data class RoleResponse(
    val id: Long,
    val name: String,
    val description: String?,
    val isActive: Boolean,
    val permissions: List<String>
)

data class CreateRoleRequest(
    val name: String,
    val description: String? = null,
    val permissionIds: List<Long> = emptyList()
)

data class UpdateRoleRequest(
    val description: String? = null,
    val permissionIds: List<Long> = emptyList()
)

