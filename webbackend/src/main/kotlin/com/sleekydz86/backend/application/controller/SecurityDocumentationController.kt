package com.sleekydz86.backend.application.controller

import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/security-docs")
class SecurityDocumentationController {

    @GetMapping("/endpoints")
    fun getSecurityEndpoints(): Map<String, Any> {
        return mapOf(
            "authentication" to mapOf(
                "login" to mapOf(
                    "method" to "POST",
                    "url" to "/api/auth/login",
                    "body" to mapOf(
                        "username" to "string",
                        "password" to "string"
                    )
                ),
                "register" to mapOf(
                    "method" to "POST",
                    "url" to "/api/auth/register",
                    "body" to mapOf(
                        "username" to "string",
                        "email" to "string",
                        "password" to "string",
                        "firstName" to "string (optional)",
                        "lastName" to "string (optional)"
                    )
                ),
                "refresh" to mapOf(
                    "method" to "POST",
                    "url" to "/api/auth/refresh",
                    "body" to mapOf(
                        "refreshToken" to "string"
                    )
                )
            ),
            "authorization" to mapOf(
                "public" to listOf(
                    "/api/public/**",
                    "/api/stocks/symbols",
                    "/api/auth/**"
                ),
                "user" to listOf(
                    "/api/stocks/realtime/**",
                    "/api/stocks/analysis/**",
                    "/api/stocks/historical/**",
                    "/api/email-subscriptions/**",
                    "/api/profile/**"
                ),
                "admin" to listOf(
                    "/api/admin/**",
                    "/api/templates/**",
                    "/api/ai-email/**"
                )
            ),
            "roles" to mapOf(
                "USER" to "Can access stock data and analysis",
                "ADMIN" to "Can access all features including admin functions"
            ),
            "permissions" to mapOf(
                "STOCK_READ" to "Read stock data",
                "STOCK_WRITE" to "Write stock data",
                "ANALYSIS_READ" to "Read analysis data",
                "ANALYSIS_WRITE" to "Write analysis data",
                "USER_READ" to "Read user data",
                "USER_WRITE" to "Write user data",
                "ADMIN_READ" to "Read admin data",
                "ADMIN_WRITE" to "Write admin data",
                "EMAIL_READ" to "Read email data",
                "EMAIL_WRITE" to "Write email data",
                "TEMPLATE_READ" to "Read template data",
                "TEMPLATE_WRITE" to "Write template data"
            )
        )
    }

    @GetMapping("/test-credentials")
    fun getTestCredentials(): Map<String, Any> {
        return mapOf(
            "admin" to mapOf(
                "username" to "admin",
                "password" to "admin123",
                "roles" to listOf("ADMIN"),
                "permissions" to listOf("All permissions")
            ),
            "user" to mapOf(
                "username" to "user",
                "password" to "user123",
                "roles" to listOf("USER"),
                "permissions" to listOf("STOCK_READ", "ANALYSIS_READ", "EMAIL_READ")
            )
        )
    }

    @GetMapping("/security-headers")
    fun getSecurityHeaders(): Map<String, String> {
        return mapOf(
            "Authorization" to "Bearer <jwt_token>",
            "Content-Type" to "application/json",
            "X-Requested-With" to "XMLHttpRequest"
        )
    }
}
