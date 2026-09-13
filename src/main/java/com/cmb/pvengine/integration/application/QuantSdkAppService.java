package com.cmb.pvengine.integration.application;

import java.util.Arrays;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.cmb.pvengine.integration.application.command.OneShotRunCommand;
import com.cmb.pvengine.integration.application.command.WorkflowParseMode;
import com.cmb.pvengine.integration.engine.InvalidEngineInputException;
import com.cmb.pvengine.integration.engine.OneShotEngineResult;
import com.cmb.pvengine.integration.engine.OneShotPayload;
import com.cmb.pvengine.integration.engine.QuantEngineGateway;
import com.cmb.pvengine.integration.web.assembler.QuantResultAssembler;
import com.cmb.pvengine.integration.web.view.CapabilitiesView;
import com.cmb.pvengine.integration.web.view.InitConfigStatusView;
import com.cmb.pvengine.integration.web.view.InitResultView;
import com.cmb.pvengine.integration.web.view.OneShotResultView;
import com.cmb.pvengine.integration.web.view.SessionStateView;
import com.cmb.pvengine.integration.web.view.WorkflowParseView;
import com.cmb.pvengine.integration.web.view.WorkflowResultView;
import com.cmb.pvengine.model.constant.TaskTypes;
import com.cmb.pvengine.task.Workflow;

/**
 * QUANT SDK 应用服务：校验入参、调用引擎、组装视图。
 */
@Service
public class QuantSdkAppService {

    private static final Logger LOGGER = LoggerFactory.getLogger(QuantSdkAppService.class);

    private static final String SDK_API_VERSION = "1.1.0-SNAPSHOT";

    private final QuantEngineGateway gateway;

    private final QuantResultAssembler assembler;

    private final JsonPayloadSupport jsonPayloadSupport;

    public QuantSdkAppService(QuantEngineGateway gateway, QuantResultAssembler assembler,
            JsonPayloadSupport jsonPayloadSupport) {
        this.gateway = gateway;
        this.assembler = assembler;
        this.jsonPayloadSupport = jsonPayloadSupport;
    }

    public CapabilitiesView capabilities() {
        return new CapabilitiesView(
                SDK_API_VERSION,
                Arrays.asList("initBuildRecipe", "initCalendar", "initConventions",
                        "initFinished", "resetInit", "initStatus", "run"),
                Arrays.asList(TaskTypes.BUILD_MODELS),
                Arrays.asList("initFixing", "initFutureStartDates", "PV", "PV_RISK", "PV_ARRAY"));
    }

    public SessionStateView sessionState() {
        return assembler.toSessionStateView(gateway.sessionState());
    }

    public List<InitConfigStatusView> initStatus() {
        return assembler.toInitStatusViews(gateway.initStatus());
    }

    public InitResultView initBuildRecipe(String json) {
        String normalized = jsonPayloadSupport.normalizeInitJson(json);
        LOGGER.info("装载 BUILD_RECIPE, payloadBytes={}", payloadBytes(normalized));
        return assembler.toInitResultView(gateway.initBuildRecipe(normalized));
    }

    public InitResultView initCalendar(String json) {
        String normalized = jsonPayloadSupport.normalizeInitJson(json);
        LOGGER.info("装载 CALENDAR, payloadBytes={}", payloadBytes(normalized));
        return assembler.toInitResultView(gateway.initCalendar(normalized));
    }

    public InitResultView initConventions(String json) {
        String normalized = jsonPayloadSupport.normalizeInitJson(json);
        LOGGER.info("装载 CONVENTION, payloadBytes={}", payloadBytes(normalized));
        return assembler.toInitResultView(gateway.initConventions(normalized));
    }

    public SessionStateView initFinished() {
        gateway.initFinished();
        return sessionState();
    }

    public SessionStateView resetInit() {
        gateway.resetInit();
        return sessionState();
    }

    public WorkflowParseView parse(String json, WorkflowParseMode mode) {
        String normalized = jsonPayloadSupport.requireJsonObject(json);
        Workflow workflow = parseWorkflow(normalized, mode);
        return assembler.toParseView(workflow);
    }

    public WorkflowResultView run(String json, WorkflowParseMode mode) {
        String normalized = jsonPayloadSupport.requireJsonObject(json);
        LOGGER.info("执行工作流, parseMode={}, payloadBytes={}", mode, payloadBytes(normalized));
        if (mode == WorkflowParseMode.WORKFLOW) {
            return assembler.toWorkflowResultView(gateway.runWorkflow(normalized));
        }
        return assembler.toWorkflowResultView(gateway.runTask(normalized));
    }

    public OneShotResultView runOneShot(OneShotRunCommand command) {
        if (command == null) {
            throw new InvalidEngineInputException("oneshot 命令不能为空");
        }
        if (command.getPayload() == null || command.getPayload().isNull()) {
            throw new InvalidEngineInputException("payload 不能为空");
        }
        OneShotPayload payload = OneShotPayload.builder()
                .buildRecipeJson(jsonPayloadSupport.writeObject(command.getBuildRecipe(), "buildRecipe"))
                .calendarJson(jsonPayloadSupport.writeObject(command.getCalendar(), "calendar"))
                .conventionsJson(jsonPayloadSupport.writeObject(command.getConventions(), "conventions"))
                .payloadJson(jsonPayloadSupport.writeObject(command.getPayload(), "payload"))
                .parseMode(command.getParseMode())
                .resetBeforeInit(command.isResetBeforeInit())
                .build();
        LOGGER.info("一次性执行, parseMode={}, resetBeforeInit={}",
                payload.getParseMode(), payload.isResetBeforeInit());
        OneShotEngineResult result = gateway.executeOneShot(payload);
        return assembler.toOneShotView(result);
    }

    private Workflow parseWorkflow(String json, WorkflowParseMode mode) {
        if (mode == WorkflowParseMode.WORKFLOW) {
            return gateway.parseWorkflow(json);
        }
        return gateway.parseTask(json);
    }

    private int payloadBytes(String json) {
        if (json == null) {
            return 0;
        }
        return json.length();
    }
}
