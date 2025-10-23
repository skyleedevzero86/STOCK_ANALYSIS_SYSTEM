package com.sleekydz86.backend.application.controller

import org.springframework.stereotype.Controller
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.ResponseBody
import java.nio.file.Files
import java.nio.file.Paths

@Controller
class WebController {

    @GetMapping("/")
    @ResponseBody
    fun index(): String {
        return try {
            val path = Paths.get("src/main/resources/static/index.html")
            Files.readString(path)
        } catch (e: Exception) {
            "<html><body><h1>Welcome to Stock Analysis System</h1><p>Static files are not accessible</p></body></html>"
        }
    }

    @GetMapping("/admin-dashboard")
    fun adminDashboard(): String = "admin-dashboard"

    @GetMapping("/admin-login")
    fun adminLogin(): String = "admin-login"

    @GetMapping("/api-view")
    fun apiView(): String = "api-view"

    @GetMapping("/email-subscription")
    fun emailSubscription(): String = "email-subscription"

    @GetMapping("/template-management")
    fun templateManagement(): String = "template-management"
}