package com.sleekydz86.backend.global.handler

import com.sleekydz86.backend.application.command.CommandBus
import com.sleekydz86.backend.domain.cqrs.command.StockCommand
import com.sleekydz86.backend.domain.cqrs.query.StockQuery
import com.sleekydz86.backend.global.query.QueryBus
import org.springframework.core.ParameterizedTypeReference
import org.springframework.stereotype.Component
import org.springframework.web.reactive.function.server.ServerRequest
import org.springframework.web.reactive.function.server.ServerResponse
import reactor.core.publisher.Mono

@Component
class CQRSStockHandler(
    private val commandBus: CommandBus,
    private val queryBus: QueryBus
) {

    fun getAnalysis(request: ServerRequest): Mono<ServerResponse> {
        val symbol = request.pathVariable("symbol")
        val query = StockQuery.GetStockAnalysis(symbol)

        return queryBus.send<StockQuery.GetStockAnalysis, Any>(query)
            .flatMap { result ->
                if (result.success) {
                    ServerResponse.ok().bodyValue(result.data)
                } else {
                    ServerResponse.badRequest().bodyValue(mapOf("error" to "Analysis failed"))
                }
            }
            .onErrorResume { error ->
                ServerResponse.badRequest().bodyValue(mapOf("error" to (error.message ?: "Unknown error")))
            }
    }

    fun getRealtimeData(request: ServerRequest): Mono<ServerResponse> {
        val symbol = request.pathVariable("symbol")
        val query = StockQuery.GetRealtimeData(symbol)

        return queryBus.send<StockQuery.GetRealtimeData, Any>(query)
            .flatMap { result ->
                if (result.success) {
                    ServerResponse.ok().bodyValue(result.data)
                } else {
                    ServerResponse.badRequest().bodyValue(mapOf("error" to "Data retrieval failed"))
                }
            }
            .onErrorResume { error ->
                ServerResponse.badRequest().bodyValue(mapOf("error" to (error.message ?: "Unknown error")))
            }
    }

    fun getHistoricalData(request: ServerRequest): Mono<ServerResponse> {
        val symbol = request.pathVariable("symbol")
        val days = request.queryParam("days").map { it.toInt() }.orElse(30)
        val query = StockQuery.GetHistoricalData(symbol, days)

        return queryBus.send<StockQuery.GetHistoricalData, Any>(query)
            .flatMap { result ->
                if (result.success) {
                    ServerResponse.ok().bodyValue(result.data)
                } else {
                    ServerResponse.badRequest().bodyValue(mapOf("error" to "Historical data retrieval failed"))
                }
            }
            .onErrorResume { error ->
                ServerResponse.badRequest().bodyValue(mapOf("error" to (error.message ?: "Unknown error")))
            }
    }

    fun getAllAnalysis(request: ServerRequest): Mono<ServerResponse> {
        val query = StockQuery.GetAllAnalysis()

        return queryBus.send<StockQuery.GetAllAnalysis, Any>(query)
            .flatMap { result ->
                if (result.success) {
                    ServerResponse.ok().bodyValue(result.data)
                } else {
                    ServerResponse.badRequest().bodyValue(mapOf("error" to "Analysis retrieval failed"))
                }
            }
            .onErrorResume { error ->
                ServerResponse.badRequest().bodyValue(mapOf("error" to (error.message ?: "Unknown error")))
            }
    }

    fun getSymbols(request: ServerRequest): Mono<ServerResponse> {
        val query = StockQuery.GetAvailableSymbols

        return queryBus.send<StockQuery.GetAvailableSymbols, Any>(query)
            .flatMap { result ->
                if (result.success) {
                    ServerResponse.ok().bodyValue(result.data)
                } else {
                    ServerResponse.badRequest().bodyValue(mapOf("error" to "Symbols retrieval failed"))
                }
            }
            .onErrorResume { error ->
                ServerResponse.badRequest().bodyValue(mapOf("error" to (error.message ?: "Unknown error")))
            }
    }

    fun analyzeStock(request: ServerRequest): Mono<ServerResponse> {
        val symbol = request.pathVariable("symbol")
        val analysisType = request.queryParam("type").orElse("comprehensive")
        val command = StockCommand.AnalyzeStock(symbol, analysisType)

        return commandBus.send(command)
            .flatMap { result ->
                if (result.success) {
                    ServerResponse.ok().bodyValue(result.data ?: emptyMap<Any, Any>())
                } else {
                    ServerResponse.badRequest().bodyValue(mapOf("error" to result.message))
                }
            }
            .onErrorResume { error ->
                ServerResponse.badRequest().bodyValue(mapOf("error" to (error.message ?: "Unknown error")))
            }
    }

    fun updateStockPrice(request: ServerRequest): Mono<ServerResponse> {
        val typeRef = object : ParameterizedTypeReference<Map<String, Any>>() {}
        return request.bodyToMono(typeRef)
            .flatMap { body ->
                val symbol = body["symbol"] as String
                val price = (body["price"] as Number).toDouble()
                val volume = (body["volume"] as Number).toLong()
                val command = StockCommand.UpdateStockPrice(symbol, price, volume, java.time.LocalDateTime.now())

                commandBus.send(command)
                    .flatMap { result ->
                        if (result.success) {
                            ServerResponse.ok().bodyValue(result.data ?: emptyMap<Any, Any>())
                        } else {
                            ServerResponse.badRequest().bodyValue(mapOf("error" to result.message))
                        }
                    }
            }
            .onErrorResume { error ->
                ServerResponse.badRequest().bodyValue(mapOf("error" to (error.message ?: "Unknown error")))
            }
    }

    fun generateTradingSignal(request: ServerRequest): Mono<ServerResponse> {
        val symbol = request.pathVariable("symbol")
        val signalType = request.queryParam("type").orElse("technical")
        val command = StockCommand.GenerateTradingSignal(symbol, signalType)

        return commandBus.send(command)
            .flatMap { result ->
                if (result.success) {
                    ServerResponse.ok().bodyValue(result.data ?: emptyMap<Any, Any>())
                } else {
                    ServerResponse.badRequest().bodyValue(mapOf("error" to result.message))
                }
            }
            .onErrorResume { error ->
                ServerResponse.badRequest().bodyValue(mapOf("error" to (error.message ?: "Unknown error")))
            }
    }
}



