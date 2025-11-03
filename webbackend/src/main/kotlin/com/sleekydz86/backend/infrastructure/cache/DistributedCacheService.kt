package com.sleekydz86.backend.infrastructure.cache

import com.fasterxml.jackson.databind.ObjectMapper
import org.springframework.data.redis.core.RedisTemplate
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration
import java.util.concurrent.TimeUnit
import org.slf4j.LoggerFactory

@Service
class DistributedCacheService(
    private val redisTemplate: RedisTemplate<String, Any>,
    private val objectMapper: ObjectMapper
) {
    private val logger = LoggerFactory.getLogger(DistributedCacheService::class.java)

    fun <T : Any> get(key: String, type: Class<T>): Mono<T> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().get(key)
        }
            .flatMap { value ->
                if (value != null) {
                    Mono.just(objectMapper.convertValue(value, type) as T)
                } else {
                    Mono.empty()
                }
            }
            .onErrorResume { error ->
                if (error.message?.contains("MOVED") == true) {
                    logger.debug("Redis cluster MOVED response for key: $key, will be handled by topology refresh", error)
                } else {
                    logger.warn("Redis get operation failed for key: $key, falling back to null", error)
                }
                Mono.empty()
            }
    }

    fun <T> set(key: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().set(key, value as Any, ttl.toMillis(), TimeUnit.MILLISECONDS)
            true
        }
            .onErrorResume { error ->
                if (error.message?.contains("MOVED") == true) {
                    logger.debug("Redis cluster MOVED response for key: $key, will be handled by topology refresh", error)
                } else {
                    logger.warn("Redis set operation failed for key: $key, continuing without cache", error)
                }
                Mono.just(false)
            }
    }

    fun <T> setIfAbsent(key: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().setIfAbsent(key, value as Any, ttl.toMillis(), TimeUnit.MILLISECONDS) ?: false
        }
            .onErrorResume { error ->
                logger.warn("Redis setIfAbsent operation failed for key: $key", error)
                Mono.just(false)
            }
    }

    fun delete(key: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.delete(key)
        }
            .onErrorResume { error ->
                logger.warn("Redis delete operation failed for key: $key", error)
                Mono.just(false)
            }
    }

    fun deletePattern(pattern: String): Mono<Long> {
        return Mono.fromCallable {
            val keys = redisTemplate.keys(pattern)
            if (keys.isNotEmpty()) {
                redisTemplate.delete(keys)
            } else {
                0L
            }
        }
            .onErrorResume { error ->
                logger.warn("Redis deletePattern operation failed for pattern: $pattern", error)
                Mono.just(0L)
            }
    }

    fun exists(key: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.hasKey(key)
        }
            .onErrorResume { error ->
                logger.warn("Redis exists operation failed for key: $key", error)
                Mono.just(false)
            }
    }

    fun expire(key: String, ttl: Duration): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.expire(key, ttl.toMillis(), TimeUnit.MILLISECONDS)
        }
            .onErrorResume { error ->
                logger.warn("Redis expire operation failed for key: $key", error)
                Mono.just(false)
            }
    }

    fun <T : Any> getOrSet(key: String, type: Class<T>, supplier: () -> Mono<T>, ttl: Duration = Duration.ofMinutes(30)): Mono<T> {
        return get(key, type)
            .switchIfEmpty(
                supplier()
                    .flatMap { value ->
                        set(key, value, ttl)
                            .then(Mono.just(value))
                    }
            )
            .onErrorResume { error ->
                logger.warn("Redis getOrSet operation failed for key: $key, falling back to supplier", error)
                supplier()
            }
    }

    fun <T : Any> getOrSetFlux(key: String, type: Class<T>, supplier: () -> Flux<T>, ttl: Duration = Duration.ofMinutes(30)): Flux<T> {
        return Mono.fromCallable {
            val value = redisTemplate.opsForValue().get(key)
            if (value != null) {
                val listType = objectMapper.typeFactory.constructCollectionType(List::class.java, type)
                @Suppress("UNCHECKED_CAST")
                objectMapper.convertValue(value, listType) as? List<T>
            } else {
                null
            }
        }
            .flatMapMany { cachedList ->
                if (cachedList != null) {
                    Flux.fromIterable(cachedList)
                } else {
                    supplier()
                        .collectList()
                        .flatMapMany { values ->
                            set(key, values, ttl)
                                .thenMany(Flux.fromIterable(values))
                        }
                }
            }
            .onErrorResume { error ->
                logger.warn("Redis getOrSetFlux operation failed for key: $key, falling back to supplier", error)
                supplier()
            }
    }

    fun increment(key: String, delta: Long = 1L): Mono<Long> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().increment(key, delta) ?: 0L
        }
            .onErrorResume { error ->
                logger.warn("Redis increment operation failed for key: $key", error)
                Mono.just(0L)
            }
    }

    fun decrement(key: String, delta: Long = 1L): Mono<Long> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().increment(key, -delta) ?: 0L
        }
            .onErrorResume { error ->
                logger.warn("Redis decrement operation failed for key: $key", error)
                Mono.just(0L)
            }
    }

    fun <T : Any> hashGet(hashKey: String, field: String, type: Class<T>): Mono<T> {
        return Mono.fromCallable {
            redisTemplate.opsForHash<String, Any>().get(hashKey, field)
        }
            .flatMap { value ->
                if (value != null) {
                    Mono.just(objectMapper.convertValue(value, type) as T)
                } else {
                    Mono.empty()
                }
            }
            .onErrorResume { error ->
                logger.warn("Redis hashGet operation failed for hashKey: $hashKey, field: $field", error)
                Mono.empty()
            }
    }

    fun <T> hashSet(hashKey: String, field: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForHash<String, Any>().put(hashKey, field, value as Any)
            redisTemplate.expire(hashKey, ttl.toMillis(), TimeUnit.MILLISECONDS)
            true
        }
            .onErrorResume { error ->
                logger.warn("Redis hashSet operation failed for hashKey: $hashKey", error)
                Mono.just(false)
            }
    }

    fun hashDelete(hashKey: String, field: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForHash<String, Any>().delete(hashKey, field)
            true
        }
            .onErrorResume { error ->
                logger.warn("Redis hashDelete operation failed for hashKey: $hashKey", error)
                Mono.just(false)
            }
    }

    fun <T> listPush(key: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Long> {
        return Mono.fromCallable {
            val result = redisTemplate.opsForList().rightPush(key, value as Any)
            redisTemplate.expire(key, ttl.toMillis(), TimeUnit.MILLISECONDS)
            result ?: 0L
        }
            .onErrorResume { error ->
                logger.warn("Redis listPush operation failed for key: $key", error)
                Mono.just(0L)
            }
    }

    fun <T : Any> listPop(key: String, type: Class<T>): Mono<T> {
        return Mono.fromCallable {
            redisTemplate.opsForList().leftPop(key)
        }
            .flatMap { value ->
                if (value != null) {
                    Mono.just(objectMapper.convertValue(value, type) as T)
                } else {
                    Mono.empty()
                }
            }
            .onErrorResume { error ->
                logger.warn("Redis listPop operation failed for key: $key", error)
                Mono.empty()
            }
    }

    fun <T> listRange(key: String, start: Long, end: Long, type: Class<T>): Flux<T> {
        return Mono.fromCallable {
            redisTemplate.opsForList().range(key, start, end)
        }
            .flatMapMany { values ->
                Flux.fromIterable(values.map { objectMapper.convertValue(it, type) })
            }
            .onErrorResume { error ->
                logger.warn("Redis listRange operation failed for key: $key", error)
                Flux.empty()
            }
    }

    fun setAdd(key: String, value: Any, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            val result = redisTemplate.opsForSet().add(key, value)
            redisTemplate.expire(key, ttl.toMillis(), TimeUnit.MILLISECONDS)
            (result ?: 0L) > 0
        }
            .onErrorResume { error ->
                logger.warn("Redis setAdd operation failed for key: $key", error)
                Mono.just(false)
            }
    }

    fun setMembers(key: String, type: Class<*>): Flux<Any> {
        return Mono.fromCallable {
            redisTemplate.opsForSet().members(key)
        }
            .flatMapMany { members ->
                Flux.fromIterable(members ?: emptySet())
            }
            .onErrorResume { error ->
                logger.warn("Redis setMembers operation failed for key: $key", error)
                Flux.empty()
            }
    }

    fun setRemove(key: String, value: Any): Mono<Boolean> {
        return Mono.fromCallable {
            val result = redisTemplate.opsForSet().remove(key, value)
            (result ?: 0L) > 0
        }
            .onErrorResume { error ->
                logger.warn("Redis setRemove operation failed for key: $key", error)
                Mono.just(false)
            }
    }
}