package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.infrastructure.entity.NotificationLogEntity
import com.sleekydz86.backend.infrastructure.repository.NotificationLogRepository
import org.springframework.data.domain.PageRequest
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono

@Service
class NotificationLogService(
    private val notificationLogRepository: NotificationLogRepository
) {

    fun getEmailHistoryByUserEmail(email: String, page: Int, size: Int): Mono<Pair<List<Map<String, Any>>, Long>> {
        return Mono.fromCallable {
            val pageable = PageRequest.of(page, size)
            val pageResult = notificationLogRepository.findByUserEmail(email, pageable)
            
            val logs = pageResult.content.map { entity ->
                mapOf(
                    "id" to (entity.id ?: 0),
                    "userEmail" to entity.userEmail,
                    "symbol" to (entity.symbol ?: ""),
                    "notificationType" to entity.notificationType.uppercase(),
                    "message" to (entity.message ?: ""),
                    "sentAt" to entity.sentAt.toString(),
                    "status" to entity.status.uppercase(),
                    "errorMessage" to (entity.errorMessage ?: "")
                )
            }
            
            Pair(logs, pageResult.totalElements)
        }
    }

    fun getEmailHistoryByUserEmail(email: String): Mono<List<Map<String, Any>>> {
        return Mono.fromCallable {
            notificationLogRepository.findByUserEmail(email).map { entity ->
                mapOf(
                    "id" to (entity.id ?: 0),
                    "userEmail" to entity.userEmail,
                    "symbol" to (entity.symbol ?: ""),
                    "notificationType" to entity.notificationType.uppercase(),
                    "message" to (entity.message ?: ""),
                    "sentAt" to entity.sentAt.toString(),
                    "status" to entity.status.uppercase(),
                    "errorMessage" to (entity.errorMessage ?: "")
                )
            }
        }
    }
}

