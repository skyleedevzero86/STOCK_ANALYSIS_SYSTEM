package com.sleekydz86.backend.global.config

import io.swagger.v3.oas.models.OpenAPI
import io.swagger.v3.oas.models.info.Info
import io.swagger.v3.oas.models.info.Contact
import io.swagger.v3.oas.models.servers.Server
import io.swagger.v3.oas.models.security.SecurityRequirement
import io.swagger.v3.oas.models.security.SecurityScheme
import io.swagger.v3.oas.models.Components
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class SwaggerConfig {

    @Bean
    fun openAPI(): OpenAPI {
        return OpenAPI()
            .info(
                Info()
                    .title("주식 분석 시스템 API")
                    .description("실시간 주식 데이터 분석 및 알림 시스템 REST API 문서")
                    .version("1.0.0")
                    .contact(
                        Contact()
                            .name("개발팀")
                    )
            )
            .servers(
                listOf(
                    Server().url("http://localhost:8080").description("로컬 개발 서버"),
                    Server().url("https://api.example.com").description("프로덕션 서버")
                )
            )
            .components(
                Components()
                    .addSecuritySchemes(
                        "bearerAuth",
                        SecurityScheme()
                            .type(SecurityScheme.Type.HTTP)
                            .scheme("bearer")
                            .bearerFormat("JWT")
                            .description("JWT 토큰을 입력하세요. 형식: Bearer {token}")
                    )
            )
            .addSecurityItem(
                SecurityRequirement().addList("bearerAuth")
            )
    }
}


