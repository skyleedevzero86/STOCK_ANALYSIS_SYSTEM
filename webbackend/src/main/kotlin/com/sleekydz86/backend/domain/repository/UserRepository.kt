package com.sleekydz86.backend.domain.repository

import com.sleekydz86.backend.domain.model.User
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository
import java.util.*

@Repository
interface UserRepository : JpaRepository<User, Long> {

    fun findByUsername(username: String): Optional<User>

    fun findByEmail(email: String): Optional<User>

    fun existsByUsername(username: String): Boolean

    fun existsByEmail(email: String): Boolean

    @Query("SELECT u FROM User u JOIN FETCH u.roles r JOIN FETCH r.permissions WHERE u.username = :username")
    fun findByUsernameWithRolesAndPermissions(@Param("username") username: String): Optional<User>

    @Query("SELECT u FROM User u JOIN FETCH u.roles WHERE u.username = :username")
    fun findByUsernameWithRoles(@Param("username") username: String): Optional<User>

    fun findByIsActiveTrue(): List<User>
}
