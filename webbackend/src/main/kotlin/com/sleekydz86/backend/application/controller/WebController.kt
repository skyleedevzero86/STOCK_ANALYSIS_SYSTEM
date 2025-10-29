package com.sleekydz86.backend.application.controller

import org.springframework.core.io.ClassPathResource
import org.springframework.stereotype.Controller
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.ResponseBody

@Controller
class WebController {

    private val staticResourcePath = "static/"
    private val fallbackHtml = "<html><body><h1>Welcome to Stock Analysis System</h1><p>Static files are not accessible</p></body></html>"

    @GetMapping("/")
    @ResponseBody
    fun index(): String = loadHtmlFile("index.html")

    @GetMapping("/admin-dashboard")
    @ResponseBody
    fun adminDashboard(): String = loadHtmlFile("admin-dashboard.html")

    @GetMapping("/admin-login")
    @ResponseBody
    fun adminLogin(): String = loadHtmlFile("admin-login.html")

    @GetMapping("/api-view")
    @ResponseBody
    fun apiView(): String = loadHtmlFile("api-view.html")

    @GetMapping("/email-subscription")
    @ResponseBody
    fun emailSubscription(): String = loadHtmlFile("email-subscription.html")

    @GetMapping("/template-management")
    @ResponseBody
    fun templateManagement(): String = loadHtmlFile("template-management.html")

    private fun loadHtmlFile(filename: String): String {
        return try {
            val resource = ClassPathResource("$staticResourcePath$filename")
            resource.inputStream.bufferedReader().use { it.readText() }
        } catch (e: Exception) {
            fallbackHtml
        }
    }
}