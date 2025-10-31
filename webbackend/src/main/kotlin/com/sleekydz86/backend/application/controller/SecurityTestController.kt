package com.sleekydz86.backend.application.controller

import org.springframework.http.ResponseEntity
import org.springframework.security.access.prepost.PreAuthorize
import org.springframework.security.core.Authentication
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/security-test")
class SecurityTestController {

    @GetMapping("/public")
    fun publicEndpoint(): ResponseEntity<Map<String, String>> {
        return ResponseEntity.ok(mapOf(
            "message" to "This is a public endpoint",
            "access" to "No authentication required"
        ))
    }

    @GetMapping("/user")
    @PreAuthorize("hasAnyRole('USER', 'ADMIN')")
    fun userEndpoint(): ResponseEntity<Map<String, Any>> {
        val authentication = SecurityContextHolder.getContext().authentication
        return ResponseEntity.ok(mapOf(
            "message" to "This is a user endpoint",
            "access" to "USER or ADMIN role required",
            "user" to authentication.name,
            "authorities" to authentication.authorities.map { it.authority }
        ))
    }

    @GetMapping("/admin")
    @PreAuthorize("hasRole('ADMIN')")
    fun adminEndpoint(): ResponseEntity<Map<String, Any>> {
        val authentication = SecurityContextHolder.getContext().authentication
        return ResponseEntity.ok(mapOf(
            "message" to "This is an admin endpoint",
            "access" to "ADMIN role required",
            "user" to authentication.name,
            "authorities" to authentication.authorities.map { it.authority }
        ))
    }

    @GetMapping("/permission-test")
    @PreAuthorize("hasAuthority('STOCK_READ')")
    fun permissionTestEndpoint(): ResponseEntity<Map<String, Any>> {
        val authentication = SecurityContextHolder.getContext().authentication
        return ResponseEntity.ok(mapOf(
            "message" to "This endpoint requires STOCK_READ permission",
            "user" to authentication.name,
            "authorities" to authentication.authorities.map { it.authority }
        ))
    }

    @GetMapping("/method-security")
    @PreAuthorize("hasRole('ADMIN') and hasAuthority('USER_WRITE')")
    fun methodSecurityEndpoint(): ResponseEntity<Map<String, Any>> {
        val authentication = SecurityContextHolder.getContext().authentication
        return ResponseEntity.ok(mapOf(
            "message" to "This endpoint uses method-level security",
            "requirements" to "ADMIN role AND USER_WRITE permission",
            "user" to authentication.name,
            "authorities" to authentication.authorities.map { it.authority }
        ))
    }
}
