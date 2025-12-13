package com.sleekydz86.backend.infrastructure.repository

import com.sleekydz86.backend.infrastructure.entity.EmailTemplateEntity
import org.springframework.data.domain.Page
import org.springframework.data.domain.Pageable
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.data.repository.query.Param
import org.springframework.stereotype.Repository

@Repository
interface EmailTemplateRepository : JpaRepository<EmailTemplateEntity, Long> {
    fun findAllByIsActiveTrue(): List<EmailTemplateEntity>
    
    @Query("SELECT e FROM EmailTemplateEntity e WHERE e.isActive = true")
    fun findAllActive(pageable: Pageable): Page<EmailTemplateEntity>
    
    @Query("SELECT e FROM EmailTemplateEntity e WHERE e.isActive = true AND (e.name LIKE CONCAT('%', :keyword, '%') OR e.subject LIKE CONCAT('%', :keyword, '%') OR e.content LIKE CONCAT('%', :keyword, '%'))")
    fun findAllActiveByKeyword(@Param("keyword") keyword: String, pageable: Pageable): Page<EmailTemplateEntity>
}
