package com.sleekydz86.backend.infrastructure.cache

import com.sleekydz86.backend.domain.model.HistoricalData
import com.sleekydz86.backend.domain.model.StockData
import com.sleekydz86.backend.domain.model.TechnicalAnalysis
import org.aspectj.lang.ProceedingJoinPoint
import org.aspectj.lang.annotation.Around
import org.aspectj.lang.annotation.Aspect
import org.springframework.stereotype.Component
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration

@Aspect
@Component
class CacheAspect(
    private val stockCacheService: StockCacheService
) {
    private val logger = org.slf4j.LoggerFactory.getLogger(CacheAspect::class.java)

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
                            .cast(StockData::class.java)
                            .flatMap { stockData ->
                                stockCacheService.setStockData(symbol, stockData, Duration.ofMinutes(cacheable.ttl.toLong()))
                                    .then(Mono.just(stockData))
                            }
                    )
                    .onErrorResume { error ->
                        logger.warn("Cache operation failed for STOCK_DATA (symbol: $symbol), proceeding without cache", error)
                        (joinPoint.proceed() as Mono<*>).cast(StockData::class.java)
                    }
            }
            CacheType.STOCK_ANALYSIS -> {
                val symbol = args[0] as String
                stockCacheService.getStockAnalysis(symbol)
                    .switchIfEmpty(
                        (joinPoint.proceed() as Mono<*>)
                            .cast(TechnicalAnalysis::class.java)
                            .flatMap { analysis ->
                                stockCacheService.setStockAnalysis(symbol, analysis, Duration.ofMinutes(cacheable.ttl.toLong()))
                                    .then(Mono.just(analysis))
                            }
                    )
                    .onErrorResume { error ->
                        logger.warn("Cache operation failed for STOCK_ANALYSIS (symbol: $symbol), proceeding without cache", error)
                        (joinPoint.proceed() as Mono<*>).cast(TechnicalAnalysis::class.java)
                    }
            }
            CacheType.HISTORICAL_DATA -> {
                val symbol = args[0] as String
                val days = if (args.size > 1) args[1] as Int else 30
                stockCacheService.getHistoricalData(symbol, days)
                    .switchIfEmpty(
                        (joinPoint.proceed() as Mono<*>)
                            .cast(HistoricalData::class.java)
                            .flatMap { historicalData ->
                                stockCacheService.setHistoricalData(symbol, days, historicalData, Duration.ofMinutes(cacheable.ttl.toLong()))
                                    .then(Mono.just(historicalData))
                            }
                    )
                    .onErrorResume { error ->
                        logger.warn("Cache operation failed for HISTORICAL_DATA (symbol: $symbol), proceeding without cache", error)
                        (joinPoint.proceed() as Mono<*>).cast(HistoricalData::class.java)
                    }
            }
            CacheType.SYMBOLS -> {
                stockCacheService.getAvailableSymbols()
                    .switchIfEmpty(
                        (joinPoint.proceed() as Mono<*>)
                            .map { it as? List<String> ?: emptyList<String>() }
                            .flatMap { symbols ->
                                stockCacheService.setAvailableSymbols(symbols, Duration.ofMinutes(cacheable.ttl.toLong()))
                                    .then(Mono.just(symbols))
                            }
                    )
                    .onErrorResume { error ->
                        logger.warn("Cache operation failed for SYMBOLS, proceeding without cache", error)
                        (joinPoint.proceed() as Mono<*>)
                            .map { it as? List<String> ?: emptyList<String>() }
                    }
            }
            CacheType.ALL_STOCK_DATA -> {
                stockCacheService.getAllStockData()
                    .switchIfEmpty(
                        (joinPoint.proceed() as Flux<*>)
                            .cast(StockData::class.java)
                            .collectList()
                            .flatMapMany { stockDataList ->
                                stockCacheService.setAllStockData(stockDataList, Duration.ofMinutes(cacheable.ttl.toLong()))
                                    .thenMany(Flux.fromIterable(stockDataList))
                            }
                    )
                    .onErrorResume { error ->
                        logger.warn("Cache operation failed for ALL_STOCK_DATA, proceeding without cache", error)
                        (joinPoint.proceed() as Flux<*>).cast(StockData::class.java)
                    }
            }
            CacheType.ALL_STOCK_ANALYSIS -> {
                stockCacheService.getAllStockAnalysis()
                    .switchIfEmpty(
                        (joinPoint.proceed() as Flux<*>)
                            .cast(TechnicalAnalysis::class.java)
                            .collectList()
                            .flatMapMany { analysisList ->
                                stockCacheService.setAllStockAnalysis(analysisList, Duration.ofMinutes(cacheable.ttl.toLong()))
                                    .thenMany(Flux.fromIterable(analysisList))
                            }
                    )
                    .onErrorResume { error ->
                        logger.warn("Cache operation failed for ALL_STOCK_ANALYSIS, proceeding without cache", error)
                        (joinPoint.proceed() as Flux<*>).cast(TechnicalAnalysis::class.java)
                    }
            }
        }
    }
}