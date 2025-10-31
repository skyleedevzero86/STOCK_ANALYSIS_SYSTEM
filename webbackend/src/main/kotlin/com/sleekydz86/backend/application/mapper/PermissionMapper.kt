package com.sleekydz86.backend.application.mapper

import com.sleekydz86.backend.application.dto.PermissionResponse
import com.sleekydz86.backend.domain.model.Permission

object PermissionMapper {
    fun toPermissionResponse(permission: Permission): PermissionResponse {
        return PermissionResponse(
            id = permission.id,
            name = permission.name,
            description = permission.description,
            resource = permission.resource,
            action = permission.action,
            isActive = permission.isActive
        )
    }
}

