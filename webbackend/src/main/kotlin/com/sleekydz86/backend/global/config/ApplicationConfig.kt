package com.sleekydz86.backend.global.config

import com.sleekydz86.backend.global.handler.StockHandler
import com.sleekydz86.backend.global.router.StockRouter
import com.sleekydz86.backend.global.websocket.StockWebSocketHandler
import com.sleekydz86.backend.global.websocket.WebSocketRouter
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.reactive.function.server.RouterFunction
import org.springframework.web.reactive.function.server.ServerResponse
import org.springframework.web.reactive.socket.server.support.WebSocketHandlerAdapter

@Configuration
class ApplicationConfig(
    private val stockHandler: StockHandler,
    private val stockWebSocketHandler: StockWebSocketHandler
) {

    @Bean
    fun webSocketHandlerAdapter(): WebSocketHandlerAdapter =
        WebSocketHandlerAdapter()

    @Bean
    fun stockRoutes(): RouterFunction<ServerResponse> =
        StockRouter(stockHandler).stockRoutes()

    @Bean
    fun webSocketRoutes(): RouterFunction<ServerResponse> =
        WebSocketRouter(stockWebSocketHandler).webSocketRoutes()

    @Bean
    fun allRoutes(): RouterFunction<ServerResponse> =
        stockRoutes().and(webSocketRoutes())
}
