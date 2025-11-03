package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.User
import com.sleekydz86.backend.domain.repository.UserRepository
import org.springframework.security.core.userdetails.UserDetails
import org.springframework.security.core.userdetails.UserDetailsService
import org.springframework.security.core.userdetails.UsernameNotFoundException
import org.springframework.security.crypto.password.PasswordEncoder
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional

@Service
@Transactional
class UserService(
    private val userRepository: UserRepository,
    private val passwordEncoder: PasswordEncoder
) : UserDetailsService {

    override fun loadUserByUsername(username: String): UserDetails {
        return userRepository.findByUsernameWithRolesAndPermissions(username)
            .orElseThrow { UsernameNotFoundException("User not found: $username") }
    }

    fun findByUsername(username: String): User? {
        return userRepository.findByUsername(username).orElse(null)
    }

    fun findByEmail(email: String): User? {
        return userRepository.findByEmail(email).orElse(null)
    }

    fun save(user: User): User {
        return userRepository.save(user)
    }

    fun createUser(username: String, email: String, password: String, firstName: String? = null, lastName: String? = null): User {
        val encodedPassword = passwordEncoder.encode(password)
        val user = User(
            username = username,
            email = email,
            password = encodedPassword,
            firstName = firstName,
            lastName = lastName
        )
        return userRepository.save(user)
    }

    fun updatePassword(username: String, newPassword: String): User {
        val user = findByUsername(username) ?: throw UsernameNotFoundException("User not found: $username")
        val encodedPassword = passwordEncoder.encode(newPassword)
        val updatedUser = user.copy(password = encodedPassword)
        return userRepository.save(updatedUser)
    }

    fun activateUser(username: String): User {
        val user = findByUsername(username) ?: throw UsernameNotFoundException("User not found: $username")
        val updatedUser = user.copy(isActive = true)
        return userRepository.save(updatedUser)
    }

    fun deactivateUser(username: String): User {
        val user = findByUsername(username) ?: throw UsernameNotFoundException("User not found: $username")
        val updatedUser = user.copy(isActive = false)
        return userRepository.save(updatedUser)
    }

    fun existsByUsername(username: String): Boolean {
        return userRepository.existsByUsername(username)
    }

    fun existsByEmail(email: String): Boolean {
        return userRepository.existsByEmail(email)
    }

    fun getAllActiveUsers(): List<User> {
        return userRepository.findByIsActiveTrue()
    }
}
