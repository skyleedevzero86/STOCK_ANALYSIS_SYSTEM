package com.sleekydz86.backend.infrastructure.cache

import com.fasterxml.jackson.databind.ObjectMapper
import org.springframework.data.redis.core.RedisTemplate
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong
import org.slf4j.LoggerFactory

@Service
class DistributedCacheService(
    private val redisTemplate: RedisTemplate<String, Any>,
    private val objectMapper: ObjectMapper
) {
    private val logger = LoggerFactory.getLogger(DistributedCacheService::class.java)
    private val isConnected = AtomicBoolean(true)
    private val lastFailureTime = AtomicLong(0)
    private val failureCount = AtomicLong(0)
    private val logInterval = 300000L

    fun <T : Any> get(key: String, type: Class<T>): Mono<T> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().get(key)
        }
            .flatMap { value ->
                handleConnectionSuccess()
                if (value != null) {
                    Mono.just(objectMapper.convertValue(value, type) as T)
                } else {
                    Mono.empty()
                }
            }
            .onErrorResume { error ->
                handleConnectionError(error, "get", key)
                val isMovedError = error.message?.contains("MOVED") == true || 
                                  error.cause?.message?.contains("MOVED") == true
                if (isMovedError) {
                    logger.debug("Redis 클러스터 MOVED 응답: key=$key (자동 처리됨)")
                }
                Mono.empty()
            }
    }

    fun <T> set(key: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().set(key, value as Any, ttl.toMillis(), TimeUnit.MILLISECONDS)
            true
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "set", key)
                val isMovedError = error.message?.contains("MOVED") == true || 
                                  error.cause?.message?.contains("MOVED") == true
                if (isMovedError) {
                    logger.debug("Redis 클러스터 MOVED 응답: key=$key (자동 처리됨)")
                }
                Mono.just(false)
            }
    }

    fun <T> setIfAbsent(key: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().setIfAbsent(key, value as Any, ttl.toMillis(), TimeUnit.MILLISECONDS) ?: false
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "setIfAbsent", key)
                Mono.just(false)
            }
    }

    fun delete(key: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.delete(key)
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "delete", key)
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
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "deletePattern", pattern)
                Mono.just(0L)
            }
    }

    fun exists(key: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.hasKey(key)
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "exists", key)
                Mono.just(false)
            }
    }

    fun expire(key: String, ttl: Duration): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.expire(key, ttl.toMillis(), TimeUnit.MILLISECONDS)
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "expire", key)
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
                logger.debug("Redis getOrSet 작업 실패: key=$key, supplier로 대체합니다", error)
                supplier()
            }
    }

    fun <T : Any> getOrSetFlux(key: String, type: Class<T>, supplier: () -> Flux<T>, ttl: Duration = Duration.ofMinutes(30)): Flux<T> {
        return Mono.fromCallable {
            val value = redisTemplate.opsForValue().get(key)
            if (value != null) {
                handleConnectionSuccess()
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
                handleConnectionError(error, "getOrSetFlux", key)
                logger.debug("Redis getOrSetFlux 작업 실패: key=$key, supplier로 대체합니다", error)
                supplier()
            }
    }

    fun increment(key: String, delta: Long = 1L): Mono<Long> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().increment(key, delta) ?: 0L
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "increment", key)
                Mono.just(0L)
            }
    }

    fun decrement(key: String, delta: Long = 1L): Mono<Long> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().increment(key, -delta) ?: 0L
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "decrement", key)
                Mono.just(0L)
            }
    }

    fun <T : Any> hashGet(hashKey: String, field: String, type: Class<T>): Mono<T> {
        return Mono.fromCallable {
            redisTemplate.opsForHash<String, Any>().get(hashKey, field)
        }
            .flatMap { value ->
                handleConnectionSuccess()
                if (value != null) {
                    Mono.just(objectMapper.convertValue(value, type) as T)
                } else {
                    Mono.empty()
                }
            }
            .onErrorResume { error ->
                handleConnectionError(error, "hashGet", "$hashKey:$field")
                Mono.empty()
            }
    }

    fun <T> hashSet(hashKey: String, field: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForHash<String, Any>().put(hashKey, field, value as Any)
            redisTemplate.expire(hashKey, ttl.toMillis(), TimeUnit.MILLISECONDS)
            true
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "hashSet", hashKey)
                Mono.just(false)
            }
    }

    fun hashDelete(hashKey: String, field: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForHash<String, Any>().delete(hashKey, field)
            true
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "hashDelete", hashKey)
                Mono.just(false)
            }
    }

    fun <T> listPush(key: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Long> {
        return Mono.fromCallable {
            val result = redisTemplate.opsForList().rightPush(key, value as Any)
            redisTemplate.expire(key, ttl.toMillis(), TimeUnit.MILLISECONDS)
            result ?: 0L
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "listPush", key)
                Mono.just(0L)
            }
    }

    fun <T : Any> listPop(key: String, type: Class<T>): Mono<T> {
        return Mono.fromCallable {
            redisTemplate.opsForList().leftPop(key)
        }
            .flatMap { value ->
                handleConnectionSuccess()
                if (value != null) {
                    Mono.just(objectMapper.convertValue(value, type) as T)
                } else {
                    Mono.empty()
                }
            }
            .onErrorResume { error ->
                handleConnectionError(error, "listPop", key)
                Mono.empty()
            }
    }

    fun <T> listRange(key: String, start: Long, end: Long, type: Class<T>): Flux<T> {
        return Mono.fromCallable {
            redisTemplate.opsForList().range(key, start, end)
        }
            .flatMapMany { values ->
                handleConnectionSuccess()
                Flux.fromIterable(values.map { objectMapper.convertValue(it, type) })
            }
            .onErrorResume { error ->
                handleConnectionError(error, "listRange", key)
                Flux.empty()
            }
    }

    fun setAdd(key: String, value: Any, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            val result = redisTemplate.opsForSet().add(key, value)
            redisTemplate.expire(key, ttl.toMillis(), TimeUnit.MILLISECONDS)
            (result ?: 0L) > 0
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "setAdd", key)
                Mono.just(false)
            }
    }

    fun setMembers(key: String, type: Class<*>): Flux<Any> {
        return Mono.fromCallable {
            redisTemplate.opsForSet().members(key)
        }
            .flatMapMany { members ->
                handleConnectionSuccess()
                Flux.fromIterable(members ?: emptySet())
            }
            .onErrorResume { error ->
                handleConnectionError(error, "setMembers", key)
                Flux.empty()
            }
    }

    fun setRemove(key: String, value: Any): Mono<Boolean> {
        return Mono.fromCallable {
            val result = redisTemplate.opsForSet().remove(key, value)
            (result ?: 0L) > 0
        }
            .doOnSuccess { handleConnectionSuccess() }
            .onErrorResume { error ->
                handleConnectionError(error, "setRemove", key)
                Mono.just(false)
            }
    }

    private fun handleConnectionSuccess() {
        if (!isConnected.get()) {
            isConnected.set(true)
            failureCount.set(0)
            logger.info("Redis 연결이 복구되었습니다")
        }
    }

    private fun handleConnectionError(error: Throwable, operation: String, key: String) {
        val isConnectionError = error.message?.contains("Unable to connect") == true ||
                               error.message?.contains("Connection refused") == true ||
                               error.cause?.message?.contains("Unable to connect") == true ||
                               error.cause?.message?.contains("Connection refused") == true

        if (isConnectionError) {
            val currentTime = System.currentTimeMillis()
            val lastFailure = lastFailureTime.get()
            val count = failureCount.incrementAndGet()

            if (isConnected.get()) {
                isConnected.set(false)
                lastFailureTime.set(currentTime)
                logger.warn("Redis 연결 실패: $operation 작업 중 오류 발생 (key=$key). Redis 없이 계속 진행합니다", error)
            } else {
                val timeSinceLastLog = currentTime - lastFailure
                if (timeSinceLastLog >= logInterval) {
                    logger.debug("Redis 연결 실패 지속 중: $operation 작업 실패 (key=$key, 실패 횟수: $count). Redis 없이 계속 진행합니다")
                    lastFailureTime.set(currentTime)
                }
            }
        } else {
            val isMovedError = error.message?.contains("MOVED") == true ||
                             error.cause?.message?.contains("MOVED") == true
            if (!isMovedError) {
                logger.debug("Redis 작업 실패: $operation (key=$key)", error)
            }
        }
    }

    fun isRedisConnected(): Boolean {
        return isConnected.get()
    }
}