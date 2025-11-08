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
                val isMovedError = error.message?.contains("MOVED") == true || 
                                  error.cause?.message?.contains("MOVED") == true
                if (isMovedError) {
                    logger.debug("Redis 클러스터 MOVED 응답: key=$key (자동 처리됨)")
                } else {
                    logger.warn("Redis get 작업 실패: key=$key, null로 대체합니다", error)
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
                val isMovedError = error.message?.contains("MOVED") == true || 
                                  error.cause?.message?.contains("MOVED") == true
                if (isMovedError) {
                    logger.debug("Redis 클러스터 MOVED 응답: key=$key (자동 처리됨)")
                    Mono.just(false)
                } else {
                    logger.warn("Redis set 작업 실패: key=$key, 캐시 없이 계속 진행합니다", error)
                    Mono.just(false)
                }
            }
    }

    fun <T> setIfAbsent(key: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().setIfAbsent(key, value as Any, ttl.toMillis(), TimeUnit.MILLISECONDS) ?: false
        }
            .onErrorResume { error ->
                logger.warn("Redis setIfAbsent 작업 실패: key=$key", error)
                Mono.just(false)
            }
    }

    fun delete(key: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.delete(key)
        }
            .onErrorResume { error ->
                logger.warn("Redis delete 작업 실패: key=$key", error)
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
                logger.warn("Redis deletePattern 작업 실패: pattern=$pattern", error)
                Mono.just(0L)
            }
    }

    fun exists(key: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.hasKey(key)
        }
            .onErrorResume { error ->
                logger.warn("Redis exists 작업 실패: key=$key", error)
                Mono.just(false)
            }
    }

    fun expire(key: String, ttl: Duration): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.expire(key, ttl.toMillis(), TimeUnit.MILLISECONDS)
        }
            .onErrorResume { error ->
                logger.warn("Redis expire 작업 실패: key=$key", error)
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
                logger.warn("Redis getOrSet 작업 실패: key=$key, supplier로 대체합니다", error)
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
                logger.warn("Redis getOrSetFlux 작업 실패: key=$key, supplier로 대체합니다", error)
                supplier()
            }
    }

    fun increment(key: String, delta: Long = 1L): Mono<Long> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().increment(key, delta) ?: 0L
        }
            .onErrorResume { error ->
                logger.warn("Redis increment 작업 실패: key=$key", error)
                Mono.just(0L)
            }
    }

    fun decrement(key: String, delta: Long = 1L): Mono<Long> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().increment(key, -delta) ?: 0L
        }
            .onErrorResume { error ->
                logger.warn("Redis decrement 작업 실패: key=$key", error)
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
                logger.warn("Redis hashGet 작업 실패: hashKey=$hashKey, field=$field", error)
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
                logger.warn("Redis hashSet 작업 실패: hashKey=$hashKey", error)
                Mono.just(false)
            }
    }

    fun hashDelete(hashKey: String, field: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForHash<String, Any>().delete(hashKey, field)
            true
        }
            .onErrorResume { error ->
                logger.warn("Redis hashDelete 작업 실패: hashKey=$hashKey", error)
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
                logger.warn("Redis listPush 작업 실패: key=$key", error)
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
                logger.warn("Redis listPop 작업 실패: key=$key", error)
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
                logger.warn("Redis listRange 작업 실패: key=$key", error)
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
                logger.warn("Redis setAdd 작업 실패: key=$key", error)
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
                logger.warn("Redis setMembers 작업 실패: key=$key", error)
                Flux.empty()
            }
    }

    fun setRemove(key: String, value: Any): Mono<Boolean> {
        return Mono.fromCallable {
            val result = redisTemplate.opsForSet().remove(key, value)
            (result ?: 0L) > 0
        }
            .onErrorResume { error ->
                logger.warn("Redis setRemove 작업 실패: key=$key", error)
                Mono.just(false)
            }
    }
}