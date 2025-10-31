package com.sleekydz86.backend.infrastructure.cache

@Target(AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
annotation class Cacheable(
    val type: CacheType,
    val ttl: Int = 30
)

enum class CacheType {
    STOCK_DATA,
    STOCK_ANALYSIS,
    HISTORICAL_DATA,
    SYMBOLS,
    ALL_STOCK_DATA,
    ALL_STOCK_ANALYSIS
}

