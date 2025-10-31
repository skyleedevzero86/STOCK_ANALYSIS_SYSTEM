package com.sleekydz86.backend.global.query

import com.sleekydz86.backend.domain.cqrs.query.QueryResult
import com.sleekydz86.backend.domain.cqrs.query.StockQuery
import com.sleekydz86.backend.domain.model.StockData
import com.sleekydz86.backend.domain.service.StockAnalysisService
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import java.time.LocalDateTime

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
                        timestamp = LocalDateTime.now()
                    ),
                    success = false
                ))
            }
    }

    override fun canHandle(query: StockQuery): Boolean {
        return query is StockQuery.GetRealtimeData
    }
}

