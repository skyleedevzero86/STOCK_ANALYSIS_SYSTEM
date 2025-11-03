package com.sleekydz86.backend.global.config

import com.sleekydz86.backend.global.websocket.StockWebSocketHandler
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.reactive.function.server.RouterFunction
import org.springframework.web.reactive.function.server.ServerResponse
import org.springframework.web.reactive.handler.SimpleUrlHandlerMapping
import org.springframework.web.reactive.socket.server.support.WebSocketHandlerAdapter
import java.util.HashMap

@Configuration
class ApplicationConfig(
    private val stockRoutes: RouterFunction<ServerResponse>,
    private val webSocketRoutes: RouterFunction<ServerResponse>,
    private val stockWebSocketHandler: StockWebSocketHandler
) {

    @Bean
    fun webSocketHandlerAdapter(): WebSocketHandlerAdapter =
        WebSocketHandlerAdapter()

    @Bean
    fun webSocketHandlerMapping(): SimpleUrlHandlerMapping {
        val urlMap = HashMap<String, Any>()
        urlMap["/ws/stocks"] = stockWebSocketHandler
        val handlerMapping = SimpleUrlHandlerMapping()
        handlerMapping.urlMap = urlMap
        handlerMapping.order = 1
        return handlerMapping
    }

    @Bean
    fun allRoutes(): RouterFunction<ServerResponse> =
        stockRoutes.and(webSocketRoutes)
}
