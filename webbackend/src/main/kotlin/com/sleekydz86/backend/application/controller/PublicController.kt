package com.sleekydz86.backend.application.controller

import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/public")
class PublicController {

    @GetMapping("/health")
    fun health(): Map<String, String> {
        return mapOf(
            "status" to "UP",
            "service" to "Stock Analysis System",
            "version" to "1.0.0"
        )
    }

    @GetMapping("/info")
    fun info(): Map<String, Any> {
        return mapOf(
            "name" to "Stock Analysis System",
            "description" to "Real-time stock analysis and notification system",
            "version" to "1.0.0",
            "features" to listOf(
                "Real-time stock data",
                "Technical analysis",
                "Email notifications",
                "WebSocket support",
                "OAuth2 + JWT authentication",
                "Role-based access control"
            )
        )
    }
}
