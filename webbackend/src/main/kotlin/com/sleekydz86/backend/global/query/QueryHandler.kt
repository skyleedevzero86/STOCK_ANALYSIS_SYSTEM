package com.sleekydz86.backend.global.query

import com.sleekydz86.backend.domain.cqrs.query.QueryResult
import com.sleekydz86.backend.domain.cqrs.query.StockQuery
import reactor.core.publisher.Mono

interface QueryHandler<T : StockQuery, R> {
    fun handle(query: T): Mono<QueryResult<R>>
    fun canHandle(query: StockQuery): Boolean
}

interface QueryBus {
    fun <T : StockQuery, R> send(query: T): Mono<QueryResult<R>>
    fun register(handler: QueryHandler<*, *>)
}
