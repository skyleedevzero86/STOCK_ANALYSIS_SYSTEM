package com.sleekydz86.backend.infrastructure.repository

import com.sleekydz86.backend.infrastructure.entity.AIAnalysisResultEntity
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.stereotype.Repository
import java.time.LocalDateTime

@Repository
interface AIAnalysisResultRepository : JpaRepository<AIAnalysisResultEntity, Long> {
    fun findBySymbolAndCreatedAtAfter(symbol: String, createdAt: LocalDateTime): List<AIAnalysisResultEntity>
    fun findByAnalysisType(analysisType: String): List<AIAnalysisResultEntity>
    fun findTop10ByOrderByCreatedAtDesc(): List<AIAnalysisResultEntity>
}
