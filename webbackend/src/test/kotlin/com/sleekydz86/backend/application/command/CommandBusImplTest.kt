package com.sleekydz86.backend.application.command

import com.sleekydz86.backend.domain.cqrs.command.CommandResult
import com.sleekydz86.backend.domain.cqrs.command.StockCommand
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import reactor.core.publisher.Mono
import reactor.test.StepVerifier
import java.time.LocalDateTime

class CommandBusImplTest {

    private lateinit var commandBus: CommandBusImpl
    private lateinit var mockHandler: CommandHandler<StockCommand.AnalyzeStock>

    @BeforeEach
    fun setUp() {
        commandBus = CommandBusImpl()
        mockHandler = mockk()
    }

    @Test
    fun `send - should return result when handler exists`() {
        //given
        val command = StockCommand.AnalyzeStock("AAPL")
        val expectedResult = CommandResult(
            success = true,
            message = "Analysis completed",
            data = null
        )
        
        every { mockHandler.handle(command) } returns Mono.just(expectedResult)
        every { mockHandler.canHandle(any()) } returns true
        
        commandBus.register(mockHandler)

        //when
        val result = commandBus.send(command)

        //then
        StepVerifier.create(result)
            .expectNext(expectedResult)
            .verifyComplete()
        verify(exactly = 1) { mockHandler.handle(command) }
    }

    @Test
    fun `send - should return failure result when handler not found`() {
        //given
        val command = StockCommand.AnalyzeStock("AAPL")

        //when
        val result = commandBus.send(command)

        //then
        StepVerifier.create(result)
            .expectNextMatches { it.success == false && it.message.contains("No handler found") }
            .verifyComplete()
    }

    @Test
    fun `register - should register handler successfully`() {
        //given
        val handler = mockk<CommandHandler<StockCommand.AnalyzeStock>>()
        
        every { handler.canHandle(any()) } returns true
        every { handler.handle(any<StockCommand.AnalyzeStock>()) } returns Mono.just(CommandResult(true, "success"))

        //when
        commandBus.register(handler)

        //then
        val command = StockCommand.AnalyzeStock("AAPL")
        val result = commandBus.send(command)
        StepVerifier.create(result)
            .expectNextMatches { it.success == true }
            .verifyComplete()
    }

    @Test
    fun `send - should handle UpdateStockPrice command`() {
        //given
        val command = StockCommand.UpdateStockPrice(
            symbol = "AAPL",
            price = 150.0,
            volume = 1000L,
            timestamp = LocalDateTime.now()
        )

        //when
        val result = commandBus.send(command)

        //then
        StepVerifier.create(result)
            .expectNextMatches { !it.success && it.message.contains("No handler found") }
            .verifyComplete()
    }

    @Test
    fun `send - should handle GenerateTradingSignal command`() {
        //given
        val command = StockCommand.GenerateTradingSignal("AAPL", "buy")

        //when
        val result = commandBus.send(command)

        //then
        StepVerifier.create(result)
            .expectNextMatches { !it.success && it.message.contains("No handler found") }
            .verifyComplete()
    }
}
