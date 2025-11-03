package com.sleekydz86.backend.infrastructure.event

import com.sleekydz86.backend.domain.cqrs.event.EventHandler
import com.sleekydz86.backend.domain.cqrs.event.EventPublisher
import com.sleekydz86.backend.domain.cqrs.event.StockEvent
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import java.util.concurrent.CopyOnWriteArrayList

@Component
class EventPublisherImpl : EventPublisher {

    private val handlers = CopyOnWriteArrayList<EventHandler<*>>()

    fun register(handler: EventHandler<*>) {
        handlers.add(handler)
    }

    override fun publish(event: StockEvent): Mono<Unit> {
        return Mono.fromCallable {
            handlers.forEach { handler ->
                if (handler.canHandle(event)) {
                    when (event) {
                        is StockEvent.StockAnalyzed -> (handler as? EventHandler<StockEvent.StockAnalyzed>)?.handle(event)
                        is StockEvent.PriceUpdated -> (handler as? EventHandler<StockEvent.PriceUpdated>)?.handle(event)
                        is StockEvent.TradingSignalGenerated -> (handler as? EventHandler<StockEvent.TradingSignalGenerated>)?.handle(event)
                        is StockEvent.AnomalyDetected -> (handler as? EventHandler<StockEvent.AnomalyDetected>)?.handle(event)
                        is StockEvent.NotificationSent -> (handler as? EventHandler<StockEvent.NotificationSent>)?.handle(event)
                        is StockEvent.MarketTrendChanged -> (handler as? EventHandler<StockEvent.MarketTrendChanged>)?.handle(event)
                    }
                }
            }
        }.thenReturn(Unit)
    }

    override fun publish(events: List<StockEvent>): Mono<Unit> {
        return Mono.fromCallable {
            events.forEach { event ->
                handlers.forEach { handler ->
                    if (handler.canHandle(event)) {
                        when (event) {
                            is StockEvent.StockAnalyzed -> (handler as? EventHandler<StockEvent.StockAnalyzed>)?.handle(event)
                            is StockEvent.PriceUpdated -> (handler as? EventHandler<StockEvent.PriceUpdated>)?.handle(event)
                            is StockEvent.TradingSignalGenerated -> (handler as? EventHandler<StockEvent.TradingSignalGenerated>)?.handle(event)
                            is StockEvent.AnomalyDetected -> (handler as? EventHandler<StockEvent.AnomalyDetected>)?.handle(event)
                            is StockEvent.NotificationSent -> (handler as? EventHandler<StockEvent.NotificationSent>)?.handle(event)
                            is StockEvent.MarketTrendChanged -> (handler as? EventHandler<StockEvent.MarketTrendChanged>)?.handle(event)
                        }
                    }
                }
            }
        }.thenReturn(Unit)
    }
}




