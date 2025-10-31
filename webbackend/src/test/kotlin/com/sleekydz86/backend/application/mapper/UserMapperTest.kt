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
    @DisplayName("사용자 응답 변환 - User를 UserResponse로 변환")
    fun `toUserResponse - should convert User to UserResponse`() {
        //given
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

        //when
        val result = UserMapper.toUserResponse(user)

        //then
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
    @DisplayName("사용자 응답 변환 - firstName과 lastName이 null인 경우")
    fun `toUserResponse - should handle null firstName and lastName`() {
        //given
        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            firstName = null,
            lastName = null,
            roles = emptySet()
        )

        //when
        val result = UserMapper.toUserResponse(user)

        //then
        assertNotNull(result)
        assertNull(result.firstName)
        assertNull(result.lastName)
        assertTrue(result.roles.isEmpty())
    }

    @Test
    @DisplayName("사용자 응답 변환 - 여러 역할을 가진 사용자")
    fun `toUserResponse - should handle user with multiple roles`() {
        //given
        val role1 = Role(name = "ROLE_USER")
        val role2 = Role(name = "ROLE_ADMIN")
        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            roles = setOf(role1, role2)
        )

        //when
        val result = UserMapper.toUserResponse(user)

        //then
        assertNotNull(result)
        assertEquals(2, result.roles.size)
        assertTrue(result.roles.contains("ROLE_USER"))
        assertTrue(result.roles.contains("ROLE_ADMIN"))
    }

    @Test
    @DisplayName("프로필 응답 변환 - User를 ProfileResponse로 변환")
    fun `toProfileResponse - should convert User to ProfileResponse`() {
        //given
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

        //when
        val result = UserMapper.toProfileResponse(user)

        //then
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
    @DisplayName("사용자 정보 변환 - User를 UserInfo로 변환")
    fun `toUserInfo - should convert User to UserInfo`() {
        //given
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

        //when
        val result = UserMapper.toUserInfo(user)

        //then
        assertNotNull(result)
        assertEquals(user.id, result.id)
        assertEquals(user.username, result.username)
        assertEquals(user.email, result.email)
        assertEquals(user.firstName, result.firstName)
        assertEquals(user.lastName, result.lastName)
        assertEquals(listOf("ROLE_USER"), result.roles)
    }

    @Test
    @DisplayName("사용자 정보 변환 - UserInfo는 isActive와 isEmailVerified 필드가 없음")
    fun `toUserInfo - should not include isActive and isEmailVerified fields`() {
        //given
        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            isActive = true,
            isEmailVerified = false
        )

        //when
        val result = UserMapper.toUserInfo(user)

        //then
        assertNotNull(result)
        assertEquals(user.id, result.id)
        assertEquals(user.username, result.username)
    }

    @Test
    @DisplayName("사용자 정보 변환 - 역할이 없는 사용자")
    fun `toUserInfo - should handle user without roles`() {
        //given
        val user = User(
            id = 1L,
            username = "testuser",
            email = "test@example.com",
            password = "encodedPassword",
            roles = emptySet()
        )

        //when
        val result = UserMapper.toUserInfo(user)

        //then
        assertNotNull(result)
        assertTrue(result.roles.isEmpty())
    }
}
