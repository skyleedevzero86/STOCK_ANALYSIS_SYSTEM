package com.sleekydz86.backend.global.router

import com.sleekydz86.backend.global.handler.StockHandler
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.reactive.function.server.RouterFunction
import org.springframework.web.reactive.function.server.ServerResponse
import org.springframework.web.reactive.function.server.router

@Configuration
class StockRouter(
    private val stockHandler: StockHandler
) {

    @Bean
    fun stockRoutes(): RouterFunction<ServerResponse> = router {
        "/api/stocks".nest {
            GET("/symbols", stockHandler::getAvailableSymbols)
            GET("/realtime", stockHandler::getAllRealtimeData)
            GET("/realtime/{symbol}", stockHandler::getRealtimeData)
            GET("/analysis", stockHandler::getAllAnalysis)
            GET("/analysis/{symbol}", stockHandler::getAnalysis)
            GET("/historical/{symbol}", stockHandler::getHistoricalData)
            GET("/stream", stockHandler::getRealtimeStream)
        }
    }
}
