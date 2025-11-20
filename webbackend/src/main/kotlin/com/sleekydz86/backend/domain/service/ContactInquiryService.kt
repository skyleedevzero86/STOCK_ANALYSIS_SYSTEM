package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.domain.model.ContactInquiry
import com.sleekydz86.backend.domain.model.ContactInquiryReply
import com.sleekydz86.backend.domain.model.ContactInquiryRequest
import com.sleekydz86.backend.domain.model.ContactInquiryReplyRequest
import com.sleekydz86.backend.infrastructure.entity.ContactInquiryEntity
import com.sleekydz86.backend.infrastructure.entity.ContactInquiryReplyEntity
import com.sleekydz86.backend.infrastructure.repository.ContactInquiryRepository
import com.sleekydz86.backend.infrastructure.repository.ContactInquiryReplyRepository
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import java.time.LocalDateTime

@Service
class ContactInquiryService(
    private val contactInquiryRepository: ContactInquiryRepository,
    private val contactInquiryReplyRepository: ContactInquiryReplyRepository
) {

    fun createInquiry(request: ContactInquiryRequest): Mono<ContactInquiry> {
        return Mono.fromCallable {
            val inquiry = ContactInquiryEntity(
                name = request.name,
                email = request.email,
                phone = request.phone,
                category = request.category,
                subject = request.subject,
                message = request.message,
                isRead = false,
                createdAt = LocalDateTime.now(),
                updatedAt = LocalDateTime.now()
            )

            val saved = contactInquiryRepository.save(inquiry)
            saved.toDomain()
        }
    }

    fun getAllInquiries(page: Int, size: Int, keyword: String?, category: String?): Mono<Pair<List<ContactInquiry>, Long>> {
        return Mono.fromCallable {
            val pageable = org.springframework.data.domain.PageRequest.of(page, size)
            val result = if (keyword != null && keyword.isNotBlank() || category != null && category.isNotBlank()) {
                contactInquiryRepository.findAllWithFilters(
                    keyword?.takeIf { it.isNotBlank() },
                    category?.takeIf { it.isNotBlank() },
                    pageable
                )
            } else {
                contactInquiryRepository.findAllOrderByCreatedAtDesc(pageable)
            }

            val inquiries = result.content.map { it.toDomain() }
            Pair(inquiries, result.totalElements)
        }
    }

    fun getInquiryById(id: Long): Mono<ContactInquiry> {
        return Mono.fromCallable {
            val entity = contactInquiryRepository.findById(id)
                .orElseThrow { IllegalArgumentException("문의사항을 찾을 수 없습니다.") }
            entity.toDomain()
        }
    }

    fun markAsRead(id: Long): Mono<ContactInquiry> {
        return Mono.fromCallable {
            val entity = contactInquiryRepository.findById(id)
                .orElseThrow { IllegalArgumentException("문의사항을 찾을 수 없습니다.") }

            val updated = entity.copy(
                isRead = true,
                updatedAt = LocalDateTime.now()
            )

            val saved = contactInquiryRepository.save(updated)
            saved.toDomain()
        }
    }

    fun deleteInquiry(id: Long): Mono<Boolean> {
        return Mono.fromCallable {
            if (!contactInquiryRepository.existsById(id)) {
                throw IllegalArgumentException("문의사항을 찾을 수 없습니다.")
            }
            contactInquiryRepository.deleteById(id)
            true
        }
    }

    fun addReply(request: ContactInquiryReplyRequest): Mono<ContactInquiryReply> {
        return Mono.fromCallable {
            if (!contactInquiryRepository.existsById(request.inquiryId)) {
                throw IllegalArgumentException("문의사항을 찾을 수 없습니다.")
            }

            val reply = ContactInquiryReplyEntity(
                inquiryId = request.inquiryId,
                content = request.content,
                createdBy = request.createdBy,
                createdAt = LocalDateTime.now()
            )

            val inquiryEntity = contactInquiryRepository.findById(request.inquiryId).orElse(null)
            if (inquiryEntity != null) {
                val updated = inquiryEntity.copy(
                    isRead = true,
                    updatedAt = LocalDateTime.now()
                )
                contactInquiryRepository.save(updated)
            }

            val saved = contactInquiryReplyRepository.save(reply)
            saved.toDomain()
        }
    }

    fun getRepliesByInquiryId(inquiryId: Long): Mono<List<ContactInquiryReply>> {
        return Mono.fromCallable {
            contactInquiryReplyRepository.findByInquiryId(inquiryId)
                .map { it.toDomain() }
        }
    }
}


