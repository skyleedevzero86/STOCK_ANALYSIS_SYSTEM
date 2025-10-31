package com.sleekydz86.backend.global.query

import com.sleekydz86.backend.domain.cqrs.query.QueryResult
import com.sleekydz86.backend.domain.cqrs.query.StockQuery
import com.sleekydz86.backend.domain.model.HistoricalData
import com.sleekydz86.backend.domain.service.StockAnalysisService
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono

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

