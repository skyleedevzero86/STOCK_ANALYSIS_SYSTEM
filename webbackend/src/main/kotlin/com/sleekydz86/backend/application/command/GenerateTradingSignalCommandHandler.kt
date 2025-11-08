package com.sleekydz86.backend.application.command

import com.sleekydz86.backend.domain.cqrs.command.CommandResult
import com.sleekydz86.backend.domain.cqrs.command.StockCommand
import com.sleekydz86.backend.domain.cqrs.event.EventPublisher
import com.sleekydz86.backend.domain.cqrs.event.EventStore
import com.sleekydz86.backend.domain.cqrs.event.StockEvent
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono

@Component
class GenerateTradingSignalCommandHandler(
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
                message = "거래 신호가 생성되었습니다",
                data = mapOf(
                    "symbol" to command.symbol,
                    "signal" to event.signal,
                    "confidence" to event.confidence
                )
            )))
            .onErrorResume { error ->
                Mono.just(CommandResult(
                    success = false,
                    message = "신호 생성 실패: ${error.message}"
                ))
            }
    }

    override fun canHandle(command: StockCommand): Boolean {
        return command is StockCommand.GenerateTradingSignal
    }
}

