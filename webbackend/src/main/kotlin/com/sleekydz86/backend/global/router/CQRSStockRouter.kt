package com.sleekydz86.backend.global.router

import com.sleekydz86.backend.global.handler.CQRSStockHandler
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.reactive.function.server.RouterFunction
import org.springframework.web.reactive.function.server.ServerResponse
import org.springframework.web.reactive.function.server.router

@Configuration
class CQRSStockRouter {

    @Bean
    fun cqrsStockRoutes(stockHandler: CQRSStockHandler): RouterFunction<ServerResponse> = router {
        "/api/cqrs/stocks".nest {
            GET("/analysis/{symbol}", stockHandler::getAnalysis)
            GET("/realtime/{symbol}", stockHandler::getRealtimeData)
            GET("/historical/{symbol}", stockHandler::getHistoricalData)
            GET("/analysis", stockHandler::getAllAnalysis)
            GET("/symbols", stockHandler::getSymbols)
            POST("/analyze/{symbol}", stockHandler::analyzeStock)
            POST("/price/update", stockHandler::updateStockPrice)
            POST("/signal/{symbol}", stockHandler::generateTradingSignal)
        }
    }
}