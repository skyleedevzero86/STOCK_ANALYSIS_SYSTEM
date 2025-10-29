package com.sleekydz86.backend.global.config

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import javax.annotation.PostConstruct

@Configuration
class CQRSConfig {

    @Bean
    fun commandBus(
        stockCommandHandler: StockCommandHandler,
        stockPriceCommandHandler: StockPriceCommandHandler,
        tradingSignalCommandHandler: TradingSignalCommandHandler
    ): CommandBus {
        val commandBus = CommandBusImpl()
        commandBus.register(stockCommandHandler)
        commandBus.register(stockPriceCommandHandler)
        commandBus.register(tradingSignalCommandHandler)
        return commandBus
    }

    @Bean
    fun queryBus(
        stockAnalysisQueryHandler: StockAnalysisQueryHandler,
        stockRealtimeQueryHandler: StockRealtimeQueryHandler,
        stockHistoricalQueryHandler: StockHistoricalQueryHandler,
        stockSymbolsQueryHandler: StockSymbolsQueryHandler
    ): QueryBus {
        val queryBus = QueryBusImpl()
        queryBus.register(stockAnalysisQueryHandler)
        queryBus.register(stockRealtimeQueryHandler)
        queryBus.register(stockHistoricalQueryHandler)
        queryBus.register(stockSymbolsQueryHandler)
        return queryBus
    }
}


