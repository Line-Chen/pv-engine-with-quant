package com.cmb.pvengine.integration.web;

import java.util.List;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.cmb.pvengine.integration.application.QuantSdkAppService;
import com.cmb.pvengine.integration.application.SampleCatalog;
import com.cmb.pvengine.integration.application.command.OneShotRunCommand;
import com.cmb.pvengine.integration.application.command.WorkflowParseMode;
import com.cmb.pvengine.integration.web.view.ApiResponse;
import com.cmb.pvengine.integration.web.view.CapabilitiesView;
import com.cmb.pvengine.integration.web.view.InitConfigStatusView;
import com.cmb.pvengine.integration.web.view.InitResultView;
import com.cmb.pvengine.integration.web.view.OneShotResultView;
import com.cmb.pvengine.integration.web.view.SessionStateView;
import com.cmb.pvengine.integration.web.view.WorkflowParseView;
import com.cmb.pvengine.integration.web.view.WorkflowResultView;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * QUANT SDK 可测试 HTTP 入口，按文档生命周期暴露 init / run。
 */
@RestController
@RequestMapping("/api/quant")
public class QuantSdkController {

    private final QuantSdkAppService appService;

    private final SampleCatalog sampleCatalog;

    private final ObjectMapper objectMapper;

    public QuantSdkController(QuantSdkAppService appService, SampleCatalog sampleCatalog,
            ObjectMapper objectMapper) {
        this.appService = appService;
        this.sampleCatalog = sampleCatalog;
        this.objectMapper = objectMapper;
    }

    @GetMapping("/health")
    public ApiResponse<SessionStateView> health() {
        return ApiResponse.ok(appService.sessionState());
    }

    @GetMapping("/capabilities")
    public ApiResponse<CapabilitiesView> capabilities() {
        return ApiResponse.ok(appService.capabilities());
    }

    @GetMapping("/session")
    public ApiResponse<SessionStateView> session() {
        return ApiResponse.ok(appService.sessionState());
    }

    @GetMapping("/init/status")
    public ApiResponse<List<InitConfigStatusView>> initStatus() {
        return ApiResponse.ok(appService.initStatus());
    }

    @PostMapping(value = "/init/build-recipe", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ApiResponse<InitResultView> initBuildRecipe(@RequestBody(required = false) String json) {
        return ApiResponse.ok(appService.initBuildRecipe(json));
    }

    @PostMapping(value = "/init/calendar", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ApiResponse<InitResultView> initCalendar(@RequestBody(required = false) String json) {
        return ApiResponse.ok(appService.initCalendar(json));
    }

    @PostMapping(value = "/init/conventions", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ApiResponse<InitResultView> initConventions(@RequestBody(required = false) String json) {
        return ApiResponse.ok(appService.initConventions(json));
    }

    @PostMapping("/init/finished")
    public ApiResponse<SessionStateView> initFinished() {
        return ApiResponse.ok(appService.initFinished());
    }

    @PostMapping("/init/reset")
    public ApiResponse<SessionStateView> resetInit() {
        return ApiResponse.ok(appService.resetInit());
    }

    @PostMapping(value = "/workflow/parse", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ApiResponse<WorkflowParseView> parse(@RequestBody String json,
            @RequestParam(defaultValue = "TASK") WorkflowParseMode mode) {
        return ApiResponse.ok(appService.parse(json, mode));
    }

    @PostMapping(value = "/run/task", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ApiResponse<WorkflowResultView> runTask(@RequestBody String json) {
        return ApiResponse.ok(appService.run(json, WorkflowParseMode.TASK));
    }

    @PostMapping(value = "/run/workflow", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ApiResponse<WorkflowResultView> runWorkflow(@RequestBody String json) {
        return ApiResponse.ok(appService.run(json, WorkflowParseMode.WORKFLOW));
    }

    @PostMapping(value = "/run/oneshot", consumes = MediaType.APPLICATION_JSON_VALUE)
    public ApiResponse<OneShotResultView> runOneShot(@RequestBody OneShotRunCommand command) {
        return ApiResponse.ok(appService.runOneShot(command));
    }

    @GetMapping("/samples")
    public ApiResponse<List<String>> samples() {
        return ApiResponse.ok(sampleCatalog.names());
    }

    @GetMapping(value = "/samples/{name}", produces = MediaType.APPLICATION_JSON_VALUE)
    public String sample(@PathVariable("name") String name) {
        return sampleCatalog.load(name);
    }

    /**
     * 使用内置 CNY FR007 样例走完 init + run，便于开箱验证 HTTP 链路。
     */
    @PostMapping("/run/oneshot/sample/cny-fr007")
    public ApiResponse<OneShotResultView> runBundledCnyFr007() {
        try {
            String raw = sampleCatalog.load("oneshot-cny-fr007");
            OneShotRunCommand command = objectMapper.readValue(raw, OneShotRunCommand.class);
            return ApiResponse.ok(appService.runOneShot(command));
        } catch (RuntimeException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new IllegalStateException("内置样例无法解析", ex);
        }
    }
}
