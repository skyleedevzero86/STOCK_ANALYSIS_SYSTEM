package com.sleekydz86.backend.global.config

import com.sleekydz86.backend.global.security.JwtAuthenticationEntryPoint
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.security.authentication.AuthenticationManager
import org.springframework.security.authentication.dao.DaoAuthenticationProvider
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration
import org.springframework.security.config.annotation.method.configuration.EnableReactiveMethodSecurity
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity
import org.springframework.security.config.web.server.ServerHttpSecurity
import org.springframework.security.core.userdetails.UserDetailsService
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder
import org.springframework.security.crypto.password.PasswordEncoder
import org.springframework.security.web.server.SecurityWebFilterChain
import org.springframework.web.cors.reactive.CorsConfigurationSource
import org.springframework.context.annotation.Lazy

@Configuration
@EnableWebFluxSecurity
@EnableReactiveMethodSecurity
class SecurityConfig(
    @Lazy private val userDetailsService: UserDetailsService,
    private val jwtAuthenticationEntryPoint: JwtAuthenticationEntryPoint,
    private val corsConfigurationSource: CorsConfigurationSource
) {

    @Bean
    fun passwordEncoder(): PasswordEncoder {
        return BCryptPasswordEncoder()
    }

    @Bean
    fun authenticationProvider(): DaoAuthenticationProvider {
        val authProvider = DaoAuthenticationProvider()
        authProvider.setUserDetailsService(userDetailsService)
        authProvider.setPasswordEncoder(passwordEncoder())
        return authProvider
    }

    @Bean
    fun authenticationManager(config: AuthenticationConfiguration): AuthenticationManager {
        return config.authenticationManager
    }

    @Bean
    fun springSecurityFilterChain(http: ServerHttpSecurity): SecurityWebFilterChain {
        return http
            .csrf { it.disable() }
            .cors { it.configurationSource(corsConfigurationSource) }
            .exceptionHandling { exceptions ->
                exceptions.authenticationEntryPoint(jwtAuthenticationEntryPoint)
            }
            .authorizeExchange { exchanges ->
                exchanges
                    .pathMatchers("/", "/admin-dashboard", "/admin-login", "/api-view",
                                 "/email-subscription", "/template-management").permitAll()
                    .pathMatchers("/css/**", "/js/**", "/*.html", "/*.css", "/*.js",
                                 "/*.png", "/*.jpg", "/*.gif", "/*.ico",
                                 "/*.svg").permitAll()
                    .pathMatchers("/api/auth/**").permitAll()
                    .pathMatchers("/api/public/**").permitAll()
                    .pathMatchers("/ws/**").permitAll()
                    .pathMatchers("/actuator/health").permitAll()
                    .pathMatchers("/api/stocks/**").permitAll()
                    .pathMatchers("/api/cqrs/stocks/**").permitAll()
                    .pathMatchers("/api/admin/**").hasRole("ADMIN")
                    .pathMatchers("/api/email-subscriptions/**").hasAnyRole("USER", "ADMIN")
                    .pathMatchers("/api/templates/**").hasRole("ADMIN")
                    .pathMatchers("/api/ai-analysis/**").hasAnyRole("USER", "ADMIN")
                    .pathMatchers("/api/ai-email/**").hasRole("ADMIN")
                    .anyExchange().authenticated()
            }
            .build()
    }
}
