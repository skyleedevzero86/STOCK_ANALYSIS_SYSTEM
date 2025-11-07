package com.sleekydz86.backend.global.config

import com.sleekydz86.backend.global.security.JwtAuthenticationEntryPoint
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.security.authentication.AuthenticationManager
import org.springframework.security.authentication.ProviderManager
import org.springframework.security.authentication.dao.DaoAuthenticationProvider
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
    fun bCryptPasswordEncoder(): BCryptPasswordEncoder {
        return BCryptPasswordEncoder()
    }

    @Bean
    fun passwordEncoder(bCryptPasswordEncoder: BCryptPasswordEncoder): PasswordEncoder {
        return bCryptPasswordEncoder
    }

    @Bean
    fun authenticationProvider(passwordEncoder: PasswordEncoder): DaoAuthenticationProvider {
        val authProvider = DaoAuthenticationProvider()
        authProvider.setUserDetailsService(userDetailsService)
        authProvider.setPasswordEncoder(passwordEncoder)
        return authProvider
    }

    @Bean
    fun authenticationManager(authenticationProvider: DaoAuthenticationProvider): AuthenticationManager {
        return ProviderManager(listOf(authenticationProvider))
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
                                 "/email-subscription", "/template-management", "/news-detail").permitAll()
                    .pathMatchers("/css/**", "/js/**", "/*.html", "/*.css", "/*.js",
                                 "/*.png", "/*.jpg", "/*.gif", "/*.ico",
                                 "/*.svg").permitAll()
                    .pathMatchers("/api/auth/**").permitAll()
                    .pathMatchers("/api/public/**").permitAll()
                    .pathMatchers("/ws/**").permitAll()
                    .pathMatchers("/actuator/health").permitAll()
                    .pathMatchers("/api/stocks/**").permitAll()
                    .pathMatchers("/api/cqrs/stocks/**").permitAll()
                    .pathMatchers("/api/news/**").permitAll()
                    .pathMatchers("/api/admin/check-welcome-email", "/api/admin/check-daily-email", "/api/admin/save-notification-log").permitAll()
                    .pathMatchers("/api/admin/**").hasAnyRole("USER", "ADMIN")
                    .pathMatchers("/api/email-subscriptions/subscribe", "/api/email-subscriptions/unsubscribe", "/api/email-subscriptions/email-consent").permitAll()
                    .pathMatchers("/api/email-subscriptions/**").hasAnyRole("USER", "ADMIN")
                    .pathMatchers("/api/templates/**").permitAll()
                    .pathMatchers("/api/ai-analysis/**").hasAnyRole("USER", "ADMIN")
                    .pathMatchers("/api/ai-email/**").permitAll()
                    .anyExchange().authenticated()
            }
            .build()
    }
}
