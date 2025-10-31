package com.sleekydz86.backend.application.mapper

import com.sleekydz86.backend.application.dto.RoleResponse
import com.sleekydz86.backend.domain.model.Role

object RoleMapper {
    fun toRoleResponse(role: Role): RoleResponse {
        return RoleResponse(
            id = role.id,
            name = role.name,
            description = role.description,
            isActive = role.isActive,
            permissions = role.permissions.map { it.name }
        )
    }
}

