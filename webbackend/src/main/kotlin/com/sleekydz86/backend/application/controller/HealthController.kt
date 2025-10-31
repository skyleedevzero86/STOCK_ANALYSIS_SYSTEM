package com.sleekydz86.backend.application.controller

import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController
import reactor.core.publisher.Mono
import java.time.LocalDateTime

@RestController
@RequestMapping("/api/health")
class HealthController(
    private val circuitBreakerManager: CircuitBreakerManager
) {

    @GetMapping
    fun health(): Mono<Map<String, Any>> {
        return Mono.just(mapOf(
            "status" to "UP",
            "timestamp" to LocalDateTime.now(),
            "circuitBreakers" to circuitBreakerManager.getAllCircuitBreakerStatus()
        ))
    }

    @GetMapping("/detailed")
    fun detailedHealth(): Mono<Map<String, Any>> {
        return Mono.just(mapOf(
            "status" to "UP",
            "timestamp" to LocalDateTime.now(),
            "application" to "Stock Analysis System",
            "version" to "1.0.0",
            "circuitBreakers" to circuitBreakerManager.getAllCircuitBreakerStatus(),
            "system" to mapOf(
                "javaVersion" to System.getProperty("java.version"),
                "osName" to System.getProperty("os.name"),
                "availableProcessors" to Runtime.getRuntime().availableProcessors(),
                "freeMemory" to Runtime.getRuntime().freeMemory(),
                "totalMemory" to Runtime.getRuntime().totalMemory(),
                "maxMemory" to Runtime.getRuntime().maxMemory()
            )
        ))
    }
}
