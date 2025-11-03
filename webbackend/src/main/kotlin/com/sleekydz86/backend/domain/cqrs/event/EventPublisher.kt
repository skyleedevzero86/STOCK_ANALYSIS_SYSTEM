package com.sleekydz86.backend.domain.cqrs.event

import reactor.core.publisher.Mono

interface EventPublisher {
    fun publish(event: StockEvent): Mono<Unit>
    fun publish(events: List<StockEvent>): Mono<Unit>
}

