package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.application.dto.ChangePasswordRequest
import com.sleekydz86.backend.application.dto.ProfileResponse
import com.sleekydz86.backend.application.dto.UpdateProfileRequest
import com.sleekydz86.backend.application.mapper.UserMapper
import com.sleekydz86.backend.domain.service.UserService
import org.springframework.http.ResponseEntity
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/profile")
class ProfileController(
    private val userService: UserService
) {

    @GetMapping
    fun getProfile(): ResponseEntity<ProfileResponse> {
        val authentication = SecurityContextHolder.getContext().authentication
        val username = authentication.name

        val user = userService.findByUsername(username) ?: return ResponseEntity.notFound().build()
        return ResponseEntity.ok(UserMapper.toProfileResponse(user))
    }

    @PutMapping
    fun updateProfile(@RequestBody request: UpdateProfileRequest): ResponseEntity<ProfileResponse> {
        val authentication = SecurityContextHolder.getContext().authentication
        val username = authentication.name

        val user = userService.findByUsername(username) ?: return ResponseEntity.notFound().build()

        val updatedUser = user.copy(
            firstName = request.firstName ?: user.firstName,
            lastName = request.lastName ?: user.lastName
        )

        val savedUser = userService.save(updatedUser)
        return ResponseEntity.ok(UserMapper.toProfileResponse(savedUser))
    }

    @PostMapping("/change-password")
    fun changePassword(@RequestBody request: ChangePasswordRequest): ResponseEntity<Map<String, String>> {
        val authentication = SecurityContextHolder.getContext().authentication
        val username = authentication.name

        try {
            userService.updatePassword(username, request.newPassword)
            return ResponseEntity.ok(mapOf("message" to "Password changed successfully"))
        } catch (e: Exception) {
            return ResponseEntity.badRequest().body(mapOf<String, String>("error" to (e.message ?: "Failed to change password")))
        }
    }
}