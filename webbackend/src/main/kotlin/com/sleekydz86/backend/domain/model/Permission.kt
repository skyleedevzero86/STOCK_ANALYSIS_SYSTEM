package com.sleekydz86.backend.domain.model

import jakarta.persistence.*
import java.time.LocalDateTime

@Entity
@Table(name = "permissions")
data class Permission(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0,

    @Column(unique = true, nullable = false)
    val name: String,

    val description: String? = null,

    @Column(name = "resource")
    val resource: String,

    @Column(name = "action")
    val action: String,

    @Column(name = "is_active")
    val isActive: Boolean = true,

    @Column(name = "created_at")
    val createdAt: LocalDateTime = LocalDateTime.now()
)
