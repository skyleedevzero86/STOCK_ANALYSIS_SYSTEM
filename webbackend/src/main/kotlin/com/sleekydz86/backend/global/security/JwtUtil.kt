package com.sleekydz86.backend.global.security

import io.jsonwebtoken.*
import io.jsonwebtoken.security.Keys
import org.springframework.beans.factory.annotation.Value
import org.springframework.security.core.userdetails.UserDetails
import org.springframework.stereotype.Component
import java.security.Key
import java.util.*

@Component
class JwtUtil {

    @Value("\${jwt.secret}")
    private lateinit var secret: String

    @Value("\${jwt.expiration}")
    private var expiration: Long = 0

    private val key: Key by lazy {
        Keys.hmacShaKeyFor(secret.toByteArray())
    }

    fun generateToken(userDetails: UserDetails): String {
        val claims = mapOf(
            "sub" to userDetails.username,
            "iat" to Date(),
            "exp" to Date(System.currentTimeMillis() + expiration * 1000)
        )
        return createToken(claims, userDetails.username)
    }

    fun generateToken(username: String, roles: List<String>): String {
        val claims = mapOf(
            "sub" to username,
            "roles" to roles,
            "iat" to Date(),
            "exp" to Date(System.currentTimeMillis() + expiration * 1000)
        )
        return createToken(claims, username)
    }

    fun generateRefreshToken(username: String): String {
        val claims = mapOf(
            "sub" to username,
            "type" to "refresh",
            "iat" to Date(),
            "exp" to Date(System.currentTimeMillis() + expiration * 24 * 7 * 1000)
        )
        return createToken(claims, username)
    }

    private fun createToken(claims: Map<String, Any>, subject: String): String {
        return Jwts.builder()
            .setClaims(claims)
            .setSubject(subject)
            .setIssuedAt(Date())
            .setExpiration(Date(System.currentTimeMillis() + expiration * 1000))
            .signWith(key, SignatureAlgorithm.HS512)
            .compact()
    }

    fun extractUsername(token: String): String {
        return extractClaim(token, Claims::getSubject)
    }

    fun extractExpiration(token: String): Date {
        return extractClaim(token, Claims::getExpiration)
    }

    fun extractRoles(token: String): List<String> {
        val claims = extractAllClaims(token)
        return claims["roles"] as? List<String> ?: emptyList()
    }

    fun <T> extractClaim(token: String, claimsResolver: (Claims) -> T): T {
        val claims = extractAllClaims(token)
        return claimsResolver(claims)
    }

    private fun extractAllClaims(token: String): Claims {
        return Jwts.parserBuilder()
            .setSigningKey(key)
            .build()
            .parseClaimsJws(token)
            .body
    }

    fun isTokenExpired(token: String): Boolean {
        return extractExpiration(token).before(Date())
    }

    fun validateToken(token: String, userDetails: UserDetails): Boolean {
        val username = extractUsername(token)
        return username == userDetails.username && !isTokenExpired(token)
    }

    fun validateToken(token: String): Boolean {
        return try {
            Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
            true
        } catch (e: JwtException) {
            false
        }
    }
}
