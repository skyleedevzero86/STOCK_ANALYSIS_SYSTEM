package com.sleekydz86.backend.application.command

import reactor.core.publisher.Mono

interface CommandHandler<T : StockCommand> {
    fun handle(command: T): Mono<CommandResult>
    fun canHandle(command: StockCommand): Boolean
}

interface CommandBus {
    fun <T : StockCommand> send(command: T): Mono<CommandResult>
    fun register(handler: CommandHandler<*>)
}