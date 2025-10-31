package com.sleekydz86.backend.infrastructure.repository

import com.sleekydz86.backend.infrastructure.entity.EmailTemplateEntity
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.stereotype.Repository

@Repository
interface EmailTemplateRepository : JpaRepository<EmailTemplateEntity, Long> {
    fun findAllByIsActiveTrue(): List<EmailTemplateEntity>
    fun findById(id: Long): EmailTemplateEntity?
}
