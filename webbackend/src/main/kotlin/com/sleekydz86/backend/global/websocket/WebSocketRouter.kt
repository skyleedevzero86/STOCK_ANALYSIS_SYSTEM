package com.sleekydz86.backend.global.websocket

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.reactive.function.server.RouterFunction
import org.springframework.web.reactive.function.server.ServerResponse
import org.springframework.web.reactive.function.server.router

@Configuration
class WebSocketRouter(
    private val stockWebSocketHandler: StockWebSocketHandler
) {

    @Bean
    fun webSocketRoutes(): RouterFunction<ServerResponse> = router {
        GET("/ws/stocks") { request ->
            ServerResponse.ok()
                .body(stockWebSocketHandler.handle(request.exchange().request))
        }
    }
}