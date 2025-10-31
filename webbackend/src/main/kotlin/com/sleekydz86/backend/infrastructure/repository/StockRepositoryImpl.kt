package com.sleekydz86.backend.infrastructure.repository

import com.sleekydz86.backend.domain.model.HistoricalData
import com.sleekydz86.backend.domain.model.StockData
import com.sleekydz86.backend.domain.model.TechnicalAnalysis
import com.sleekydz86.backend.domain.repository.StockRepository
import com.sleekydz86.backend.infrastructure.client.PythonApiClient
import org.springframework.stereotype.Repository
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

@Repository
class StockRepositoryImpl(
    private val pythonApiClient: PythonApiClient
) : StockRepository {

    private val analysisToStockData: (TechnicalAnalysis) -> StockData = { analysis ->
        StockData(
            symbol = analysis.symbol,
            currentPrice = analysis.currentPrice,
            volume = analysis.volume,
            changePercent = analysis.changePercent,
            timestamp = analysis.timestamp
        )
    }

    override val getRealtimeData: (String) -> Mono<StockData> =
        pythonApiClient::getRealtimeData

    override val getAllRealtimeData: () -> Flux<StockData> = {
        pythonApiClient.getAllAnalysis()
            .map(analysisToStockData)
    }

    override val getAnalysis: (String) -> Mono<TechnicalAnalysis> =
        pythonApiClient::getAnalysis

    override val getAllAnalysis: () -> Flux<TechnicalAnalysis> =
        pythonApiClient::getAllAnalysis

    override val getHistoricalData: (String, Int) -> Mono<HistoricalData> =
        pythonApiClient::getHistoricalData

    override val getAvailableSymbols: () -> Mono<List<String>> =
        pythonApiClient::getSymbols
}
