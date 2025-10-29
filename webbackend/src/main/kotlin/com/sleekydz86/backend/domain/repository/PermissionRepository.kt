package com.sleekydz86.backend.domain.repository

import com.sleekydz86.backend.domain.model.Permission
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.util.*

@Repository
interface PermissionRepository : JpaRepository<Permission, Long> {

    fun findByName(name: String): Optional<Permission>

    fun existsByName(name: String): Boolean

    fun findByResource(resource: String): List<Permission>

    fun findByAction(action: String): List<Permission>

    @Query("SELECT p FROM Permission p WHERE p.resource = :resource AND p.action = :action")
    fun findByResourceAndAction(@Param("resource") resource: String, @Param("action") action: String): Optional<Permission>

    fun findByIsActiveTrue(): List<Permission>
}
