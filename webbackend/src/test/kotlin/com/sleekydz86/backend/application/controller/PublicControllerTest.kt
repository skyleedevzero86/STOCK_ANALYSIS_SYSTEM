package com.sleekydz86.backend.application.controller

import org.junit.jupiter.api.Test
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.*
import org.springframework.test.web.servlet.setup.MockMvcBuilders

class PublicControllerTest {

    private val publicController = PublicController()
    private val mockMvc: MockMvc = MockMvcBuilders.standaloneSetup(publicController).build()

    @Test
    fun `health - should return health status`() {
        mockMvc.perform(get("/api/public/health"))
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.status").value("UP"))
            .andExpect(jsonPath("$.service").value("Stock Analysis System"))
            .andExpect(jsonPath("$.version").value("1.0.0"))
    }

    @Test
    fun `info - should return service information`() {
        mockMvc.perform(get("/api/public/info"))
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.name").value("Stock Analysis System"))
            .andExpect(jsonPath("$.description").value("Real-time stock analysis and notification system"))
            .andExpect(jsonPath("$.version").value("1.0.0"))
            .andExpect(jsonPath("$.features").isArray)
            .andExpect(jsonPath("$.features[0]").value("Real-time stock data"))
    }
}
