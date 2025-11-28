package com.sleekydz86.backend.application.mapper

import com.sleekydz86.backend.application.dto.ProfileResponse
import com.sleekydz86.backend.application.dto.UserInfo
import com.sleekydz86.backend.application.dto.UserResponse
import com.sleekydz86.backend.domain.model.Role
import com.sleekydz86.backend.domain.model.User
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test

class UserMapperTest {

    @Test
    @DisplayName("?¨Ïö©???ëÎãµ Î≥Ä??- UserÎ•?UserResponseÎ°?Î≥Ä??)
    fun `toUserResponse - should convert User to UserResponse`() {

        val role = Role(name = "ROLE_USER")
        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            firstName = "John",
            lastName = "Doe",
            isActive = true,
            isEmailVerified = true,
            roles = setOf(role)
        )

        val result = UserMapper.toUserResponse(user)

        assertNotNull(result)
        assertEquals(user.id, result.id)
        assertEquals(user.username, result.username)
        assertEquals(user.email, result.email)
        assertEquals(user.firstName, result.firstName)
        assertEquals(user.lastName, result.lastName)
        assertEquals(user.isActive, result.isActive)
        assertEquals(user.isEmailVerified, result.isEmailVerified)
        assertEquals(listOf("ROLE_USER"), result.roles)
    }

    @Test
    @DisplayName("?¨Ïö©???ëÎãµ Î≥Ä??- firstNameÍ≥?lastName??null??Í≤ΩÏö∞")
    fun `toUserResponse - should handle null firstName and lastName`() {

        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            firstName = null,
            lastName = null,
            roles = emptySet()
        )

        val result = UserMapper.toUserResponse(user)

        assertNotNull(result)
        assertNull(result.firstName)
        assertNull(result.lastName)
        assertTrue(result.roles.isEmpty())
    }

    @Test
    @DisplayName("?¨Ïö©???ëÎãµ Î≥Ä??- ?¨Îü¨ ??ï†??Í∞ÄÏß??¨Ïö©??)
    fun `toUserResponse - should handle user with multiple roles`() {

        val role1 = Role(name = "ROLE_USER")
        val role2 = Role(name = "ROLE_ADMIN")
        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            roles = setOf(role1, role2)
        )

        val result = UserMapper.toUserResponse(user)

        assertNotNull(result)
        assertEquals(2, result.roles.size)
        assertTrue(result.roles.contains("ROLE_USER"))
        assertTrue(result.roles.contains("ROLE_ADMIN"))
    }

    @Test
    @DisplayName("?ÑÎ°ú???ëÎãµ Î≥Ä??- UserÎ•?ProfileResponseÎ°?Î≥Ä??)
    fun `toProfileResponse - should convert User to ProfileResponse`() {

        val role = Role(name = "ROLE_USER")
        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            firstName = "John",
            lastName = "Doe",
            isActive = true,
            isEmailVerified = true,
            roles = setOf(role)
        )

        val result = UserMapper.toProfileResponse(user)

        assertNotNull(result)
        assertEquals(user.id, result.id)
        assertEquals(user.username, result.username)
        assertEquals(user.email, result.email)
        assertEquals(user.firstName, result.firstName)
        assertEquals(user.lastName, result.lastName)
        assertEquals(user.isActive, result.isActive)
        assertEquals(user.isEmailVerified, result.isEmailVerified)
        assertEquals(listOf("ROLE_USER"), result.roles)
    }

    @Test
    @DisplayName("?¨Ïö©???ïÎ≥¥ Î≥Ä??- UserÎ•?UserInfoÎ°?Î≥Ä??)
    fun `toUserInfo - should convert User to UserInfo`() {

        val role = Role(name = "ROLE_USER")
        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            firstName = "John",
            lastName = "Doe",
            roles = setOf(role)
        )

        val result = UserMapper.toUserInfo(user)

        assertNotNull(result)
        assertEquals(user.id, result.id)
        assertEquals(user.username, result.username)
        assertEquals(user.email, result.email)
        assertEquals(user.firstName, result.firstName)
        assertEquals(user.lastName, result.lastName)
        assertEquals(listOf("ROLE_USER"), result.roles)
    }

    @Test
    @DisplayName("?¨Ïö©???ïÎ≥¥ Î≥Ä??- UserInfo??isActive?Ä isEmailVerified ?ÑÎìúÍ∞Ä ?ÜÏùå")
    fun `toUserInfo - should not include isActive and isEmailVerified fields`() {

        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            isActive = true,
            isEmailVerified = false
        )

        val result = UserMapper.toUserInfo(user)

        assertNotNull(result)
        assertEquals(user.id, result.id)
        assertEquals(user.username, result.username)
    }

    @Test
    @DisplayName("?¨Ïö©???ïÎ≥¥ Î≥Ä??- ??ï†???ÜÎäî ?¨Ïö©??)
    fun `toUserInfo - should handle user without roles`() {

        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            roles = emptySet()
        )

        val result = UserMapper.toUserInfo(user)

        assertNotNull(result)
        assertTrue(result.roles.isEmpty())
    }
}
