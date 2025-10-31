package com.sleekydz86.backend.global.query

import com.sleekydz86.backend.domain.cqrs.query.QueryResult
import com.sleekydz86.backend.domain.cqrs.query.StockQuery
import com.sleekydz86.backend.domain.service.StockAnalysisService
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono

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

