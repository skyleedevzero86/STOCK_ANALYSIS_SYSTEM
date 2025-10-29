package com.sleekydz86.backend.global.query

import org.springframework.stereotype.Component
import reactor.core.publisher.Mono

@Component
class StockAnalysisQueryHandler(
    private val stockAnalysisService: StockAnalysisService
) : QueryHandler<StockQuery.GetStockAnalysis, TechnicalAnalysis> {

    override fun handle(query: StockQuery.GetStockAnalysis): Mono<QueryResult<TechnicalAnalysis>> {
        return stockAnalysisService.getStockAnalysis(query.symbol)
            .map { analysis ->
                QueryResult(
                    data = analysis,
                    success = true
                )
            }
            .onErrorResume { error ->
                Mono.just(QueryResult(
                    data = TechnicalAnalysis(
                        symbol = query.symbol,
                        trend = "unknown",
                        trendStrength = 0.0,
                        signals = TradingSignals("hold", 0.0, null, null, null),
                        anomalies = emptyList(),
                        timestamp = java.time.LocalDateTime.now()
                    ),
                    success = false
                ))
            }
    }

    override fun canHandle(query: StockQuery): Boolean {
        return query is StockQuery.GetStockAnalysis
    }
}

@Component
class StockRealtimeQueryHandler(
    private val stockAnalysisService: StockAnalysisService
) : QueryHandler<StockQuery.GetRealtimeData, StockData> {

    override fun handle(query: StockQuery.GetRealtimeData): Mono<QueryResult<StockData>> {
        return stockAnalysisService.getRealtimeStockData(query.symbol)
            .map { stockData ->
                QueryResult(
                    data = stockData,
                    success = true
                )
            }
            .onErrorResume { error ->
                Mono.just(QueryResult(
                    data = StockData(
                        symbol = query.symbol,
                        currentPrice = 0.0,
                        volume = 0L,
                        changePercent = 0.0,
                        timestamp = java.time.LocalDateTime.now()
                    ),
                    success = false
                ))
            }
    }

    override fun canHandle(query: StockQuery): Boolean {
        return query is StockQuery.GetRealtimeData
    }
}

@Component
class StockHistoricalQueryHandler(
    private val stockAnalysisService: StockAnalysisService
) : QueryHandler<StockQuery.GetHistoricalData, HistoricalData> {

    override fun handle(query: StockQuery.GetHistoricalData): Mono<QueryResult<HistoricalData>> {
        return stockAnalysisService.getStockHistoricalData(query.symbol, query.days)
            .map { historicalData ->
                QueryResult(
                    data = historicalData,
                    success = true
                )
            }
            .onErrorResume { error ->
                Mono.just(QueryResult(
                    data = HistoricalData(
                        symbol = query.symbol,
                        data = emptyList(),
                        period = query.days
                    ),
                    success = false
                ))
            }
    }

    override fun canHandle(query: StockQuery): Boolean {
        return query is StockQuery.GetHistoricalData
    }
}

@Component
class StockSymbolsQueryHandler(
    private val stockAnalysisService: StockAnalysisService
) : QueryHandler<StockQuery.GetAvailableSymbols, List<String>> {

    override fun handle(query: StockQuery.GetAvailableSymbols): Mono<QueryResult<List<String>>> {
        return stockAnalysisService.getAvailableSymbols()
            .map { symbols ->
                QueryResult(
                    data = symbols,
                    success = true
                )
            }
            .onErrorResume { error ->
                Mono.just(QueryResult(
                    data = emptyList<String>(),
                    success = false
                ))
            }
    }

    override fun canHandle(query: StockQuery): Boolean {
        return query is StockQuery.GetAvailableSymbols
    }
}