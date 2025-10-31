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
    @DisplayName("사용자 조회 - 사용자가 존재할 때 사용자 정보 반환")
    fun `loadUserByUsername - should return user details when user exists`() {
        //given
        val username = "testuser"
        val user = User(
            id = 1L,
            username = username,
            email = "test@example.com",
            password = "encodedPassword"
        )

        every { userRepository.findByUsernameWithRolesAndPermissions(username) } returns Optional.of(user)

        //when
        val result = userService.loadUserByUsername(username)

        //then
        assertNotNull(result)
        assertEquals(username, result.username)
        verify(exactly = 1) { userRepository.findByUsernameWithRolesAndPermissions(username) }
    }

    @Test
    @DisplayName("사용자 조회 - 사용자를 찾을 수 없을 때 예외 발생")
    fun `loadUserByUsername - should throw exception when user not found`() {
        //given
        val username = "nonexistent"

        every { userRepository.findByUsernameWithRolesAndPermissions(username) } returns Optional.empty()

        //when & then
        assertThrows(UsernameNotFoundException::class.java) {
            userService.loadUserByUsername(username)
        }
        verify(exactly = 1) { userRepository.findByUsernameWithRolesAndPermissions(username) }
    }

    @Test
    @DisplayName("사용자명으로 조회 - 사용자가 존재할 때 사용자 반환")
    fun `findByUsername - should return user when exists`() {
        //given
        val username = "testuser"
        val user = User(
            id = 1L,
            username = username,
            email = "test@example.com",
            password = "encodedPassword"
        )

        every { userRepository.findByUsername(username) } returns Optional.of(user)

        //when
        val result = userService.findByUsername(username)

        //then
        assertNotNull(result)
        assertEquals(user, result)
        verify(exactly = 1) { userRepository.findByUsername(username) }
    }

    @Test
    @DisplayName("사용자명으로 조회 - 사용자를 찾을 수 없을 때 null 반환")
    fun `findByUsername - should return null when user not found`() {
        //given
        val username = "nonexistent"

        every { userRepository.findByUsername(username) } returns Optional.empty()

        //when
        val result = userService.findByUsername(username)

        //then
        assertNull(result)
        verify(exactly = 1) { userRepository.findByUsername(username) }
    }

    @Test
    @DisplayName("이메일로 조회 - 사용자가 존재할 때 사용자 반환")
    fun `findByEmail - should return user when exists`() {
        //given
        val email = "test@example.com"
        val user = User(
            id = 1L,
            username = "testuser",
            email = email,
            password = "encodedPassword"
        )

        every { userRepository.findByEmail(email) } returns Optional.of(user)

        //when
        val result = userService.findByEmail(email)

        //then
        assertNotNull(result)
        assertEquals(user, result)
        verify(exactly = 1) { userRepository.findByEmail(email) }
    }

    @Test
    @DisplayName("이메일로 조회 - 사용자를 찾을 수 없을 때 null 반환")
    fun `findByEmail - should return null when user not found`() {
        //given
        val email = "nonexistent@example.com"

        every { userRepository.findByEmail(email) } returns Optional.empty()

        //when
        val result = userService.findByEmail(email)

        //then
        assertNull(result)
        verify(exactly = 1) { userRepository.findByEmail(email) }
    }

    @Test
    @DisplayName("사용자 저장 - 사용자 저장 후 반환")
    fun `save - should save and return user`() {
        //given
        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword"
        )

        every { userRepository.save(user) } returns user

        //when
        val result = userService.save(user)

        //then
        assertNotNull(result)
        assertEquals(user, result)
        verify(exactly = 1) { userRepository.save(user) }
    }

    @Test
    @DisplayName("사용자 생성 - 암호화된 비밀번호로 사용자 생성")
    fun `createUser - should create user with encoded password`() {
        //given
        val username = "testuser"
        val email = "test@example.com"
        val password = "plainPassword"
        val firstName = "John"
        val lastName = "Doe"
        val encodedPassword = "encodedPassword"

        every { passwordEncoder.encode(password) } returns encodedPassword
        every { userRepository.save(any()) } answers { firstArg() }

        //when
        val result = userService.createUser(username, email, password, firstName, lastName)

        //then
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
    @DisplayName("사용자 생성 - firstName/lastName 없이 사용자 생성")
    fun `createUser - should create user without firstName and lastName`() {
        //given
        val username = "testuser"
        val email = "test@example.com"
        val password = "plainPassword"
        val encodedPassword = "encodedPassword"

        every { passwordEncoder.encode(password) } returns encodedPassword
        every { userRepository.save(any()) } answers { firstArg() }

        //when
        val result = userService.createUser(username, email, password)

        //then
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
    @DisplayName("비밀번호 변경 - 사용자가 존재할 때 비밀번호 변경")
    fun `updatePassword - should update password when user exists`() {
        //given
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

        //when
        val result = userService.updatePassword(username, newPassword)

        //then
        assertNotNull(result)
        assertEquals(encodedNewPassword, result.password)
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 1) { passwordEncoder.encode(newPassword) }
        verify(exactly = 1) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("비밀번호 변경 - 사용자를 찾을 수 없을 때 예외 발생")
    fun `updatePassword - should throw exception when user not found`() {
        //given
        val username = "nonexistent"
        val newPassword = "newPassword"

        every { userRepository.findByUsername(username) } returns Optional.empty()

        //when & then
        assertThrows(UsernameNotFoundException::class.java) {
            userService.updatePassword(username, newPassword)
        }
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 0) { passwordEncoder.encode(any()) }
        verify(exactly = 0) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("사용자 활성화 - 사용자가 존재할 때 활성화")
    fun `activateUser - should activate user when exists`() {
        //given
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

        //when
        val result = userService.activateUser(username)

        //then
        assertNotNull(result)
        assertTrue(result.isActive)
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 1) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("사용자 활성화 - 사용자를 찾을 수 없을 때 예외 발생")
    fun `activateUser - should throw exception when user not found`() {
        //given
        val username = "nonexistent"

        every { userRepository.findByUsername(username) } returns Optional.empty()

        //when & then
        assertThrows(UsernameNotFoundException::class.java) {
            userService.activateUser(username)
        }
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 0) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("사용자 비활성화 - 사용자가 존재할 때 비활성화")
    fun `deactivateUser - should deactivate user when exists`() {
        //given
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

        //when
        val result = userService.deactivateUser(username)

        //then
        assertNotNull(result)
        assertFalse(result.isActive)
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 1) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("사용자 비활성화 - 사용자를 찾을 수 없을 때 예외 발생")
    fun `deactivateUser - should throw exception when user not found`() {
        //given
        val username = "nonexistent"

        every { userRepository.findByUsername(username) } returns Optional.empty()

        //when & then
        assertThrows(UsernameNotFoundException::class.java) {
            userService.deactivateUser(username)
        }
        verify(exactly = 1) { userRepository.findByUsername(username) }
        verify(exactly = 0) { userRepository.save(any()) }
    }

    @Test
    @DisplayName("사용자명 존재 확인 - 사용자명이 존재할 때 true 반환")
    fun `existsByUsername - should return true when username exists`() {
        //given
        val username = "testuser"

        every { userRepository.existsByUsername(username) } returns true

        //when
        val result = userService.existsByUsername(username)

        //then
        assertTrue(result)
        verify(exactly = 1) { userRepository.existsByUsername(username) }
    }

    @Test
    @DisplayName("사용자명 존재 확인 - 사용자명이 존재하지 않을 때 false 반환")
    fun `existsByUsername - should return false when username not exists`() {
        //given
        val username = "nonexistent"

        every { userRepository.existsByUsername(username) } returns false

        //when
        val result = userService.existsByUsername(username)

        //then
        assertFalse(result)
        verify(exactly = 1) { userRepository.existsByUsername(username) }
    }

    @Test
    @DisplayName("이메일 존재 확인 - 이메일이 존재할 때 true 반환")
    fun `existsByEmail - should return true when email exists`() {
        //given
        val email = "test@example.com"

        every { userRepository.existsByEmail(email) } returns true

        //when
        val result = userService.existsByEmail(email)

        //then
        assertTrue(result)
        verify(exactly = 1) { userRepository.existsByEmail(email) }
    }

    @Test
    @DisplayName("이메일 존재 확인 - 이메일이 존재하지 않을 때 false 반환")
    fun `existsByEmail - should return false when email not exists`() {
        //given
        val email = "nonexistent@example.com"

        every { userRepository.existsByEmail(email) } returns false

        //when
        val result = userService.existsByEmail(email)

        //then
        assertFalse(result)
        verify(exactly = 1) { userRepository.existsByEmail(email) }
    }

    @Test
    @DisplayName("활성 사용자 목록 조회 - 활성 사용자 목록 반환")
    fun `getAllActiveUsers - should return list of active users`() {
        //given
        val activeUsers = listOf(
            User(id = 1L, username = "user1", email = "user1@example.com", password = "password", isActive = true),
            User(id = 2L, username = "user2", email = "user2@example.com", password = "password", isActive = true)
        )

        every { userRepository.findByIsActiveTrue() } returns activeUsers

        //when
        val result = userService.getAllActiveUsers()

        //then
        assertNotNull(result)
        assertEquals(2, result.size)
        assertTrue(result.all { it.isActive })
        verify(exactly = 1) { userRepository.findByIsActiveTrue() }
    }

    @Test
    @DisplayName("활성 사용자 목록 조회 - 활성 사용자가 없을 때 빈 목록 반환")
    fun `getAllActiveUsers - should return empty list when no active users`() {
        //given
        val emptyList = emptyList<User>()

        every { userRepository.findByIsActiveTrue() } returns emptyList

        //when
        val result = userService.getAllActiveUsers()

        //then
        assertNotNull(result)
        assertTrue(result.isEmpty())
        verify(exactly = 1) { userRepository.findByIsActiveTrue() }
    }
}
