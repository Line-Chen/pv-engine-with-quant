package com.cmb.pvengine.integration.web;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Arrays;
import java.util.Collections;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import com.cmb.pvengine.integration.application.QuantSdkAppService;
import com.cmb.pvengine.integration.application.SampleCatalog;
import com.cmb.pvengine.integration.application.command.WorkflowParseMode;
import com.cmb.pvengine.integration.engine.InvalidEngineInputException;
import com.cmb.pvengine.integration.web.view.CapabilitiesView;
import com.cmb.pvengine.integration.web.view.SessionStateView;
import com.cmb.pvengine.integration.web.view.WorkflowParseView;

@WebMvcTest(controllers = QuantSdkController.class)
class QuantSdkControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private QuantSdkAppService appService;

    @MockBean
    private SampleCatalog sampleCatalog;

    @Test
    void shouldReturnCapabilities() throws Exception {
        CapabilitiesView view = new CapabilitiesView("1.1.0-SNAPSHOT",
                Collections.singletonList("initBuildRecipe"),
                Collections.singletonList("BUILD_MODELS"),
                Collections.singletonList("initFixing"));
        when(appService.capabilities()).thenReturn(view);
        mockMvc.perform(get("/api/quant/capabilities"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data.sdkApiVersion").value("1.1.0-SNAPSHOT"));
    }

    @Test
    void shouldReturnSession() throws Exception {
        when(appService.sessionState()).thenReturn(new SessionStateView("UNINITIALIZED"));
        mockMvc.perform(get("/api/quant/session"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.state").value("UNINITIALIZED"));
    }

    @Test
    void shouldParseTaskJson() throws Exception {
        WorkflowParseView view = new WorkflowParseView("CNY FR007",
                Arrays.asList("CNY FR007"), 1);
        when(appService.parse(any(String.class), eq(WorkflowParseMode.TASK))).thenReturn(view);
        mockMvc.perform(post("/api/quant/workflow/parse")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"task_id\":\"CNY FR007\",\"task_type\":\"BUILD_MODELS\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.workflowId").value("CNY FR007"));
    }

    @Test
    void shouldMapInvalidInputTo400() throws Exception {
        when(appService.parse(any(String.class), eq(WorkflowParseMode.TASK)))
                .thenThrow(new InvalidEngineInputException("请求体必须是 JSON 对象"));
        mockMvc.perform(post("/api/quant/workflow/parse")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("[1]"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_INPUT"));
    }
}
