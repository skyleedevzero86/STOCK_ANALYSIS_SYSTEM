package com.sleekydz86.backend.domain.service

import com.sleekydz86.backend.infrastructure.entity.NotificationLogEntity
import com.sleekydz86.backend.infrastructure.repository.NotificationLogRepository
import org.springframework.data.domain.PageRequest
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import java.time.LocalDateTime

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

    fun saveEmailLog(
        userEmail: String,
        subject: String?,
        message: String,
        status: String,
        errorMessage: String? = null,
        source: String = "manual",
        notificationType: String = "email",
        symbol: String? = null
    ): Mono<NotificationLogEntity> {
        return Mono.fromCallable {
            val logMessage = if (source == "manual") {
                if (subject != null) {
                "[수기발송] $subject\n$message"
                } else {
                    "[수기발송] $message"
                }
            } else if (source == "airflow") {
                if (subject != null) {
                "[Airflow발송] $subject\n$message"
                } else {
                    "[Airflow발송] $message"
                }
            } else {
                if (subject != null) {
                "[$source] $subject\n$message"
                } else {
                    "[$source] $message"
                }
            }
            
            val finalSymbol = if (source == "manual") {
                symbol ?: "notice"
            } else {
                symbol
            }
            
            val logEntity = NotificationLogEntity(
                userEmail = userEmail,
                symbol = finalSymbol,
                notificationType = notificationType.lowercase(),
                message = logMessage,
                sentAt = LocalDateTime.now(),
                status = status,
                errorMessage = errorMessage
            )
            
            notificationLogRepository.save(logEntity)
        }
    }

    fun getEmailHistoryBySubject(subject: String, page: Int, size: Int): Mono<Pair<List<Map<String, Any>>, Long>> {
        return Mono.fromCallable {
            val pageable = PageRequest.of(page, size)
            val pageResult = notificationLogRepository.findByMessageContainingSubject(subject, pageable)
            
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

    fun getEmailHistoryBySubject(subject: String): Mono<List<Map<String, Any>>> {
        return Mono.fromCallable {
            notificationLogRepository.findByMessageContainingSubject(subject).map { entity ->
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

