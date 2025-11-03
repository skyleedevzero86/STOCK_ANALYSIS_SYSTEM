package com.sleekydz86.backend.global.security

import com.fasterxml.jackson.databind.ObjectMapper
import org.springframework.http.HttpStatus
import org.springframework.http.MediaType
import org.springframework.http.server.reactive.ServerHttpResponse
import org.springframework.security.core.AuthenticationException
import org.springframework.security.web.server.ServerAuthenticationEntryPoint
import org.springframework.stereotype.Component
import org.springframework.web.server.ServerWebExchange
import reactor.core.publisher.Mono
import java.time.LocalDateTime

@Component
class JwtAuthenticationEntryPoint(
    private val objectMapper: ObjectMapper
) : ServerAuthenticationEntryPoint {

    override fun commence(
        exchange: ServerWebExchange,
        ex: AuthenticationException
    ): Mono<Void> {
        val response: ServerHttpResponse = exchange.response
        response.statusCode = HttpStatus.UNAUTHORIZED
        response.headers.contentType = MediaType.APPLICATION_JSON

        val body = mapOf(
            "timestamp" to LocalDateTime.now().toString(),
            "status" to HttpStatus.UNAUTHORIZED.value(),
            "error" to "Unauthorized",
            "message" to "Authentication required",
            "path" to (exchange.request.path.toString())
        )

        val buffer = response.bufferFactory().wrap(
            objectMapper.writeValueAsBytes(body)
        )

        return response.writeWith(Mono.just(buffer))
    }
}
