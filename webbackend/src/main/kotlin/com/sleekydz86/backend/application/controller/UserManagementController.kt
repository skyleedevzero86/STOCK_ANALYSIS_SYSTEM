package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.ChangePasswordRequest
import com.sleekydz86.backend.application.dto.UpdateUserRequest
import com.sleekydz86.backend.application.dto.UserResponse
import com.sleekydz86.backend.application.mapper.UserMapper
import com.sleekydz86.backend.domain.service.RoleService
import com.sleekydz86.backend.domain.service.UserService
import org.springframework.http.ResponseEntity
import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/admin/users")
@PreAuthorize("hasRole('ADMIN')")
class UserManagementController(
    private val userService: UserService,
    private val roleService: RoleService
) {

    @GetMapping
    fun getAllUsers(): ResponseEntity<List<UserResponse>> {
        val users = userService.getAllActiveUsers()
        val userResponses = users.map { UserMapper.toUserResponse(it) }
        return ResponseEntity.ok(userResponses)
    }

    @GetMapping("/{username}")
    fun getUserByUsername(@PathVariable username: String): ResponseEntity<UserResponse> {
        val user = userService.findByUsername(username) ?: return ResponseEntity.notFound().build()
        return ResponseEntity.ok(UserMapper.toUserResponse(user))
    }

    @PutMapping("/{username}")
    fun updateUser(
        @PathVariable username: String,
        @RequestBody request: UpdateUserRequest
    ): ResponseEntity<UserResponse> {
        val user = userService.findByUsername(username) ?: return ResponseEntity.notFound().build()

        val updatedUser = user.copy(
            firstName = request.firstName ?: user.firstName,
            lastName = request.lastName ?: user.lastName,
            isActive = request.isActive ?: user.isActive
        )

        val savedUser = userService.save(updatedUser)
        return ResponseEntity.ok(UserMapper.toUserResponse(savedUser))
    }

    @PostMapping("/{username}/activate")
    fun activateUser(@PathVariable username: String): ResponseEntity<Map<String, String>> {
        try {
            userService.activateUser(username)
            return ResponseEntity.ok(mapOf("message" to "User activated successfully"))
        } catch (e: Exception) {
            val errorMessage: String = e.message ?: "Failed to activate user"
            return ResponseEntity.badRequest().body(mapOf("error" to errorMessage))
        }
    }

    @PostMapping("/{username}/deactivate")
    fun deactivateUser(@PathVariable username: String): ResponseEntity<Map<String, String>> {
        try {
            userService.deactivateUser(username)
            return ResponseEntity.ok(mapOf("message" to "User deactivated successfully"))
        } catch (e: Exception) {
            val errorMessage: String = e.message ?: "Failed to deactivate user"
            return ResponseEntity.badRequest().body(mapOf("error" to errorMessage))
        }
    }

    @PostMapping("/{username}/change-password")
    fun changePassword(
        @PathVariable username: String,
        @RequestBody request: ChangePasswordRequest
    ): ResponseEntity<Map<String, String>> {
        try {
            userService.updatePassword(username, request.newPassword)
            return ResponseEntity.ok(mapOf("message" to "Password changed successfully"))
        } catch (e: Exception) {
            val errorMessage: String = e.message ?: "Failed to change password"
            return ResponseEntity.badRequest().body(mapOf("error" to errorMessage))
        }
    }
}