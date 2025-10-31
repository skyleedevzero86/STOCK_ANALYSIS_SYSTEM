package com.sleekydz86.backend.infrastructure.cache

import com.fasterxml.jackson.databind.ObjectMapper
import org.springframework.data.redis.core.RedisTemplate
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration
import java.util.concurrent.TimeUnit

@Service
class DistributedCacheService(
    private val redisTemplate: RedisTemplate<String, Any>,
    private val objectMapper: ObjectMapper
) {

    fun <T> get(key: String, type: Class<T>): Mono<T> {
        return Mono.fromCallable {
            val value = redisTemplate.opsForValue().get(key)
            if (value != null) {
                objectMapper.convertValue(value, type)
            } else {
                null
            }
        }
    }

    fun <T> set(key: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().set(key, value, ttl.toMillis(), TimeUnit.MILLISECONDS)
        }
    }

    fun <T> setIfAbsent(key: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().setIfAbsent(key, value, ttl.toMillis(), TimeUnit.MILLISECONDS)
        }
    }

    fun delete(key: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.delete(key)
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
    }

    fun exists(key: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.hasKey(key)
        }
    }

    fun expire(key: String, ttl: Duration): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.expire(key, ttl.toMillis(), TimeUnit.MILLISECONDS)
        }
    }

    fun <T> getOrSet(key: String, type: Class<T>, supplier: () -> Mono<T>, ttl: Duration = Duration.ofMinutes(30)): Mono<T> {
        return get(key, type)
            .switchIfEmpty(
                supplier()
                    .flatMap { value ->
                        set(key, value, ttl)
                            .then(Mono.just(value))
                    }
            )
    }

    fun <T> getOrSetFlux(key: String, type: Class<T>, supplier: () -> Flux<T>, ttl: Duration = Duration.ofMinutes(30)): Flux<T> {
        return get(key, type)
            .switchIfEmpty(
                supplier()
                    .collectList()
                    .flatMap { values ->
                        set(key, values, ttl)
                            .then(Mono.just(values))
                    }
            )
            .flatMapMany { Flux.fromIterable(it as List<T>) }
    }

    fun increment(key: String, delta: Long = 1L): Mono<Long> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().increment(key, delta)
        }
    }

    fun decrement(key: String, delta: Long = 1L): Mono<Long> {
        return Mono.fromCallable {
            redisTemplate.opsForValue().increment(key, -delta)
        }
    }

    fun <T> hashGet(hashKey: String, field: String, type: Class<T>): Mono<T> {
        return Mono.fromCallable {
            val value = redisTemplate.opsForHash().get(hashKey, field)
            if (value != null) {
                objectMapper.convertValue(value, type)
            } else {
                null
            }
        }
    }

    fun <T> hashSet(hashKey: String, field: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForHash().put(hashKey, field, value)
            redisTemplate.expire(hashKey, ttl.toMillis(), TimeUnit.MILLISECONDS)
            true
        }
    }

    fun hashDelete(hashKey: String, field: String): Mono<Boolean> {
        return Mono.fromCallable {
            redisTemplate.opsForHash().delete(hashKey, field)
            true
        }
    }

    fun <T> listPush(key: String, value: T, ttl: Duration = Duration.ofMinutes(30)): Mono<Long> {
        return Mono.fromCallable {
            val result = redisTemplate.opsForList().rightPush(key, value)
            redisTemplate.expire(key, ttl.toMillis(), TimeUnit.MILLISECONDS)
            result
        }
    }

    fun <T> listPop(key: String, type: Class<T>): Mono<T> {
        return Mono.fromCallable {
            val value = redisTemplate.opsForList().leftPop(key)
            if (value != null) {
                objectMapper.convertValue(value, type)
            } else {
                null
            }
        }
    }

    fun <T> listRange(key: String, start: Long, end: Long, type: Class<T>): Flux<T> {
        return Mono.fromCallable {
            redisTemplate.opsForList().range(key, start, end)
        }
            .flatMapMany { values ->
                Flux.fromIterable(values.map { objectMapper.convertValue(it, type) })
            }
    }

    fun setAdd(key: String, value: Any, ttl: Duration = Duration.ofMinutes(30)): Mono<Boolean> {
        return Mono.fromCallable {
            val result = redisTemplate.opsForSet().add(key, value)
            redisTemplate.expire(key, ttl.toMillis(), TimeUnit.MILLISECONDS)
            result > 0
        }
    }

    fun setMembers(key: String, type: Class<*>): Flux<Any> {
        return Mono.fromCallable {
            redisTemplate.opsForSet().members(key)
        }
            .flatMapMany { members ->
                Flux.fromIterable(members ?: emptySet())
            }
    }

    fun setRemove(key: String, value: Any): Mono<Boolean> {
        return Mono.fromCallable {
            val result = redisTemplate.opsForSet().remove(key, value)
            result > 0
        }
    }
}