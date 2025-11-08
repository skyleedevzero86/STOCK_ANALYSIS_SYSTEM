package com.sleekydz86.backend.global.config

import com.sleekydz86.backend.application.command.AnalyzeStockCommandHandler
import com.sleekydz86.backend.application.command.CommandBus
import com.sleekydz86.backend.application.command.CommandBusImpl
import com.sleekydz86.backend.application.command.GenerateTradingSignalCommandHandler
import com.sleekydz86.backend.application.command.UpdateStockPriceCommandHandler
import com.sleekydz86.backend.global.query.QueryBus
import com.sleekydz86.backend.global.query.QueryBusImpl
import com.sleekydz86.backend.global.query.StockAnalysisQueryHandler
import com.sleekydz86.backend.global.query.StockHistoricalQueryHandler
import com.sleekydz86.backend.global.query.StockRealtimeQueryHandler
import com.sleekydz86.backend.global.query.StockSymbolsQueryHandler
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class CQRSConfig {

    @Bean
    fun commandBus(
        analyzeStockCommandHandler: AnalyzeStockCommandHandler,
        updateStockPriceCommandHandler: UpdateStockPriceCommandHandler,
        generateTradingSignalCommandHandler: GenerateTradingSignalCommandHandler
    ): CommandBus {
        val commandBus = CommandBusImpl()
        commandBus.register(analyzeStockCommandHandler, com.sleekydz86.backend.domain.cqrs.command.StockCommand.AnalyzeStock::class.java)
        commandBus.register(updateStockPriceCommandHandler, com.sleekydz86.backend.domain.cqrs.command.StockCommand.UpdateStockPrice::class.java)
        commandBus.register(generateTradingSignalCommandHandler, com.sleekydz86.backend.domain.cqrs.command.StockCommand.GenerateTradingSignal::class.java)
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


