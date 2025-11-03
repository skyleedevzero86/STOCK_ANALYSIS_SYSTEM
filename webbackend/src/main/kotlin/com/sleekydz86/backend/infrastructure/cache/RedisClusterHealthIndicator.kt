package com.sleekydz86.backend.infrastructure.cache

import org.springframework.boot.actuate.health.Health
import org.springframework.boot.actuate.health.HealthIndicator
import org.springframework.data.redis.connection.RedisConnectionFactory
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import java.time.Duration

@Component
class RedisClusterHealthIndicator(
    private val redisConnectionFactory: RedisConnectionFactory,
    private val distributedCacheService: DistributedCacheService
) : HealthIndicator {

    override fun health(): Health {
        return try {
            val connection = redisConnectionFactory.connection
            val isConnected = connection.ping() == "PONG"
            connection.close()

            if (isConnected) {
                Health.up()
                    .withDetail("status", "connected")
                    .withDetail("cluster", "healthy")
                    .build()
            } else {
                Health.down()
                    .withDetail("status", "disconnected")
                    .withDetail("cluster", "unhealthy")
                    .build()
            }
        } catch (e: Exception) {
            Health.down()
                .withDetail("status", "unavailable")
                .withDetail("message", "Redis connection failed, but application continues without cache")
                .withDetail("error", e.message)
                .build()
        }
    }

    fun getClusterInfo(): Mono<Map<String, Any>> {
        return distributedCacheService.get("cluster:info", Map::class.java)
            .map { it as Map<String, Any> }
            .switchIfEmpty(Mono.just(emptyMap()))
    }

    fun updateClusterInfo(info: Map<String, Any>): Mono<Boolean> {
        return distributedCacheService.set<Map<String, Any>>("cluster:info", info, Duration.ofMinutes(30))
    }

    fun getClusterNodes(): Mono<List<String>> {
        return distributedCacheService.get("cluster:nodes", List::class.java)
            .map { it as List<String> }
            .switchIfEmpty(Mono.just(emptyList()))
    }

    fun setClusterNodes(nodes: List<String>): Mono<Boolean> {
        return distributedCacheService.set<List<String>>("cluster:nodes", nodes, Duration.ofMinutes(30))
    }

    fun getClusterStats(): Mono<Map<String, Any>> {
        return distributedCacheService.get("cluster:stats", Map::class.java)
            .map { it as Map<String, Any> }
            .switchIfEmpty(Mono.just(emptyMap()))
    }

    fun updateClusterStats(stats: Map<String, Any>): Mono<Boolean> {
        return distributedCacheService.set<Map<String, Any>>("cluster:stats", stats, Duration.ofMinutes(30))
    }
}