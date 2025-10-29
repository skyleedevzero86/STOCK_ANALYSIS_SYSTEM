package com.sleekydz86.backend.application.command

import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import java.time.LocalDateTime

@Component
class StockCommandHandler(
    private val eventStore: EventStore,
    private val eventPublisher: EventPublisher,
    private val stockAnalysisService: StockAnalysisService
) : CommandHandler<StockCommand.AnalyzeStock> {

    override fun handle(command: StockCommand.AnalyzeStock): Mono<CommandResult> {
        return stockAnalysisService.getStockAnalysis(command.symbol)
            .map { analysis ->
                val event = StockEvent.StockAnalyzed(
                    symbol = command.symbol,
                    analysisResult = mapOf(
                        "trend" to analysis.trend,
                        "trendStrength" to analysis.trendStrength,
                        "signals" to analysis.signals
                    ),
                    confidence = analysis.signals.confidence
                )
                eventStore.saveEvent(command.symbol, event, 1)
                    .then(eventPublisher.publish(event))
                    .then(Mono.just(CommandResult(
                        success = true,
                        message = "Stock analysis completed",
                        data = analysis
                    )))
            }
            .flatMap { it }
            .onErrorResume { error ->
                Mono.just(CommandResult(
                    success = false,
                    message = "Analysis failed: ${error.message}"
                ))
            }
    }

    override fun canHandle(command: StockCommand): Boolean {
        return command is StockCommand.AnalyzeStock
    }
}

@Component
class StockPriceCommandHandler(
    private val eventStore: EventStore,
    private val eventPublisher: EventPublisher
) : CommandHandler<StockCommand.UpdateStockPrice> {

    override fun handle(command: StockCommand.UpdateStockPrice): Mono<CommandResult> {
        val event = StockEvent.PriceUpdated(
            symbol = command.symbol,
            price = command.price,
            volume = command.volume,
            changePercent = 0.0
        )

        return eventStore.saveEvent(command.symbol, event, 1)
            .then(eventPublisher.publish(event))
            .then(Mono.just(CommandResult(
                success = true,
                message = "Stock price updated",
                data = mapOf(
                    "symbol" to command.symbol,
                    "price" to command.price,
                    "volume" to command.volume
                )
            )))
            .onErrorResume { error ->
                Mono.just(CommandResult(
                    success = false,
                    message = "Price update failed: ${error.message}"
                ))
            }
    }

    override fun canHandle(command: StockCommand): Boolean {
        return command is StockCommand.UpdateStockPrice
    }
}

@Component
class TradingSignalCommandHandler(
    private val eventStore: EventStore,
    private val eventPublisher: EventPublisher
) : CommandHandler<StockCommand.GenerateTradingSignal> {

    override fun handle(command: StockCommand.GenerateTradingSignal): Mono<CommandResult> {
        val event = StockEvent.TradingSignalGenerated(
            symbol = command.symbol,
            signal = "buy",
            confidence = 0.75,
            signalType = command.signalType
        )

        return eventStore.saveEvent(command.symbol, event, 1)
            .then(eventPublisher.publish(event))
            .then(Mono.just(CommandResult(
                success = true,
                message = "Trading signal generated",
                data = mapOf(
                    "symbol" to command.symbol,
                    "signal" to event.signal,
                    "confidence" to event.confidence
                )
            )))
            .onErrorResume { error ->
                Mono.just(CommandResult(
                    success = false,
                    message = "Signal generation failed: ${error.message}"
                ))
            }
    }

    override fun canHandle(command: StockCommand): Boolean {
        return command is StockCommand.GenerateTradingSignal
    }
}


