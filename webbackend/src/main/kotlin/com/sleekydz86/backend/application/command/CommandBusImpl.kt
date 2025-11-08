package com.sleekydz86.backend.application.command

import com.sleekydz86.backend.domain.cqrs.command.CommandResult
import com.sleekydz86.backend.domain.cqrs.command.StockCommand
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
                message = "명령에 대한 핸들러를 찾을 수 없습니다: ${command::class.java.simpleName}"
            ))

        return handler.handle(command)
    }

    override fun <T : StockCommand> register(handler: CommandHandler<T>, commandType: Class<T>) {
        handlers[commandType] = handler
    }
}


