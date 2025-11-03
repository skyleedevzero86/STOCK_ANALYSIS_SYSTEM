package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.Role
import com.sleekydz86.backend.domain.repository.RoleRepository
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.util.*

class RoleServiceTest {

    private lateinit var roleRepository: RoleRepository
    private lateinit var roleService: RoleService

    @BeforeEach
    fun setUp() {
        roleRepository = mockk()
        roleService = RoleService(roleRepository)
    }

    @Test
    fun `findByName - should return role when exists`() {
        //given
        val roleName = "ROLE_USER"
        val role = Role(
            id = 1L,
            name = roleName,
            description = "User role",
            isActive = true
        )

        every { roleRepository.findByName(roleName) } returns Optional.of(role)

        //when
        val result = roleService.findByName(roleName)

        //then
        assertNotNull(result)
        assertEquals(role, result)
        assertEquals(roleName, result?.name)
        verify(exactly = 1) { roleRepository.findByName(roleName) }
    }

    @Test
    fun `findByName - should return null when role not found`() {
        //given
        val roleName = "ROLE_NONEXISTENT"

        every { roleRepository.findByName(roleName) } returns Optional.empty()

        //when
        val result = roleService.findByName(roleName)

        //then
        assertNull(result)
        verify(exactly = 1) { roleRepository.findByName(roleName) }
    }

    @Test
    fun `save - should save and return role`() {
        //given
        val role = Role(
            id = 1L,
            name = "ROLE_USER",
            description = "User role",
            isActive = true
        )

        every { roleRepository.save(role) } returns role

        //when
        val result = roleService.save(role)

        //then
        assertNotNull(result)
        assertEquals(role, result)
        verify(exactly = 1) { roleRepository.save(role) }
    }

    @Test
    fun `createRole - should create role with name and description`() {
        //given
        val roleName = "ROLE_ADMIN"
        val roleDescription = "Administrator role"
        val role = Role(
            id = 1L,
            name = roleName,
            description = roleDescription,
            isActive = true
        )

        every { roleRepository.save(any()) } answers { firstArg<Role>().copy(id = 1L) }

        //when
        val result = roleService.createRole(roleName, roleDescription)

        //then
        assertNotNull(result)
        assertEquals(roleName, result.name)
        assertEquals(roleDescription, result.description)
        verify(exactly = 1) { roleRepository.save(any()) }
    }

    @Test
    fun `createRole - should create role without description`() {
        //given
        val roleName = "ROLE_USER"
        val role = Role(
            id = 1L,
            name = roleName,
            description = null,
            isActive = true
        )

        every { roleRepository.save(any()) } answers { firstArg<Role>().copy(id = 1L) }

        //when
        val result = roleService.createRole(roleName)

        //then
        assertNotNull(result)
        assertEquals(roleName, result.name)
        assertNull(result.description)
        verify(exactly = 1) { roleRepository.save(any()) }
    }

    @Test
    fun `getAllActiveRoles - should return list of active roles`() {
        //given
        val activeRoles = listOf(
            Role(id = 1L, name = "ROLE_USER", description = "User role", isActive = true),
            Role(id = 2L, name = "ROLE_ADMIN", description = "Admin role", isActive = true)
        )

        every { roleRepository.findByIsActiveTrue() } returns activeRoles

        //when
        val result = roleService.getAllActiveRoles()

        //then
        assertNotNull(result)
        assertEquals(2, result.size)
        assertTrue(result.all { it.isActive })
        verify(exactly = 1) { roleRepository.findByIsActiveTrue() }
    }

    @Test
    fun `getAllActiveRoles - should return empty list when no active roles`() {
        //given
        val emptyList = emptyList<Role>()

        every { roleRepository.findByIsActiveTrue() } returns emptyList

        //when
        val result = roleService.getAllActiveRoles()

        //then
        assertNotNull(result)
        assertTrue(result.isEmpty())
        verify(exactly = 1) { roleRepository.findByIsActiveTrue() }
    }

    @Test
    fun `existsByName - should return true when role exists`() {
        //given
        val roleName = "ROLE_USER"

        every { roleRepository.existsByName(roleName) } returns true

        //when
        val result = roleService.existsByName(roleName)

        //then
        assertTrue(result)
        verify(exactly = 1) { roleRepository.existsByName(roleName) }
    }

    @Test
    fun `existsByName - should return false when role not exists`() {
        //given
        val roleName = "ROLE_NONEXISTENT"

        every { roleRepository.existsByName(roleName) } returns false

        //when
        val result = roleService.existsByName(roleName)

        //then
        assertFalse(result)
        verify(exactly = 1) { roleRepository.existsByName(roleName) }
    }

    @Test
    fun `findByNameWithPermissions - should return role with permissions`() {
        //given
        val roleName = "ROLE_ADMIN"
        val role = Role(
            id = 1L,
            name = roleName,
            description = "Admin role",
            isActive = true
        )

        every { roleRepository.findByNameWithPermissions(roleName) } returns Optional.of(role)

        //when
        val result = roleService.findByNameWithPermissions(roleName)

        //then
        assertNotNull(result)
        assertEquals(role, result)
        verify(exactly = 1) { roleRepository.findByNameWithPermissions(roleName) }
    }

    @Test
    fun `findByNameWithPermissions - should return null when role not found`() {
        //given
        val roleName = "ROLE_NONEXISTENT"

        every { roleRepository.findByNameWithPermissions(roleName) } returns Optional.empty()

        //when
        val result = roleService.findByNameWithPermissions(roleName)

        //then
        assertNull(result)
        verify(exactly = 1) { roleRepository.findByNameWithPermissions(roleName) }
    }
}
