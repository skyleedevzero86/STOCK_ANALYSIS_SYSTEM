package com.sleekydz86.backend.domain.repository

import com.sleekydz86.backend.domain.model.Role
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.util.*

@Repository
interface RoleRepository : JpaRepository<Role, Long> {

    fun findByName(name: String): Optional<Role>

    fun existsByName(name: String): Boolean

    @Query("SELECT r FROM Role r JOIN FETCH r.permissions WHERE r.name = :name")
    fun findByNameWithPermissions(@Param("name") name: String): Optional<Role>

    fun findByIsActiveTrue(): List<Role>
}
