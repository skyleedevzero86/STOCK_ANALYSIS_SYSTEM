package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.CreatePermissionRequest
import com.sleekydz86.backend.application.dto.PermissionResponse
import com.sleekydz86.backend.application.dto.UpdatePermissionRequest
import com.sleekydz86.backend.application.mapper.PermissionMapper
import com.sleekydz86.backend.domain.model.Permission
import com.sleekydz86.backend.domain.service.PermissionService
import org.springframework.http.ResponseEntity
import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/admin/permissions")
@PreAuthorize("hasRole('ADMIN')")
class PermissionManagementController(
    private val permissionService: PermissionService
) {

    @GetMapping
    fun getAllPermissions(): ResponseEntity<List<PermissionResponse>> {
        val permissions = permissionService.getAllActivePermissions()
        val permissionResponses = permissions.map { PermissionMapper.toPermissionResponse(it) }
        return ResponseEntity.ok(permissionResponses)
    }

    @GetMapping("/{name}")
    fun getPermissionByName(@PathVariable name: String): ResponseEntity<PermissionResponse> {
        val permission = permissionService.findByName(name) ?: return ResponseEntity.notFound().build()
        return ResponseEntity.ok(PermissionMapper.toPermissionResponse(permission))
    }

    @GetMapping("/resource/{resource}")
    fun getPermissionsByResource(@PathVariable resource: String): ResponseEntity<List<PermissionResponse>> {
        val permissions = permissionService.findByResource(resource)
        val permissionResponses = permissions.map { PermissionMapper.toPermissionResponse(it) }
        return ResponseEntity.ok(permissionResponses)
    }

    @PostMapping
    fun createPermission(@RequestBody request: CreatePermissionRequest): ResponseEntity<PermissionResponse> {
        if (permissionService.existsByName(request.name)) {
            return ResponseEntity.badRequest().build()
        }

        val permission = Permission(
            name = request.name,
            resource = request.resource,
            action = request.action,
            description = request.description
        )

        val savedPermission = permissionService.save(permission)
        return ResponseEntity.ok(PermissionMapper.toPermissionResponse(savedPermission))
    }

    @PutMapping("/{name}")
    fun updatePermission(
        @PathVariable name: String,
        @RequestBody request: UpdatePermissionRequest
    ): ResponseEntity<PermissionResponse> {
        val permission = permissionService.findByName(name) ?: return ResponseEntity.notFound().build()

        val updatedPermission = permission.copy(
            description = request.description ?: permission.description
        )

        val savedPermission = permissionService.save(updatedPermission)
        return ResponseEntity.ok(PermissionMapper.toPermissionResponse(savedPermission))
    }
}