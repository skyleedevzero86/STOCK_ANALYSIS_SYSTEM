package com.sleekydz86.backend.global.security

import com.fasterxml.jackson.databind.ObjectMapper
import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse
import org.springframework.http.MediaType
import org.springframework.security.core.AuthenticationException
import org.springframework.security.web.AuthenticationEntryPoint
import org.springframework.stereotype.Component

@Component
class JwtAuthenticationEntryPoint : AuthenticationEntryPoint {

    override fun commence(
        request: HttpServletRequest,
        response: HttpServletResponse,
        authException: AuthenticationException
    ) {
        response.contentType = MediaType.APPLICATION_JSON_VALUE
        response.status = HttpServletResponse.SC_UNAUTHORIZED

        val body = mapOf(
            "status" to HttpServletResponse.SC_UNAUTHORIZED,
            "error" to "Unauthorized",
            "message" to "Authentication required",
            "path" to request.servletPath
        )

        ObjectMapper().writeValue(response.outputStream, body)
    }
}
