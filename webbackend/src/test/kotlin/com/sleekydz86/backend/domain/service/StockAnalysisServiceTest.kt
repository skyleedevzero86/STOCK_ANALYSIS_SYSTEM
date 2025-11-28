package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.*
import com.sleekydz86.backend.domain.repository.StockRepository
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.DisplayName
import org.junit.jupiter.api.Test
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import reactor.test.StepVerifier
import java.time.Duration
import java.time.LocalDateTime

class StockAnalysisServiceTest {

    private lateinit var stockRepository: StockRepository
    private lateinit var stockAnalysisService: StockAnalysisService

    @BeforeEach
    fun setUp() {
        stockRepository = mockk()
        stockAnalysisService = StockAnalysisService(stockRepository)
    }

    @Test
    @DisplayName("?�시�?주식 ?�이??조회 - ?�볼??존재????주식 ?�이??반환")
    fun `getRealtimeStockData - should return stock data when symbol exists`() {

        val symbol = "AAPL"
        val stockData = StockData(
            symbol = symbol,
            currentPrice = 150.0,
            volume = 1000000L,
            changePercent = 2.5,
            timestamp = LocalDateTime.now()
        )

        every { stockRepository.getRealtimeData.invoke(symbol) } returns Mono.just(stockData)

        val result = stockAnalysisService.getRealtimeStockData(symbol)

        StepVerifier.create(result)
            .expectNext(stockData)
            .verifyComplete()
        verify(exactly = 1) { stockRepository.getRealtimeData.invoke(symbol) }
    }

    @Test
    @DisplayName("?�시�?주식 ?�이??조회 - ?�볼??찾을 ???�을 ???�러 처리")
    fun `getRealtimeStockData - should handle error when symbol not found`() {

        val symbol = "INVALID"
        val error = RuntimeException("Stock not found")

        every { stockRepository.getRealtimeData.invoke(symbol) } returns Mono.error(error)

        val result = stockAnalysisService.getRealtimeStockData(symbol)

        StepVerifier.create(result)
            .expectError(RuntimeException::class.java)
            .verify()
        verify(exactly = 1) { stockRepository.getRealtimeData.invoke(symbol) }
    }

    @Test
    @DisplayName("?�체 ?�시�?주식 ?�이??조회 - 주식 ?�이??Flux 반환")
    fun `getAllRealtimeStockData - should return flux of stock data`() {

        val stockData1 = StockData(
            symbol = "AAPL",
            currentPrice = 150.0,
            volume = 1000000L,
            changePercent = 2.5,
            timestamp = LocalDateTime.now()
        )
        val stockData2 = StockData(
            symbol = "GOOGL",
            currentPrice = 2500.0,
            volume = 500000L,
            changePercent = -1.2,
            timestamp = LocalDateTime.now()
        )
        val stockDataList = listOf(stockData1, stockData2)

        every { stockRepository.getAllRealtimeData.invoke() } returns Flux.fromIterable(stockDataList)

        val result = stockAnalysisService.getAllRealtimeStockData()

        StepVerifier.create(result)
            .expectNext(stockData1)
            .expectNext(stockData2)
            .verifyComplete()
        verify(exactly = 1) { stockRepository.getAllRealtimeData.invoke() }
    }

    @Test
    @DisplayName("주식 분석 조회 - ?�볼??존재????기술??분석 반환")
    fun `getStockAnalysis - should return technical analysis when symbol exists`() {

        val symbol = "AAPL"
        val technicalAnalysis = TechnicalAnalysis(
            symbol = symbol,
            currentPrice = 150.0,
            volume = 1000000L,
            changePercent = 2.5,
            trend = "UPWARD",
            trendStrength = 0.8,
            signals = TradingSignals(
                signal = "BUY",
                confidence = 0.85,
                rsi = 65.0,
                macd = 1.2,
                macdSignal = 1.0
            ),
            anomalies = emptyList(),
            timestamp = LocalDateTime.now()
        )

        every { stockRepository.getAnalysis.invoke(symbol) } returns Mono.just(technicalAnalysis)

        val result = stockAnalysisService.getStockAnalysis(symbol)

        StepVerifier.create(result)
            .expectNext(technicalAnalysis)
            .verifyComplete()
        verify(exactly = 1) { stockRepository.getAnalysis.invoke(symbol) }
    }

    @Test
    @DisplayName("주식 분석 조회 - 분석??찾을 ???�을 ???�러 처리")
    fun `getStockAnalysis - should handle error when analysis not found`() {

        val symbol = "INVALID"
        val error = RuntimeException("Analysis not found")

        every { stockRepository.getAnalysis.invoke(symbol) } returns Mono.error(error)

        val result = stockAnalysisService.getStockAnalysis(symbol)

        StepVerifier.create(result)
            .expectError(RuntimeException::class.java)
            .verify()
        verify(exactly = 1) { stockRepository.getAnalysis.invoke(symbol) }
    }

    @Test
    @DisplayName("?�체 주식 분석 조회 - 기술??분석 Flux 반환")
    fun `getAllStockAnalysis - should return flux of technical analysis`() {

        val analysis1 = TechnicalAnalysis(
            symbol = "AAPL",
            currentPrice = 150.0,
            volume = 1000000L,
            changePercent = 2.5,
            trend = "UPWARD",
            trendStrength = 0.8,
            signals = TradingSignals(signal = "BUY", confidence = 0.85, rsi = 65.0, macd = 1.2, macdSignal = 1.0),
            anomalies = emptyList(),
            timestamp = LocalDateTime.now()
        )
        val analysis2 = TechnicalAnalysis(
            symbol = "GOOGL",
            currentPrice = 2500.0,
            volume = 500000L,
            changePercent = -1.2,
            trend = "DOWNWARD",
            trendStrength = 0.6,
            signals = TradingSignals(signal = "SELL", confidence = 0.70, rsi = 35.0, macd = -0.5, macdSignal = -0.3),
            anomalies = emptyList(),
            timestamp = LocalDateTime.now()
        )
        val analysisList = listOf(analysis1, analysis2)

        every { stockRepository.getAllAnalysis.invoke() } returns Flux.fromIterable(analysisList)

        val result = stockAnalysisService.getAllStockAnalysis()

        StepVerifier.create(result)
            .expectNext(analysis1)
            .expectNext(analysis2)
            .verifyComplete()
        verify(exactly = 1) { stockRepository.getAllAnalysis.invoke() }
    }

    @Test
    @DisplayName("주식 과거 ?�이??조회 - ?�볼??존재????과거 ?�이??반환")
    fun `getStockHistoricalData - should return historical data when symbol exists`() {

        val symbol = "AAPL"
        val days = 30
        val historicalData = HistoricalData(
            symbol = symbol,
            data = listOf(
                ChartDataPoint(
                    date = "2024-01-01",
                    close = 150.0,
                    volume = 1000000L,
                    rsi = 65.0,
                    macd = 1.2,
                    bbUpper = 155.0,
                    bbLower = 145.0,
                    sma20 = 148.0
                )
            ),
            period = days
        )

        every { stockRepository.getHistoricalData.invoke(symbol, days) } returns Mono.just(historicalData)

        val result = stockAnalysisService.getStockHistoricalData(symbol, days)

        StepVerifier.create(result)
            .expectNext(historicalData)
            .verifyComplete()
        verify(exactly = 1) { stockRepository.getHistoricalData.invoke(symbol, days) }
    }

    @Test
    @DisplayName("주식 과거 ?�이??조회 - 과거 ?�이?��? 찾을 ???�을 ???�러 처리")
    fun `getStockHistoricalData - should handle error when historical data not found`() {

        val symbol = "INVALID"
        val days = 30
        val error = RuntimeException("Historical data not found")

        every { stockRepository.getHistoricalData.invoke(symbol, days) } returns Mono.error(error)

        val result = stockAnalysisService.getStockHistoricalData(symbol, days)

        StepVerifier.create(result)
            .expectError(RuntimeException::class.java)
            .verify()
        verify(exactly = 1) { stockRepository.getHistoricalData.invoke(symbol, days) }
    }

    @Test
    @DisplayName("?�용 가?�한 ?�볼 조회 - ?�용 가?�한 ?�볼 목록 반환")
    fun `getAvailableSymbols - should return list of available symbols`() {

        val symbols = listOf("AAPL", "GOOGL", "MSFT", "AMZN")

        every { stockRepository.getAvailableSymbols.invoke() } returns Mono.just(symbols)

        val result = stockAnalysisService.getAvailableSymbols()

        StepVerifier.create(result)
            .expectNext(symbols)
            .verifyComplete()
        verify(exactly = 1) { stockRepository.getAvailableSymbols.invoke() }
    }

    @Test
    @DisplayName("?�용 가?�한 ?�볼 조회 - ?�용 가?�한 ?�볼???�을 ??�?목록 반환")
    fun `getAvailableSymbols - should return empty list when no symbols available`() {

        val emptySymbols = emptyList<String>()

        every { stockRepository.getAvailableSymbols.invoke() } returns Mono.just(emptySymbols)

        val result = stockAnalysisService.getAvailableSymbols()

        StepVerifier.create(result)
            .expectNext(emptySymbols)
            .verifyComplete()
        verify(exactly = 1) { stockRepository.getAvailableSymbols.invoke() }
    }

    @Test
    @DisplayName("?�시�?분석 ?�트�?- 주기?�으�?분석 ?�이??방출")
    fun `getRealtimeAnalysisStream - should emit analysis periodically`() {

        val analysis = TechnicalAnalysis(
            symbol = "AAPL",
            currentPrice = 150.0,
            volume = 1000000L,
            changePercent = 2.5,
            trend = "UPWARD",
            trendStrength = 0.8,
            signals = TradingSignals(signal = "BUY", confidence = 0.85, rsi = 65.0, macd = 1.2, macdSignal = 1.0),
            anomalies = emptyList(),
            timestamp = LocalDateTime.now()
        )

        every { stockRepository.getAllAnalysis.invoke() } returns Flux.just(analysis)

        val result = stockAnalysisService.getRealtimeAnalysisStream()

        StepVerifier.create(result)
            .expectNextCount(1)
            .thenCancel()
            .verify()
    }

    @Test
    @DisplayName("?�시�?분석 ?�트�??�시???�함) - ?�러 발생 ???�시??)
    fun `getRealtimeAnalysisStreamWithRetry - should retry on error`() {

        val error = RuntimeException("Connection error")
        val analysis = TechnicalAnalysis(
            symbol = "AAPL",
            currentPrice = 150.0,
            volume = 1000000L,
            changePercent = 2.5,
            trend = "UPWARD",
            trendStrength = 0.8,
            signals = TradingSignals(signal = "BUY", confidence = 0.85, rsi = 65.0, macd = 1.2, macdSignal = 1.0),
            anomalies = emptyList(),
            timestamp = LocalDateTime.now()
        )

        every { stockRepository.getAllAnalysis.invoke() } returnsMany listOf(
            Flux.error(error),
            Flux.just(analysis)
        )

        val result = stockAnalysisService.getRealtimeAnalysisStreamWithRetry()

        StepVerifier.create(result)
            .expectNext(analysis)
            .thenCancel()
            .verify()
    }
}
