package com.sleekydz86.backend.application.controller

import io.swagger.v3.oas.annotations.Operation
import io.swagger.v3.oas.annotations.responses.ApiResponse
import io.swagger.v3.oas.annotations.responses.ApiResponses
import io.swagger.v3.oas.annotations.tags.Tag
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/public")
@Tag(name = "공개 API", description = "인증 없이 접근 가능한 공개 API")
class PublicController {

    @GetMapping("/health")
    @Operation(summary = "서비스 상태 확인", description = "서비스의 현재 상태를 확인합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "서비스가 정상적으로 동작 중입니다")
        ]
    )
    fun health(): Map<String, String> {
        return mapOf(
            "status" to "UP",
            "service" to "Stock Analysis System",
            "version" to "1.0.0"
        )
    }

    @GetMapping("/info")
    @Operation(summary = "서비스 정보 조회", description = "서비스의 기본 정보 및 기능 목록을 조회합니다")
    @ApiResponses(
        value = [
            ApiResponse(responseCode = "200", description = "성공적으로 서비스 정보를 조회했습니다")
        ]
    )
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
