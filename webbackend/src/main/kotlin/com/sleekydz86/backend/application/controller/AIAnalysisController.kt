package com.sleekydz86.backend.application.controller

import com.sleekydz86.backend.domain.model.AIAnalysisRequest
import com.sleekydz86.backend.domain.model.AIAnalysisResult
import com.sleekydz86.backend.domain.service.AIAnalysisService
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Mono

@RestController
@RequestMapping("/api/ai-analysis")
class AIAnalysisController(
    private val aiAnalysisService: AIAnalysisService
) {

    @PostMapping("/generate")
    fun generateAnalysis(@RequestBody request: AIAnalysisRequest): Mono<ResponseEntity<AIAnalysisResult>> {
        return aiAnalysisService.generateAIAnalysis(request)
            .map { ResponseEntity.ok(it) }
    }

    @GetMapping("/symbol/{symbol}")
    fun getAnalysisBySymbol(@PathVariable symbol: String): Mono<ResponseEntity<AIAnalysisResult>> {
        val request = AIAnalysisRequest(symbol = symbol)
        return aiAnalysisService.generateAIAnalysis(request)
            .map { ResponseEntity.ok(it) }
    }
}