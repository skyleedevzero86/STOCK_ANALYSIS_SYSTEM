package com.sleekydz86.backend.infrastructure.cache

import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.data.redis.connection.RedisClusterConfiguration
import org.springframework.data.redis.connection.RedisConnectionFactory
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory
import org.springframework.data.redis.core.RedisTemplate
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer
import org.springframework.data.redis.serializer.StringRedisSerializer
import org.springframework.scheduling.annotation.EnableScheduling
import java.time.Duration

@Configuration
@EnableScheduling
class RedisClusterConfig {

    @Value("\${spring.redis.cluster.nodes:localhost:7000,localhost:7001,localhost:7002}")
    private lateinit var clusterNodes: String

    @Value("\${spring.redis.cluster.max-redirects:3}")
    private var maxRedirects: Int = 3

    @Value("\${spring.redis.cluster.timeout:2000}")
    private var timeout: Long = 2000

    @Bean
    fun redisClusterConfiguration(): RedisClusterConfiguration {
        val clusterConfig = RedisClusterConfiguration()
        clusterConfig.clusterNodes = clusterNodes.split(",").map { node ->
            val parts = node.trim().split(":")
            org.springframework.data.redis.connection.RedisClusterNode(parts[0], parts[1].toInt())
        }
        clusterConfig.maxRedirects = maxRedirects
        return clusterConfig
    }

    @Bean
    fun redisConnectionFactory(clusterConfig: RedisClusterConfiguration): RedisConnectionFactory {
        return LettuceConnectionFactory(clusterConfig)
    }

    @Bean
    fun redisTemplate(connectionFactory: RedisConnectionFactory): RedisTemplate<String, Any> {
        val template = RedisTemplate<String, Any>()
        template.connectionFactory = connectionFactory
        template.keySerializer = StringRedisSerializer()
        template.valueSerializer = GenericJackson2JsonRedisSerializer()
        template.hashKeySerializer = StringRedisSerializer()
        template.hashValueSerializer = GenericJackson2JsonRedisSerializer()
        template.afterPropertiesSet()
        return template
    }
}