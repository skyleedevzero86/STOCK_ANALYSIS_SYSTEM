package com.sleekydz86.backend.infrastructure.entity

import com.sleekydz86.backend.domain.model.AdminUser
import jakarta.persistence.*
import java.time.LocalDateTime

@Entity
@Table(name = "admin_users")
data class AdminUserEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long? = null,

    @Column(name = "email", nullable = false, unique = true, length = 255)
    val email: String,

    @Column(name = "password_hash", nullable = false, length = 255)
    val passwordHash: String,

    @Column(name = "created_at")
    val createdAt: LocalDateTime = LocalDateTime.now(),

    @Column(name = "is_active", nullable = false)
    val isActive: Boolean = true
) {
    fun toDomain(): AdminUser = AdminUser(
        id = id,
        email = email,
        password = passwordHash,
        createdAt = createdAt,
        isActive = isActive
    )

    companion object {
        fun fromDomain(adminUser: AdminUser): AdminUserEntity = AdminUserEntity(
            id = adminUser.id,
            email = adminUser.email,
            passwordHash = adminUser.password,
            createdAt = adminUser.createdAt,
            isActive = adminUser.isActive
        )
    }
}