package com.sleekydz86.backend.application.command

import com.sleekydz86.backend.domain.cqrs.command.CommandResult
import com.sleekydz86.backend.domain.cqrs.command.StockCommand
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import java.lang.reflect.ParameterizedType
import java.util.concurrent.ConcurrentHashMap

@Component
class CommandBusImpl : CommandBus {

    private val handlers = ConcurrentHashMap<Class<*>, CommandHandler<*>>()

    override fun <T : StockCommand> send(command: T): Mono<CommandResult> {
        val handler = handlers[command::class.java] as? CommandHandler<T>
            ?: return Mono.just(CommandResult(
                success = false,
                message = "No handler found for command: ${command::class.java.simpleName}"
            ))

        return handler.handle(command)
    }

    override fun register(handler: CommandHandler<*>) {
        val commandType = handler::class.java
            .genericInterfaces
            .firstOrNull { it is ParameterizedType && it.rawType.typeName.contains("CommandHandler") }
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

        commandType?.let { handlers[it] = handler }
    }
}


