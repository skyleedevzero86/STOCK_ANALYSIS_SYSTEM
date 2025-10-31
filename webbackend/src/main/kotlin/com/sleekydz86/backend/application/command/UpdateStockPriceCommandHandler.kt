package com.sleekydz86.backend.application.command

import com.sleekydz86.backend.domain.cqrs.command.CommandResult
import com.sleekydz86.backend.domain.cqrs.command.StockCommand
import com.sleekydz86.backend.domain.cqrs.event.EventPublisher
import com.sleekydz86.backend.domain.cqrs.event.EventStore
import com.sleekydz86.backend.domain.cqrs.event.StockEvent
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono

@Component
class UpdateStockPriceCommandHandler(
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

