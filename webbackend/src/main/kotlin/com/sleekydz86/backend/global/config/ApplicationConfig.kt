package com.sleekydz86.backend.global.config

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.reactive.function.server.RouterFunction
import org.springframework.web.reactive.function.server.ServerResponse
import org.springframework.web.reactive.socket.server.support.WebSocketHandlerAdapter

@Configuration
class ApplicationConfig(
    private val stockRoutes: RouterFunction<ServerResponse>,
    private val webSocketRoutes: RouterFunction<ServerResponse>
) {

    @Bean
    fun webSocketHandlerAdapter(): WebSocketHandlerAdapter =
        WebSocketHandlerAdapter()

    @Bean
    fun allRoutes(): RouterFunction<ServerResponse> =
        stockRoutes.and(webSocketRoutes)
}
