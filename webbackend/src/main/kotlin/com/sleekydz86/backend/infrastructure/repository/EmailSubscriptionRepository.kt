package com.sleekydz86.backend.infrastructure.repository

import com.sleekydz86.backend.infrastructure.entity.EmailSubscriptionEntity
import org.springframework.data.domain.Page
import org.springframework.data.domain.Pageable
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.stereotype.Repository

@Repository
interface EmailSubscriptionRepository : JpaRepository<EmailSubscriptionEntity, Long> {

    fun findByEmail(email: String): EmailSubscriptionEntity?

    fun findByEmailAndIsActive(email: String, isActive: Boolean): EmailSubscriptionEntity?

    @Query("SELECT e FROM EmailSubscriptionEntity e WHERE e.isActive = true")
    fun findAllActive(): List<EmailSubscriptionEntity>

    @Query("SELECT e FROM EmailSubscriptionEntity e WHERE e.isActive = true")
    fun findAllActive(pageable: Pageable): Page<EmailSubscriptionEntity>

    @Query("SELECT e FROM EmailSubscriptionEntity e WHERE e.name LIKE CONCAT('%', :name, '%')")
    fun findByNameContaining(name: String, pageable: Pageable): Page<EmailSubscriptionEntity>

    @Query("SELECT e FROM EmailSubscriptionEntity e WHERE e.isActive = true AND e.name LIKE CONCAT('%', :name, '%')")
    fun findAllActiveByNameContaining(name: String, pageable: Pageable): Page<EmailSubscriptionEntity>

    @Query("SELECT e FROM EmailSubscriptionEntity e WHERE e.isActive = true AND e.isEmailConsent = true")
    fun findAllActiveWithEmailConsent(): List<EmailSubscriptionEntity>
}
