package com.sleekydz86.backend.application.command

import com.sleekydz86.backend.domain.cqrs.command.CommandResult
import com.sleekydz86.backend.domain.cqrs.command.StockCommand
import com.sleekydz86.backend.domain.cqrs.event.EventPublisher
import com.sleekydz86.backend.domain.cqrs.event.EventStore
import com.sleekydz86.backend.domain.cqrs.event.StockEvent
import com.sleekydz86.backend.domain.service.StockAnalysisService
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono

@Component
class AnalyzeStockCommandHandler(
    private val eventStore: EventStore,
    private val eventPublisher: EventPublisher,
    private val stockAnalysisService: StockAnalysisService
) : CommandHandler<StockCommand.AnalyzeStock> {

    override fun handle(command: StockCommand.AnalyzeStock): Mono<CommandResult> {
        return stockAnalysisService.getStockAnalysis(command.symbol)
            .flatMap { analysis ->
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
                        message = "주식 분석이 완료되었습니다",
                        data = analysis
                    )))
            }
            .onErrorResume { error ->
                Mono.just(CommandResult(
                    success = false,
                    message = "분석 실패: ${error.message}"
                ))
            }
    }

    override fun canHandle(command: StockCommand): Boolean {
        return command is StockCommand.AnalyzeStock
    }
}

