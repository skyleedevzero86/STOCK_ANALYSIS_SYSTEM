package com.sleekydz86.backend.global.security

import jakarta.servlet.FilterChain
import jakarta.servlet.http.HttpServletRequest
import jakarta.servlet.http.HttpServletResponse
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken
import org.springframework.security.core.context.SecurityContextHolder
import org.springframework.security.core.userdetails.UserDetailsService
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource
import org.springframework.stereotype.Component
import org.springframework.web.filter.OncePerRequestFilter

@Component
class JwtAuthenticationFilter(
    private val jwtUtil: JwtUtil,
    private val userDetailsService: UserDetailsService
) : OncePerRequestFilter() {

    companion object {
        private const val BEARER_PREFIX = "Bearer "
        private const val AUTHORIZATION_HEADER = "Authorization"
    }

    override fun doFilterInternal(
        request: HttpServletRequest,
        response: HttpServletResponse,
        filterChain: FilterChain
    ) {
        val authHeader = request.getHeader(AUTHORIZATION_HEADER)

        if (authHeader != null && authHeader.startsWith(BEARER_PREFIX)) {
            val token = authHeader.substring(BEARER_PREFIX.length)

            if (jwtUtil.validateToken(token)) {
                val username = jwtUtil.extractUsername(token)
                val userDetails = userDetailsService.loadUserByUsername(username)

                if (jwtUtil.validateToken(token, userDetails)) {
                    val authToken = UsernamePasswordAuthenticationToken(
                        userDetails,
                        null,
                        userDetails.authorities
                    )
                    authToken.details = WebAuthenticationDetailsSource().buildDetails(request)
                    SecurityContextHolder.getContext().authentication = authToken
                }
            }
        }

        filterChain.doFilter(request, response)
    }
}
