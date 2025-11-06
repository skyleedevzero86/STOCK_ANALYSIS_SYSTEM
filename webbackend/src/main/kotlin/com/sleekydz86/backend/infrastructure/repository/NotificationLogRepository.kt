package com.sleekydz86.backend.infrastructure.repository

import com.sleekydz86.backend.infrastructure.entity.NotificationLogEntity
import org.springframework.data.domain.Page
import org.springframework.data.domain.Pageable
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.stereotype.Repository

@Repository
interface NotificationLogRepository : JpaRepository<NotificationLogEntity, Long> {

    @Query("SELECT n FROM NotificationLogEntity n WHERE n.userEmail = :email ORDER BY n.sentAt DESC")
    fun findByUserEmail(email: String, pageable: Pageable): Page<NotificationLogEntity>

    @Query("SELECT n FROM NotificationLogEntity n WHERE n.userEmail = :email ORDER BY n.sentAt DESC")
    fun findByUserEmail(email: String): List<NotificationLogEntity>
}

