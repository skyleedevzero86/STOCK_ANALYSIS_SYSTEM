package com.sleekydz86.backend.infrastructure.repository

import com.sleekydz86.backend.infrastructure.entity.ContactInquiryReplyEntity
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.stereotype.Repository

@Repository
interface ContactInquiryReplyRepository : JpaRepository<ContactInquiryReplyEntity, Long> {

    @Query("SELECT r FROM ContactInquiryReplyEntity r WHERE r.inquiryId = :inquiryId ORDER BY r.createdAt ASC")
    fun findByInquiryId(inquiryId: Long): List<ContactInquiryReplyEntity>
}


