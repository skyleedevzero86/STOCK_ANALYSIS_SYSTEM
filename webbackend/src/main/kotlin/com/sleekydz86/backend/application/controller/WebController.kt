package com.sleekydz86.backend.application.controller

import org.springframework.core.io.ClassPathResource
import org.springframework.http.HttpHeaders
import org.springframework.http.HttpStatus
import org.springframework.http.MediaType
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RestController
import org.slf4j.LoggerFactory

@RestController
class WebController {

    private val logger = LoggerFactory.getLogger(WebController::class.java)
    private val staticResourcePath = "static/"
    private val fallbackHtml = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Error</title>
        </head>
        <body>
            <h1>Welcome to Stock Analysis System</h1>
            <p>Static files are not accessible. Please check the file path.</p>
        </body>
        </html>
    """.trimIndent()

    @GetMapping("/")
    fun index(): ResponseEntity<String> = loadHtmlFile("index.html")

    @GetMapping("/admin-dashboard")
    fun adminDashboard(): ResponseEntity<String> = loadHtmlFile("admin-dashboard.html")

    @GetMapping("/admin-login")
    fun adminLogin(): ResponseEntity<String> = loadHtmlFile("admin-login.html")

    @GetMapping("/api-view")
    fun apiView(): ResponseEntity<String> = loadHtmlFile("api-view.html")

    @GetMapping("/email-subscription")
    fun emailSubscription(): ResponseEntity<String> = loadHtmlFile("email-subscription.html")

    @GetMapping("/template-management")
    fun templateManagement(): ResponseEntity<String> = loadHtmlFile("template-management.html")

    @GetMapping("/news-detail")
    fun newsDetail(): ResponseEntity<String> = loadHtmlFile("news-detail.html")

    private fun loadHtmlFile(filename: String): ResponseEntity<String> {
        return try {
            val resource = ClassPathResource("$staticResourcePath$filename")
            
            if (!resource.exists()) {
                logger.warn("파일을 찾을 수 없습니다: $staticResourcePath$filename")
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .header(HttpHeaders.CONTENT_TYPE, MediaType.TEXT_HTML_VALUE)
                    .body(fallbackHtml)
            }

            val content = resource.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
            
            logger.debug("파일 로드 완료: $filename")
            ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, MediaType.TEXT_HTML_VALUE + "; charset=UTF-8")
                .body(content)
        } catch (e: Exception) {
            logger.error("파일 로드 오류: $staticResourcePath$filename", e)
            ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .header(HttpHeaders.CONTENT_TYPE, MediaType.TEXT_HTML_VALUE)
                .body(fallbackHtml)
        }
    }
}