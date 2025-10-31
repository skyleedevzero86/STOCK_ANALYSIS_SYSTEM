package com.sleekydz86.backend.infrastructure.repository

import com.sleekydz86.backend.infrastructure.entity.AdminUserEntity
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.stereotype.Repository

@Repository
interface AdminUserRepository : JpaRepository<AdminUserEntity, Long> {

    fun findByEmail(email: String): AdminUserEntity?

    fun findByEmailAndIsActive(email: String, isActive: Boolean): AdminUserEntity?
}
