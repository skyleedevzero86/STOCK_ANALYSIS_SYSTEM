package com.sleekydz86.backend.application.command

import com.sleekydz86.backend.domain.cqrs.command.CommandResult
import com.sleekydz86.backend.domain.cqrs.command.StockCommand
import reactor.core.publisher.Mono

interface CommandHandler<T : StockCommand> {
    fun handle(command: T): Mono<CommandResult>
    fun canHandle(command: StockCommand): Boolean
}

interface CommandBus {
    fun <T : StockCommand> send(command: T): Mono<CommandResult>
    fun <T : StockCommand> register(handler: CommandHandler<T>, commandType: Class<T>)
}