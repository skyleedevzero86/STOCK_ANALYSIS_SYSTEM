package com.sleekydz86.backend.infrastructure.entity

import jakarta.persistence.*
import java.time.LocalDateTime

@Entity
@Table(name = "notification_logs")
data class NotificationLogEntity(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long? = null,

    @Column(name = "user_email", nullable = false, length = 100)
    val userEmail: String,

    @Column(name = "symbol", length = 10)
    val symbol: String? = null,

    @Column(name = "notification_type", nullable = false, length = 20)
    val notificationType: String,

    @Column(name = "message", columnDefinition = "TEXT")
    val message: String? = null,

    @Column(name = "sent_at")
    val sentAt: LocalDateTime = LocalDateTime.now(),

    @Column(name = "status", nullable = false, length = 20)
    val status: String = "pending",

    @Column(name = "error_message", columnDefinition = "TEXT")
    val errorMessage: String? = null
)

