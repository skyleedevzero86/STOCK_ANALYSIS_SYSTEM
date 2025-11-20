package com.sleekydz86.backend.infrastructure.service

import com.deepl.api.*
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import java.util.concurrent.CompletableFuture

@Service
class DeepLTranslationService(
    @Value("\${deepl.api.key:}")
    private val apiKey: String,
    @Value("\${deepl.api.base-url:https://api.deepl.com/v2}")
    private val baseUrl: String,
    @Value("\${deepl.api.enabled:true}")
    private val enabled: Boolean
) {
    private val logger = LoggerFactory.getLogger(DeepLTranslationService::class.java)
    
    private val translator: Translator? = try {
        if (enabled && apiKey.isNotBlank()) {
            val translatorOptions = TranslatorOptions()
                .setServerUrl(baseUrl)
                .setSendPlatformInfo(false)
            Translator(apiKey, translatorOptions)
        } else {
            logger.warn("DeepL API가 비활성화되었거나 API 키가 설정되지 않았습니다.")
            null
        }
    } catch (e: Exception) {
        logger.error("DeepL Translator 초기화 실패: ${e.message}", e)
        null
    }
    
    fun isAvailable(): Boolean {
        return translator != null && enabled && apiKey.isNotBlank()
    }
    
    fun translateToKorean(text: String): Mono<String> {
        if (!isAvailable() || text.isBlank()) {
            return Mono.just(text)
        }
        
        return Mono.fromCallable {
            try {
                val options = TextTranslationOptions()
                    .setFormality(Formality.PreferMore)
                val result = translator!!.translateText(
                    text,
                    null,
                    "ko",
                    options
                )
                result.text
            } catch (e: Exception) {
                logger.warn("DeepL 번역 실패: ${e.message}, 원본 텍스트 반환", e)
                text
            }
        }
        .onErrorReturn(text)
        .timeout(java.time.Duration.ofSeconds(5))
        .doOnError { error ->
            logger.warn("DeepL 번역 타임아웃 또는 오류: ${error.message}, 원본 텍스트 반환")
        }
    }
    
    fun translateMultipleToKorean(texts: List<String>): Mono<List<String>> {
        if (!isAvailable() || texts.isEmpty()) {
            return Mono.just(texts)
        }
        
        val nonEmptyTexts = texts.filter { it.isNotBlank() }
        if (nonEmptyTexts.isEmpty()) {
            return Mono.just(texts)
        }
        
        return Mono.fromCallable {
            try {
                val futures = nonEmptyTexts.map { text ->
                    CompletableFuture.supplyAsync {
                        try {
                            val options = TextTranslationOptions()
                                .setFormality(Formality.PreferMore)
                            translator!!.translateText(
                                text,
                                null,
                                "ko",
                                options
                            ).text
                        } catch (e: Exception) {
                            logger.warn("DeepL 번역 실패 (개별): ${e.message}, 원본 텍스트 반환", e)
                            text
                        }
                    }
                }
                
                CompletableFuture.allOf(*futures.toTypedArray()).join()
                futures.map { it.get() }
            } catch (e: Exception) {
                logger.warn("DeepL 일괄 번역 실패: ${e.message}, 원본 텍스트 반환", e)
                texts
            }
        }
        .onErrorReturn(texts)
        .timeout(java.time.Duration.ofSeconds(10))
        .doOnError { error ->
            logger.warn("DeepL 일괄 번역 타임아웃 또는 오류: ${error.message}, 원본 텍스트 반환")
        }
    }
    
    fun translateNews(title: String, description: String? = null): Mono<Pair<String, String?>> {
        if (!isAvailable()) {
            return Mono.just(Pair(title, description))
        }
        
        val titleMono = if (title.isNotBlank() && !isKoreanText(title)) {
            translateToKorean(title)
        } else {
            Mono.just(title)
        }
        
        val descriptionMono = if (description != null && description.isNotBlank() && !isKoreanText(description)) {
            translateToKorean(description)
        } else {
            Mono.just(description ?: "")
        }
        
        return Mono.zip(titleMono, descriptionMono)
            .map { Pair(it.t1, if (it.t2.isNotBlank()) it.t2 else null) }
            .timeout(java.time.Duration.ofSeconds(8))
            .onErrorReturn(Pair(title, description))
    }
    
    private fun isKoreanText(text: String): Boolean {
        if (text.isBlank()) return false
        val koreanCharCount = text.count { it in '\uAC00'..'\uD7A3' }
        val totalCharCount = text.count { it.isLetterOrDigit() || it.isWhitespace() }
        if (totalCharCount == 0) return false
        val koreanRatio = koreanCharCount.toDouble() / totalCharCount
        return koreanRatio > 0.3
    }
}

