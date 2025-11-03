package com.sleekydz86.backend.domain.cqrs.event

import reactor.core.publisher.Mono

interface EventHandler<T : StockEvent> {
    fun handle(event: T): Mono<Unit>
    fun canHandle(event: StockEvent): Boolean
}

