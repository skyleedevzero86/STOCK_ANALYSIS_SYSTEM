package com.sleekydz86.backend.global.query

import com.sleekydz86.backend.domain.cqrs.query.QueryResult
import com.sleekydz86.backend.domain.cqrs.query.StockQuery
import com.sleekydz86.backend.domain.model.TechnicalAnalysis
import com.sleekydz86.backend.domain.model.TradingSignals
import com.sleekydz86.backend.domain.service.StockAnalysisService
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import java.time.LocalDateTime

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
                        currentPrice = 0.0,
                        volume = 0L,
                        changePercent = 0.0,
                        trend = "unknown",
                        trendStrength = 0.0,
                        signals = TradingSignals("hold", 0.0, null, null, null),
                        anomalies = emptyList(),
                        timestamp = LocalDateTime.now()
                    ),
                    success = false
                ))
            }
    }

    override fun canHandle(query: StockQuery): Boolean {
        return query is StockQuery.GetStockAnalysis
    }
}

