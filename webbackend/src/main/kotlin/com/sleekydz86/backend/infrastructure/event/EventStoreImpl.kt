package com.sleekydz86.backend.infrastructure.event

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.util.concurrent.ConcurrentHashMap

@Component
class EventStoreImpl : EventStore {

    private val events = ConcurrentHashMap<String, MutableList<StockEvent>>()
    private val eventVersions = ConcurrentHashMap<String, Long>()

    override fun saveEvent(aggregateId: String, event: StockEvent, version: Long): Mono<Unit> {
        return Mono.fromCallable {
            events.computeIfAbsent(aggregateId) { mutableListOf() }.add(event)
            eventVersions[aggregateId] = version
        }.then()
    }

    override fun getEvents(aggregateId: String): Flux<StockEvent> {
        return Flux.fromIterable(events[aggregateId] ?: emptyList())
    }

    override fun getEvents(aggregateId: String, fromVersion: Long): Flux<StockEvent> {
        return Flux.fromIterable(events[aggregateId] ?: emptyList())
            .skip(fromVersion)
    }

    override fun getAllEvents(): Flux<StockEvent> {
        return Flux.fromIterable(events.values.flatten())
    }

    override fun getEventsByType(eventType: String): Flux<StockEvent> {
        return Flux.fromIterable(events.values.flatten())
            .filter { event ->
                when (event) {
                    is StockEvent.StockAnalyzed -> eventType == "StockAnalyzed"
                    is StockEvent.PriceUpdated -> eventType == "PriceUpdated"
                    is StockEvent.TradingSignalGenerated -> eventType == "TradingSignalGenerated"
                    is StockEvent.AnomalyDetected -> eventType == "AnomalyDetected"
                    is StockEvent.NotificationSent -> eventType == "NotificationSent"
                    is StockEvent.MarketTrendChanged -> eventType == "MarketTrendChanged"
                }
            }
    }

    override fun getEventsBySymbol(symbol: String): Flux<StockEvent> {
        return Flux.fromIterable(events[symbol] ?: emptyList())
    }
}




