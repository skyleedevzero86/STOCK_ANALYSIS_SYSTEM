package com.sleekydz86.backend.application.controller

import org.junit.jupiter.api.Test
import org.springframework.test.web.servlet.MockMvc
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get
import org.springframework.test.web.servlet.result.MockMvcResultMatchers.*
import org.springframework.test.web.servlet.setup.MockMvcBuilders

class WebControllerTest {

    private val webController = WebController()
    private val mockMvc: MockMvc = MockMvcBuilders.standaloneSetup(webController).build()

    @Test
    fun `index - should return index html`() {
        //given
        
        //when & then
        mockMvc.perform(get("/"))
            .andExpect(status().isOk)
            .andExpect(content().contentTypeCompatibleWith("text/html"))
    }

    @Test
    fun `adminDashboard - should return admin dashboard html`() {
        //given
        
        //when & then
        mockMvc.perform(get("/admin-dashboard"))
            .andExpect(status().isOk)
            .andExpect(content().contentTypeCompatibleWith("text/html"))
    }

    @Test
    fun `adminLogin - should return admin login html`() {
        //given
        
        //when & then
        mockMvc.perform(get("/admin-login"))
            .andExpect(status().isOk)
            .andExpect(content().contentTypeCompatibleWith("text/html"))
    }

    @Test
    fun `apiView - should return api view html`() {
        //given
        
        //when & then
        mockMvc.perform(get("/api-view"))
            .andExpect(status().isOk)
            .andExpect(content().contentTypeCompatibleWith("text/html"))
    }

    @Test
    fun `emailSubscription - should return email subscription html`() {
        //given
        
        //when & then
        mockMvc.perform(get("/email-subscription"))
            .andExpect(status().isOk)
            .andExpect(content().contentTypeCompatibleWith("text/html"))
    }

    @Test
    fun `templateManagement - should return template management html`() {
        //given
        
        //when & then
        mockMvc.perform(get("/template-management"))
            .andExpect(status().isOk)
            .andExpect(content().contentTypeCompatibleWith("text/html"))
    }
}
