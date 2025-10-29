package com.sleekydz86.backend.application.command

import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import java.util.concurrent.ConcurrentHashMap

@Component
class CommandBusImpl : CommandBus {

    private val handlers = ConcurrentHashMap<Class<*>, CommandHandler<*>>()

    override fun <T : StockCommand> send(command: T): Mono<CommandResult> {
        val handler = handlers[command::class.java] as? CommandHandler<T>
            ?: return Mono.just(CommandResult(
                success = false,
                message = "No handler found for command: ${command::class.simpleName}"
            ))

        return handler.handle(command)
    }

    override fun register(handler: CommandHandler<*>) {
        val commandType = handler::class.java
            .genericInterfaces
            .firstOrNull { it.typeName.contains("CommandHandler") }
            ?.let { it.actualTypeArguments.firstOrNull() }
            ?.let { Class.forName(it.typeName) }

        commandType?.let { handlers[it] = handler }
    }
}


