package com.sleekydz86.backend.infrastructure.cache

import org.aspectj.lang.ProceedingJoinPoint
import org.aspectj.lang.annotation.Around
import org.aspectj.lang.annotation.Aspect
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import reactor.core.publisher.Flux
import java.time.Duration

@Aspect
@Component
class CacheAspect(
    private val stockCacheService: StockCacheService
) {

    @Around("@annotation(cacheable)")
    fun cacheAround(joinPoint: ProceedingJoinPoint, cacheable: Cacheable): Any? {
        val args = joinPoint.args
        val methodName = joinPoint.signature.name

        return when (cacheable.type) {
            CacheType.STOCK_DATA -> {
                val symbol = args[0] as String
                stockCacheService.getStockData(symbol)
                    .switchIfEmpty(
                        (joinPoint.proceed() as Mono<*>)
                            .cast(com.stockanalysis.domain.model.StockData::class.java)
                            .flatMap { stockData ->
                                stockCacheService.setStockData(symbol, stockData, Duration.ofMinutes(cacheable.ttl))
                                    .then(Mono.just(stockData))
                            }
                    )
            }
            CacheType.STOCK_ANALYSIS -> {
                val symbol = args[0] as String
                stockCacheService.getStockAnalysis(symbol)
                    .switchIfEmpty(
                        (joinPoint.proceed() as Mono<*>)
                            .cast(com.stockanalysis.domain.model.TechnicalAnalysis::class.java)
                            .flatMap { analysis ->
                                stockCacheService.setStockAnalysis(symbol, analysis, Duration.ofMinutes(cacheable.ttl))
                                    .then(Mono.just(analysis))
                            }
                    )
            }
            CacheType.HISTORICAL_DATA -> {
                val symbol = args[0] as String
                val days = if (args.size > 1) args[1] as Int else 30
                stockCacheService.getHistoricalData(symbol, days)
                    .switchIfEmpty(
                        (joinPoint.proceed() as Mono<*>)
                            .cast(com.stockanalysis.domain.model.HistoricalData::class.java)
                            .flatMap { historicalData ->
                                stockCacheService.setHistoricalData(symbol, days, historicalData, Duration.ofMinutes(cacheable.ttl))
                                    .then(Mono.just(historicalData))
                            }
                    )
            }
            CacheType.SYMBOLS -> {
                stockCacheService.getAvailableSymbols()
                    .switchIfEmpty(
                        (joinPoint.proceed() as Mono<*>)
                            .cast(List::class.java)
                            .flatMap { symbols ->
                                stockCacheService.setAvailableSymbols(symbols as List<String>, Duration.ofMinutes(cacheable.ttl))
                                    .then(Mono.just(symbols))
                            }
                    )
            }
            CacheType.ALL_STOCK_DATA -> {
                stockCacheService.getAllStockData()
                    .switchIfEmpty(
                        (joinPoint.proceed() as Flux<*>)
                            .cast(com.stockanalysis.domain.model.StockData::class.java)
                            .collectList()
                            .flatMap { stockDataList ->
                                stockCacheService.setAllStockData(stockDataList, Duration.ofMinutes(cacheable.ttl))
                                    .then(Flux.fromIterable(stockDataList))
                            }
                    )
            }
            CacheType.ALL_STOCK_ANALYSIS -> {
                stockCacheService.getAllStockAnalysis()
                    .switchIfEmpty(
                        (joinPoint.proceed() as Flux<*>)
                            .cast(com.stockanalysis.domain.model.TechnicalAnalysis::class.java)
                            .collectList()
                            .flatMap { analysisList ->
                                stockCacheService.setAllStockAnalysis(analysisList, Duration.ofMinutes(cacheable.ttl))
                                    .then(Flux.fromIterable(analysisList))
                            }
                    )
            }
        }
    }
}

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