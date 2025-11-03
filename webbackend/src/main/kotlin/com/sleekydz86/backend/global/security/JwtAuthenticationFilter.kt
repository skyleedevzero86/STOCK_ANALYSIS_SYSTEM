package com.sleekydz86.backend.global.security

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken
import org.springframework.security.core.context.ReactiveSecurityContextHolder
import org.springframework.security.core.context.SecurityContext
import org.springframework.security.core.context.SecurityContextImpl
import org.springframework.security.core.userdetails.UserDetailsService
import org.springframework.stereotype.Component
import org.springframework.web.server.ServerWebExchange
import org.springframework.web.server.WebFilter
import org.springframework.web.server.WebFilterChain
import reactor.core.publisher.Mono

@Component
class JwtAuthenticationFilter(
    private val jwtUtil: JwtUtil,
    private val userDetailsService: UserDetailsService
) : WebFilter {

    companion object {
        private const val BEARER_PREFIX = "Bearer "
        private const val AUTHORIZATION_HEADER = "Authorization"
    }

    override fun filter(exchange: ServerWebExchange, chain: WebFilterChain): Mono<Void> {
        val authHeader = exchange.request.headers.getFirst(AUTHORIZATION_HEADER)

        if (authHeader != null && authHeader.startsWith(BEARER_PREFIX)) {
            val token = authHeader.substring(BEARER_PREFIX.length)

            if (jwtUtil.validateToken(token)) {
                return Mono.fromCallable {
                    jwtUtil.extractUsername(token)
                }
                .flatMap { username ->
                    Mono.fromCallable {
                        userDetailsService.loadUserByUsername(username)
                    }
                    .flatMap { userDetails ->
                        if (jwtUtil.validateToken(token, userDetails)) {
                            val authToken = UsernamePasswordAuthenticationToken(
                                userDetails,
                                null,
                                userDetails.authorities
                            )
                            
                            val securityContext: SecurityContext = SecurityContextImpl().apply {
                                authentication = authToken
                            }
                            
                            chain.filter(exchange)
                                .contextWrite(ReactiveSecurityContextHolder.withSecurityContext(Mono.just(securityContext)))
                        } else {
                            chain.filter(exchange)
                        }
                    }
                }
                .onErrorResume {
                    chain.filter(exchange)
                }
            }
        }

        return chain.filter(exchange)
    }
}
