package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.Role
import com.sleekydz86.backend.domain.repository.RoleRepository
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional

@Service
@Transactional
class RoleService(
    private val roleRepository: RoleRepository
) {

    fun findByName(name: String): Role? {
        return roleRepository.findByName(name).orElse(null)
    }

    fun save(role: Role): Role {
        return roleRepository.save(role)
    }

    fun createRole(name: String, description: String? = null): Role {
        val role = Role(
            name = name,
            description = description
        )
        return roleRepository.save(role)
    }

    fun getAllActiveRoles(): List<Role> {
        return roleRepository.findByIsActiveTrue()
    }

    fun existsByName(name: String): Boolean {
        return roleRepository.existsByName(name)
    }

    fun findByNameWithPermissions(name: String): Role? {
        return roleRepository.findByNameWithPermissions(name).orElse(null)
    }
}
