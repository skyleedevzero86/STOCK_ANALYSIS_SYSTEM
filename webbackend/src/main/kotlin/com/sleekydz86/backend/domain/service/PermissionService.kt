package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.Permission
import com.sleekydz86.backend.domain.repository.PermissionRepository
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional

@Service
@Transactional
class PermissionService(
    private val permissionRepository: PermissionRepository
) {

    fun findByName(name: String): Permission? {
        return permissionRepository.findByName(name).orElse(null)
    }

    fun save(permission: Permission): Permission {
        return permissionRepository.save(permission)
    }

    fun createPermission(name: String, resource: String, action: String, description: String? = null): Permission {
        val permission = Permission(
            name = name,
            resource = resource,
            action = action,
            description = description
        )
        return permissionRepository.save(permission)
    }

    fun getAllActivePermissions(): List<Permission> {
        return permissionRepository.findByIsActiveTrue()
    }

    fun findByResource(resource: String): List<Permission> {
        return permissionRepository.findByResource(resource)
    }

    fun findByAction(action: String): List<Permission> {
        return permissionRepository.findByAction(action)
    }

    fun findByResourceAndAction(resource: String, action: String): Permission? {
        return permissionRepository.findByResourceAndAction(resource, action).orElse(null)
    }

    fun existsByName(name: String): Boolean {
        return permissionRepository.existsByName(name)
    }

    fun findById(id: Long): Permission? {
        return permissionRepository.findById(id).orElse(null)
    }
}
