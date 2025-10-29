package com.sleekydz86.backend.domain.cqrs.event

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

interface EventStore {
    fun saveEvent(aggregateId: String, event: StockEvent, version: Long): Mono<Unit>
    fun getEvents(aggregateId: String): Flux<StockEvent>
    fun getEvents(aggregateId: String, fromVersion: Long): Flux<StockEvent>
    fun getAllEvents(): Flux<StockEvent>
    fun getEventsByType(eventType: String): Flux<StockEvent>
    fun getEventsBySymbol(symbol: String): Flux<StockEvent>
}

interface EventPublisher {
    fun publish(event: StockEvent): Mono<Unit>
    fun publish(events: List<StockEvent>): Mono<Unit>
}

interface EventHandler<T : StockEvent> {
    fun handle(event: T): Mono<Unit>
    fun canHandle(event: StockEvent): Boolean
}