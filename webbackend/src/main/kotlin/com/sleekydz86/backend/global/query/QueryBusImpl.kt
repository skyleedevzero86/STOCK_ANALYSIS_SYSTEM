package com.sleekydz86.backend.global.query

import com.sleekydz86.backend.domain.cqrs.query.QueryResult
import com.sleekydz86.backend.domain.cqrs.query.StockQuery
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import java.lang.reflect.ParameterizedType
import java.util.concurrent.ConcurrentHashMap

@Component
class QueryBusImpl : QueryBus {

    private val handlers = ConcurrentHashMap<Class<*>, QueryHandler<*, *>>()

    override fun <T : StockQuery, R> send(query: T): Mono<QueryResult<R>> {
        val handler = handlers[query::class.java] as? QueryHandler<T, R>
            ?: return Mono.just(QueryResult(
                data = null as R,
                success = false
            ))

        return handler.handle(query)
    }

    override fun register(handler: QueryHandler<*, *>) {
        val queryType = handler::class.java
            .genericInterfaces
            .firstOrNull { it is ParameterizedType && it.rawType.typeName.contains("QueryHandler") }
            ?.let { it as ParameterizedType }
            ?.actualTypeArguments
            ?.firstOrNull()
            ?.let { typeArg ->
                try {
                    Class.forName(typeArg.typeName)
                } catch (e: Exception) {
                    null
                }
            }

        queryType?.let { handlers[it] = handler }
    }
}



