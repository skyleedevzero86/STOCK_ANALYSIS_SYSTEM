package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.User
import com.sleekydz86.backend.domain.repository.UserRepository
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import org.springframework.security.core.userdetails.UsernameNotFoundException
import org.springframework.security.crypto.password.PasswordEncoder
import java.util.*

class UserServiceTest {

    private lateinit var userRepository: UserRepository
    private lateinit var passwordEncoder: PasswordEncoder
    private lateinit var userService: UserService

    @BeforeEach
    fun setUp() {
        userRepository = mockk()
        passwordEncoder = mockk()
        userService = UserService(userRepository, passwordEncoder)
    }

    @Test
    @DisplayName("?¬ìš©??ì¡°íšŒ - ?¬ìš©?ê? ì¡´ì¬?????¬ìš©???•ë³´ ë°˜í™˜")
    fun `loadUserByUsername - should return user details when user exists`() {

        val username = "testuser"
        val user = User(
            id = 1L,
            username = username,
            email = "test@example.com",
            password = "encodedPassword"
        )

        every { userRepository.findByUsernameWithRolesAndPermissions(username) } returns Optional.of(user)

        val result = userService.loadUserByUsername(username)

        assertNotNull(result)
        assertEquals(username, result.username)
        verify(exactly = 1) { userRepository.findByUsernameWithRolesAndPermissions(username) }
    }

    @Test
    @DisplayName("?¬ìš©??ì¡°íšŒ - ?¬ìš©?ë? ì°¾ì„ ???†ì„ ???ˆì™¸ ë°œìƒ")
    fun `loadUserByUsername - should throw exception when user not found`() {

        val username = "nonexistent"

        every { userRepository.findByUsernameWithRolesAndPermissions(username) } returns Optional.empty()

        assertThrows(UsernameNotFoundException::class.java) {
            userService.loadUserByUsername(username)
        }
        verify(exactly = 1) { userRepository.findByUsernameWithRolesAndPermissions(username) }
    }

    @Test
    @DisplayName("?¬ìš©?ëª…?¼ë¡œ ì¡°íšŒ - ?¬ìš©?ê? ì¡´ì¬?????¬ìš©??ë°˜í™˜")
    fun `findByUsername - should return user when exists`() {

        val username = "testuser"
        val user = User(
            id = 1L,
            username = username,
            email = "test@example.com",
            password = "encodedPassword"
        )

        every { userRepository.findByUsername(username) } returns Optional.of(user)

        val result = userService.findByUsername(username)

        assertNotNull(result)
        assertEquals(user, result)
        verify(exactly = 1) { userRepository.findByUsername(username) }
    }

    @Test
    @DisplayName("?¬ìš©?ëª…?¼ë¡œ ì¡°íšŒ - ?¬ìš©?ë? ì°¾ì„ ???†ì„ ??null ë°˜í™˜")
    fun `findByUsername - should return null when user not found`() {

        val username = "nonexistent"

        every { userRepository.findByUsername(username) } returns Optional.empty()

        val result = userService.findByUsername(username)

        assertNull(result)
        verify(exactly = 1) { userRepository.findByUsername(username) }
    }

    @Test
    @DisplayName("?´ë©”?¼ë¡œ ì¡°íšŒ - ?¬ìš©?ê? ì¡´ì¬?????¬ìš©??ë°˜í™˜")
    fun `findByEmail - should return user when exists`() {

        val email = "test@example.com"
        val user = User(
            id = 1L,
            username = "testuser",
            email = email,
            password = "encodedPassword"
        )

        every { userRepository.findByEmail(email) } returns Optional.of(user)

        val result = userService.findByEmail(email)

        assertNotNull(result)
        assertEquals(user, result)
        verify(exactly = 1) { userRepository.findByEmail(email) }
    }

    @Test
    @DisplayName("?´ë©”?¼ë¡œ ì¡°íšŒ - ?¬ìš©?ë? ì°¾ì„ ???†ì„ ??null ë°˜í™˜")
    fun `findByEmail - should return null when user not found`() {

        val email = "nonexistent@example.com"

        every { userRepository.findByEmail(email) } returns Optional.empty()

        val result = userService.findByEmail(email)

        assertNull(result)
        verify(exactly = 1) { userRepository.findByEmail(email) }
    }

    @Test
    @DisplayName("?¬ìš©???€??- ?¬ìš©???€????ë°˜í™˜")
    fun `save - should save and return user`() {

        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword"
        )

        every { userRepository.save(user) } returns user

        val result = userService.save(user)

        assertNotNull(result)
        assertEquals(user, result)
        verify(exactly = 1) { userRepository.save(user) }
    }

    @Test
    @DisplayName("?¬ìš©???ì„± - ?”í˜¸?”ëœ ë¹„ë?ë²ˆí˜¸ë¡??¬ìš©???ì„±")
    fun `createUser - should create user with encoded password`() {

        val username = "testuser"
        val email = "test@example.com"
        val password = "plainPassword"
        val firstName = "John"
        val lastName = "Doe"
        val encodedPassword = "encodedPassword"

        every { passwordEncoder.encode(password) } returns encodedPassword
        every { userRepository.save(any()) } answers { firstArg() }

        val result = userService.createUser(username, email, password, firstName, lastName)

        assertNotNull(result)
        assertEquals(username, result.username)
        assertEquals(email, result.email)
        assertEquals(encodedPassword, result.password)
        assertEquals(firstName, result.firstName)
        assertEquals(lastName, result.lastName)
        verify(exactly = 1) { passwordEncoder.encode(password) }
        verify(exactly = 1) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("?¬ìš©???ì„± - firstName/lastName ?†ì´ ?¬ìš©???ì„±")
    fun `createUser - should create user without firstName and lastName`() {

        val username = "testuser"
        val email = "test@example.com"
        val password = "plainPassword"
        val encodedPassword = "encodedPassword"

        every { passwordEncoder.encode(password) } returns encodedPassword
        every { userRepository.save(any()) } answers { firstArg() }

        val result = userService.createUser(username, email, password)

        assertNotNull(result)
        assertEquals(username, result.username)
        assertEquals(email, result.email)
        assertEquals(encodedPassword, result.password)
        assertNull(result.firstName)
        assertNull(result.lastName)
        verify(exactly = 1) { passwordEncoder.encode(password) }
        verify(exactly = 1) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("ë¹„ë?ë²ˆí˜¸ ë³€ê²?- ?¬ìš©?ê? ì¡´ì¬????ë¹„ë?ë²ˆí˜¸ ë³€ê²?)
    fun `updatePassword - should update password when user exists`() {

        val username = "testuser"
        val oldPassword = "oldPassword"
        val newPassword = "newPassword"
        val encodedNewPassword = "encodedNewPassword"
        val user = User(
            id = 1L,
            username = username,
            email = "test@example.com",
            password = oldPassword
        )
        val updatedUser = user.copy(password = encodedNewPassword)

        every { userRepository.findByUsername(username) } returns Optional.of(user)
        every { passwordEncoder.encode(newPassword) } returns encodedNewPassword
        every { userRepository.save(any()) } answers { firstArg<User>().copy(password = encodedNewPassword) }

        val result = userService.updatePassword(username, newPassword)

        assertNotNull(result)
        assertEquals(encodedNewPassword, result.password)
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 1) { passwordEncoder.encode(newPassword) }
        verify(exactly = 1) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("ë¹„ë?ë²ˆí˜¸ ë³€ê²?- ?¬ìš©?ë? ì°¾ì„ ???†ì„ ???ˆì™¸ ë°œìƒ")
    fun `updatePassword - should throw exception when user not found`() {

        val username = "nonexistent"
        val newPassword = "newPassword"

        every { userRepository.findByUsername(username) } returns Optional.empty()

        assertThrows(UsernameNotFoundException::class.java) {
            userService.updatePassword(username, newPassword)
        }
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 0) { passwordEncoder.encode(any()) }
        verify(exactly = 0) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("?¬ìš©???œì„±??- ?¬ìš©?ê? ì¡´ì¬?????œì„±??)
    fun `activateUser - should activate user when exists`() {

        val username = "testuser"
        val user = User(
            id = 1L,
            username = username,
            email = "test@example.com",
            password = "encodedPassword",
            isActive = false
        )

        every { userRepository.findByUsername(username) } returns Optional.of(user)
        every { userRepository.save(any()) } answers { firstArg<User>().copy(isActive = true) }

        val result = userService.activateUser(username)

        assertNotNull(result)
        assertTrue(result.isActive)
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 1) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("?¬ìš©???œì„±??- ?¬ìš©?ë? ì°¾ì„ ???†ì„ ???ˆì™¸ ë°œìƒ")
    fun `activateUser - should throw exception when user not found`() {

        val username = "nonexistent"

        every { userRepository.findByUsername(username) } returns Optional.empty()

        assertThrows(UsernameNotFoundException::class.java) {
            userService.activateUser(username)
        }
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 0) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("?¬ìš©??ë¹„í™œ?±í™” - ?¬ìš©?ê? ì¡´ì¬????ë¹„í™œ?±í™”")
    fun `deactivateUser - should deactivate user when exists`() {

        val username = "testuser"
        val user = User(
            id = 1L,
            username = username,
            email = "test@example.com",
            password = "encodedPassword",
            isActive = true
        )

        every { userRepository.findByUsername(username) } returns Optional.of(user)
        every { userRepository.save(any()) } answers { firstArg<User>().copy(isActive = false) }

        val result = userService.deactivateUser(username)

        assertNotNull(result)
        assertFalse(result.isActive)
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 1) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("?¬ìš©??ë¹„í™œ?±í™” - ?¬ìš©?ë? ì°¾ì„ ???†ì„ ???ˆì™¸ ë°œìƒ")
    fun `deactivateUser - should throw exception when user not found`() {

        val username = "nonexistent"

        every { userRepository.findByUsername(username) } returns Optional.empty()

        assertThrows(UsernameNotFoundException::class.java) {
            userService.deactivateUser(username)
        }
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 0) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("?¬ìš©?ëª… ì¡´ì¬ ?•ì¸ - ?¬ìš©?ëª…??ì¡´ì¬????true ë°˜í™˜")
    fun `existsByUsername - should return true when username exists`() {

        val username = "testuser"

        every { userRepository.existsByUsername(username) } returns true

        val result = userService.existsByUsername(username)

        assertTrue(result)
        verify(exactly = 1) { userRepository.existsByUsername(username) }
    }

    @Test
    @DisplayName("?¬ìš©?ëª… ì¡´ì¬ ?•ì¸ - ?¬ìš©?ëª…??ì¡´ì¬?˜ì? ?Šì„ ??false ë°˜í™˜")
    fun `existsByUsername - should return false when username not exists`() {

        val username = "nonexistent"

        every { userRepository.existsByUsername(username) } returns false

        val result = userService.existsByUsername(username)

        assertFalse(result)
        verify(exactly = 1) { userRepository.existsByUsername(username) }
    }

    @Test
    @DisplayName("?´ë©”??ì¡´ì¬ ?•ì¸ - ?´ë©”?¼ì´ ì¡´ì¬????true ë°˜í™˜")
    fun `existsByEmail - should return true when email exists`() {

        val email = "test@example.com"

        every { userRepository.existsByEmail(email) } returns true

        val result = userService.existsByEmail(email)

        assertTrue(result)
        verify(exactly = 1) { userRepository.existsByEmail(email) }
    }

    @Test
    @DisplayName("?´ë©”??ì¡´ì¬ ?•ì¸ - ?´ë©”?¼ì´ ì¡´ì¬?˜ì? ?Šì„ ??false ë°˜í™˜")
    fun `existsByEmail - should return false when email not exists`() {

        val email = "nonexistent@example.com"

        every { userRepository.existsByEmail(email) } returns false

        val result = userService.existsByEmail(email)

        assertFalse(result)
        verify(exactly = 1) { userRepository.existsByEmail(email) }
    }

    @Test
    @DisplayName("?œì„± ?¬ìš©??ëª©ë¡ ì¡°íšŒ - ?œì„± ?¬ìš©??ëª©ë¡ ë°˜í™˜")
    fun `getAllActiveUsers - should return list of active users`() {

        val activeUsers = listOf(
            User(id = 1L, username = "user1", email = "user1@example.com", password = "password", isActive = true),
            User(id = 2L, username = "user2", email = "user2@example.com", password = "password", isActive = true)
        )

        every { userRepository.findByIsActiveTrue() } returns activeUsers

        val result = userService.getAllActiveUsers()

        assertNotNull(result)
        assertEquals(2, result.size)
        assertTrue(result.all { it.isActive })
        verify(exactly = 1) { userRepository.findByIsActiveTrue() }
    }

    @Test
    @DisplayName("?œì„± ?¬ìš©??ëª©ë¡ ì¡°íšŒ - ?œì„± ?¬ìš©?ê? ?†ì„ ??ë¹?ëª©ë¡ ë°˜í™˜")
    fun `getAllActiveUsers - should return empty list when no active users`() {

        val emptyList = emptyList<User>()

        every { userRepository.findByIsActiveTrue() } returns emptyList

        val result = userService.getAllActiveUsers()

        assertNotNull(result)
        assertTrue(result.isEmpty())
        verify(exactly = 1) { userRepository.findByIsActiveTrue() }
    }
}
