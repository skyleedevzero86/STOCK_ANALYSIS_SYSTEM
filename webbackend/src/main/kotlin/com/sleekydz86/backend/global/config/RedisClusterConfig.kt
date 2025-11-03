package com.sleekydz86.backend.global.config

import org.springframework.beans.factory.annotation.Value
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.data.redis.connection.RedisClusterConfiguration
import org.springframework.data.redis.connection.RedisConnectionFactory
import org.springframework.data.redis.connection.RedisStandaloneConfiguration
import org.springframework.data.redis.connection.lettuce.LettuceClientConfiguration
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory
import org.springframework.data.redis.core.RedisTemplate
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer
import org.springframework.data.redis.serializer.StringRedisSerializer
import org.springframework.scheduling.annotation.EnableScheduling
import org.slf4j.LoggerFactory
import io.lettuce.core.cluster.ClusterClientOptions
import io.lettuce.core.cluster.ClusterTopologyRefreshOptions
import java.time.Duration

@Configuration
@EnableScheduling
@ConditionalOnProperty(name = ["spring.redis.enabled"], havingValue = "true", matchIfMissing = true)
class RedisClusterConfig {

    private val logger = LoggerFactory.getLogger(RedisClusterConfig::class.java)

    @Value("\${spring.redis.host:localhost}")
    private var redisHost: String = "localhost"

    @Value("\${spring.redis.port:7000}")
    private var redisPort: Int = 7000

    @Value("\${spring.redis.cluster.enabled:false}")
    private var clusterEnabled: Boolean = false

    @Value("\${spring.redis.cluster.nodes:localhost:7000,localhost:7001,localhost:7002}")
    private lateinit var clusterNodes: String

    @Value("\${spring.redis.cluster.max-redirects:3}")
    private var maxRedirects: Int = 3

    @Value("\${spring.redis.cluster.timeout:2000}")
    private var timeout: Long = 2000

    @Bean
    fun redisConnectionFactory(): RedisConnectionFactory {
        return try {
            val factory = if (clusterEnabled) {
                logger.info("Initializing Redis cluster mode with nodes: $clusterNodes")
                val nodes = clusterNodes.split(",").map { it.trim() }
                val clusterConfig = RedisClusterConfiguration(nodes)
                clusterConfig.setMaxRedirects(maxRedirects)
                
                val topologyRefreshOptions = ClusterTopologyRefreshOptions.builder()
                    .enableAdaptiveRefreshTrigger(
                        ClusterTopologyRefreshOptions.RefreshTrigger.MOVED_REDIRECT,
                        ClusterTopologyRefreshOptions.RefreshTrigger.PERSISTENT_RECONNECTS
                    )
                    .enablePeriodicRefresh(Duration.ofSeconds(30))
                    .build()
                
                val clientOptions = ClusterClientOptions.builder()
                    .topologyRefreshOptions(topologyRefreshOptions)
                    .validateClusterNodeMembership(true)
                    .build()
                
                val clientConfig = LettuceClientConfiguration.builder()
                    .clientOptions(clientOptions)
                    .build()
                
                LettuceConnectionFactory(clusterConfig, clientConfig)
            } else {
                logger.info("Initializing Redis standalone mode with host: $redisHost, port: $redisPort")
                val standaloneConfig = RedisStandaloneConfiguration(redisHost, redisPort)
                LettuceConnectionFactory(standaloneConfig)
            }
            
            factory.afterPropertiesSet()
            logger.info("Redis connection factory initialized successfully")
            factory
        } catch (e: Exception) {
            logger.warn("Redis connection factory initialization failed, but continuing without Redis: ${e.message}", e)

            try {
                val fallbackConfig = RedisStandaloneConfiguration("localhost", 7000)
                LettuceConnectionFactory(fallbackConfig)
            } catch (ex: Exception) {
                logger.error("Redis fallback initialization also failed", ex)
                throw ex
            }
        }
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
            logger.warn("Redis template initialization failed, but continuing without Redis: ${e.message}", e)
        }
        return template
    }
}