package com.sleekydz86.backend.global.config

import com.sleekydz86.backend.domain.model.Permission
import com.sleekydz86.backend.domain.model.Role
import com.sleekydz86.backend.domain.model.User
import com.sleekydz86.backend.domain.repository.PermissionRepository
import com.sleekydz86.backend.domain.repository.RoleRepository
import com.sleekydz86.backend.domain.repository.UserRepository
import org.springframework.boot.CommandLineRunner
import org.springframework.security.crypto.password.PasswordEncoder
import org.springframework.stereotype.Component
import org.springframework.transaction.annotation.Transactional

@Component
class DataInitializer(
    private val userRepository: UserRepository,
    private val roleRepository: RoleRepository,
    private val permissionRepository: PermissionRepository,
    private val passwordEncoder: PasswordEncoder
) : CommandLineRunner {

    @Transactional
    override fun run(vararg args: String?) {
        initializePermissions()
        initializeRoles()
        initializeUsers()
    }

    private fun initializePermissions() {
        val permissions = listOf(
            Permission(name = "STOCK_READ", resource = "stock", action = "read", description = "Read stock data"),
            Permission(name = "STOCK_WRITE", resource = "stock", action = "write", description = "Write stock data"),
            Permission(name = "ANALYSIS_READ", resource = "analysis", action = "read", description = "Read analysis data"),
            Permission(name = "ANALYSIS_WRITE", resource = "analysis", action = "write", description = "Write analysis data"),
            Permission(name = "USER_READ", resource = "user", action = "read", description = "Read user data"),
            Permission(name = "USER_WRITE", resource = "user", action = "write", description = "Write user data"),
            Permission(name = "ADMIN_READ", resource = "admin", action = "read", description = "Read admin data"),
            Permission(name = "ADMIN_WRITE", resource = "admin", action = "write", description = "Write admin data"),
            Permission(name = "EMAIL_READ", resource = "email", action = "read", description = "Read email data"),
            Permission(name = "EMAIL_WRITE", resource = "email", action = "write", description = "Write email data"),
            Permission(name = "TEMPLATE_READ", resource = "template", action = "read", description = "Read template data"),
            Permission(name = "TEMPLATE_WRITE", resource = "template", action = "write", description = "Write template data")
        )

        permissions.forEach { permission ->
            if (!permissionRepository.existsByName(permission.name)) {
                permissionRepository.save(permission)
            }
        }
    }

    private fun initializeRoles() {
        val userPermissions = permissionRepository.findByResource("stock") +
                permissionRepository.findByResource("analysis") +
                permissionRepository.findByResource("email")

        val adminPermissions = permissionRepository.findAll()

        val userRole = Role(
            name = "USER",
            description = "Regular user role",
            permissions = userPermissions.toSet()
        )

        val adminRole = Role(
            name = "ADMIN",
            description = "Administrator role",
            permissions = adminPermissions.toSet()
        )

        if (!roleRepository.existsByName("USER")) {
            roleRepository.save(userRole)
        }

        if (!roleRepository.existsByName("ADMIN")) {
            roleRepository.save(adminRole)
        }
    }

    private fun initializeUsers() {
        val adminRole = roleRepository.findByName("ADMIN").orElse(null)
        val userRole = roleRepository.findByName("USER").orElse(null)

        if (adminRole != null && !userRepository.existsByUsername("admin")) {
            val adminUser = User(
                username = "admin",
                email = "admin@stockanalysis.com",
                password = passwordEncoder.encode("admin123"),
                firstName = "Admin",
                lastName = "User",
                roles = setOf(adminRole)
            )
            userRepository.save(adminUser)
        }

        if (userRole != null && !userRepository.existsByUsername("user")) {
            val regularUser = User(
                username = "user",
                email = "user@stockanalysis.com",
                password = passwordEncoder.encode("user123"),
                firstName = "Regular",
                lastName = "User",
                roles = setOf(userRole)
            )
            userRepository.save(regularUser)
        }
    }
}
