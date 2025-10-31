package com.sleekydz86.backend.application.mapper

import com.sleekydz86.backend.application.dto.ProfileResponse
import com.sleekydz86.backend.application.dto.UserInfo
import com.sleekydz86.backend.application.dto.UserResponse
import com.sleekydz86.backend.domain.model.User

object UserMapper {
    fun toUserResponse(user: User): UserResponse {
        return UserResponse(
            id = user.id,
            username = user.username,
            email = user.email,
            firstName = user.firstName,
            lastName = user.lastName,
            isActive = user.isActive,
            isEmailVerified = user.isEmailVerified,
            roles = user.roles.map { it.name }
        )
    }

    fun toProfileResponse(user: User): ProfileResponse {
        return ProfileResponse(
            id = user.id,
            username = user.username,
            email = user.email,
            firstName = user.firstName,
            lastName = user.lastName,
            isActive = user.isActive,
            isEmailVerified = user.isEmailVerified,
            roles = user.roles.map { it.name }
        )
    }

    fun toUserInfo(user: User): UserInfo {
        return UserInfo(
            id = user.id,
            username = user.username,
            email = user.email,
            firstName = user.firstName,
            lastName = user.lastName,
            roles = user.roles.map { it.name }
        )
    }
}

