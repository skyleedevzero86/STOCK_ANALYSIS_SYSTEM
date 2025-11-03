package com.sleekydz86.backend.global.config

import org.springframework.beans.factory.annotation.Value
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.data.redis.connection.RedisClusterConfiguration
import org.springframework.data.redis.connection.RedisConnectionFactory
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory
import org.springframework.data.redis.core.RedisTemplate
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer
import org.springframework.data.redis.serializer.StringRedisSerializer
import org.springframework.scheduling.annotation.EnableScheduling
import org.slf4j.LoggerFactory

@Configuration
@EnableScheduling
@ConditionalOnProperty(name = ["spring.redis.enabled"], havingValue = "true", matchIfMissing = true)
class RedisClusterConfig {

    private val logger = LoggerFactory.getLogger(RedisClusterConfig::class.java)

    @Value("\${spring.redis.cluster.nodes:localhost:7000,localhost:7001,localhost:7002}")
    private lateinit var clusterNodes: String

    @Value("\${spring.redis.cluster.max-redirects:3}")
    private var maxRedirects: Int = 3

    @Value("\${spring.redis.cluster.timeout:2000}")
    private var timeout: Long = 2000

    @Bean
    fun redisClusterConfiguration(): RedisClusterConfiguration {
        val nodes = clusterNodes.split(",").map { it.trim() }
        val clusterConfig = RedisClusterConfiguration(nodes)
        clusterConfig.setMaxRedirects(maxRedirects)
        logger.info("Redis cluster configuration initialized with nodes: $clusterNodes")
        return clusterConfig
    }

    @Bean
    fun redisConnectionFactory(clusterConfig: RedisClusterConfiguration): RedisConnectionFactory {
        val factory = LettuceConnectionFactory(clusterConfig)
        try {
            factory.afterPropertiesSet()
            logger.info("Redis connection factory initialized successfully")
        } catch (e: Exception) {
            logger.warn("Redis connection factory initialization failed, but continuing without Redis: ${e.message}")
        }
        return factory
    }

    @Bean
    fun redisTemplate(connectionFactory: RedisConnectionFactory): RedisTemplate<String, Any> {
        val template = RedisTemplate<String, Any>()
        template.setConnectionFactory(connectionFactory)
        template.keySerializer = StringRedisSerializer()
        template.valueSerializer = GenericJackson2JsonRedisSerializer()
        template.hashKeySerializer = StringRedisSerializer()
        template.hashValueSerializer = GenericJackson2JsonRedisSerializer()
        try {
            template.afterPropertiesSet()
            logger.info("Redis template initialized successfully")
        } catch (e: Exception) {
            logger.warn("Redis template initialization failed, but continuing without Redis: ${e.message}")
        }
        return template
    }
}