package com.sleekydz86.backend.domain.repository

import com.sleekydz86.backend.domain.model.HistoricalData
import com.sleekydz86.backend.domain.model.StockData
import com.sleekydz86.backend.domain.model.TechnicalAnalysis
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

interface StockRepository {
    val getRealtimeData: (String) -> Mono<StockData>
    val getAllRealtimeData: () -> Flux<StockData>
    val getAnalysis: (String) -> Mono<TechnicalAnalysis>
    val getAllAnalysis: () -> Flux<TechnicalAnalysis>
    val getHistoricalData: (String, Int) -> Mono<HistoricalData>
    val getAvailableSymbols: () -> Mono<List<String>>
}
