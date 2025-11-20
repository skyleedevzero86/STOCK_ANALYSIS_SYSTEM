package com.sleekydz86.backend.infrastructure.repository

import com.sleekydz86.backend.infrastructure.entity.ContactInquiryEntity
import org.springframework.data.domain.Page
import org.springframework.data.domain.Pageable
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query
import org.springframework.stereotype.Repository

@Repository
interface ContactInquiryRepository : JpaRepository<ContactInquiryEntity, Long> {

    @Query("SELECT c FROM ContactInquiryEntity c WHERE " +
            "(:keyword IS NULL OR :keyword = '' OR " +
            "c.name LIKE CONCAT('%', :keyword, '%') OR " +
            "c.email LIKE CONCAT('%', :keyword, '%') OR " +
            "c.subject LIKE CONCAT('%', :keyword, '%') OR " +
            "c.message LIKE CONCAT('%', :keyword, '%')) AND " +
            "(:category IS NULL OR :category = '' OR c.category = :category)")
    fun findAllWithFilters(keyword: String?, category: String?, pageable: Pageable): Page<ContactInquiryEntity>

    @Query("SELECT c FROM ContactInquiryEntity c ORDER BY c.createdAt DESC")
    fun findAllOrderByCreatedAtDesc(pageable: Pageable): Page<ContactInquiryEntity>
}


