package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.CreateRoleRequest
import com.sleekydz86.backend.application.dto.RoleResponse
import com.sleekydz86.backend.application.dto.UpdateRoleRequest
import com.sleekydz86.backend.application.mapper.RoleMapper
import com.sleekydz86.backend.domain.model.Permission
import com.sleekydz86.backend.domain.model.Role
import com.sleekydz86.backend.domain.service.PermissionService
import com.sleekydz86.backend.domain.service.RoleService
import org.springframework.http.ResponseEntity
import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/admin/roles")
@PreAuthorize("hasRole('ADMIN')")
class RoleManagementController(
    private val roleService: RoleService,
    private val permissionService: PermissionService
) {

    @GetMapping
    fun getAllRoles(): ResponseEntity<List<RoleResponse>> {
        val roles = roleService.getAllActiveRoles()
        val roleResponses = roles.map { RoleMapper.toRoleResponse(it) }
        return ResponseEntity.ok(roleResponses)
    }

    @GetMapping("/{name}")
    fun getRoleByName(@PathVariable name: String): ResponseEntity<RoleResponse> {
        val role = roleService.findByNameWithPermissions(name) ?: return ResponseEntity.notFound().build()
        return ResponseEntity.ok(RoleMapper.toRoleResponse(role))
    }

    @PostMapping
    fun createRole(@RequestBody request: CreateRoleRequest): ResponseEntity<RoleResponse> {
        if (roleService.existsByName(request.name)) {
            return ResponseEntity.badRequest().build()
        }

        val permissions = request.permissionIds.mapNotNull { id ->
            permissionService.findByName("")
        }.toSet()

        val role = Role(
            name = request.name,
            description = request.description,
            permissions = permissions
        )

        val savedRole = roleService.save(role)
        return ResponseEntity.ok(RoleMapper.toRoleResponse(savedRole))
    }

    @PutMapping("/{name}")
    fun updateRole(
        @PathVariable name: String,
        @RequestBody request: UpdateRoleRequest
    ): ResponseEntity<RoleResponse> {
        val role = roleService.findByNameWithPermissions(name) ?: return ResponseEntity.notFound().build()

        val permissions = request.permissionIds.mapNotNull { id ->
            permissionService.findByName("")
        }.toSet()

        val updatedRole = role.copy(
            description = request.description ?: role.description,
            permissions = permissions
        )

        val savedRole = roleService.save(updatedRole)
        return ResponseEntity.ok(RoleMapper.toRoleResponse(savedRole))
    }
}
