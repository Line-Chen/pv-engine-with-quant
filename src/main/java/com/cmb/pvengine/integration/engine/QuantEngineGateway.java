package com.cmb.pvengine.integration.engine;

import java.util.List;

import com.cmb.pvengine.model.enumeration.EngineSessionStateEnum;
import com.cmb.pvengine.model.result.InitConfigStatus;
import com.cmb.pvengine.model.result.InitResult;
import com.cmb.pvengine.model.result.WorkflowResult;
import com.cmb.pvengine.task.Workflow;

/**
 * QUANT SDK 引擎端口，隔离 final 的 CmbPREngine。
 */
public interface QuantEngineGateway {

    InitResult initBuildRecipe(String json);

    InitResult initCalendar(String json);

    InitResult initConventions(String json);

    void initFinished();

    void resetInit();

    List<InitConfigStatus> initStatus();

    EngineSessionStateEnum sessionState();

    Workflow parseTask(String taskJson);

    Workflow parseWorkflow(String workflowJson);

    WorkflowResult runTask(String taskJson);

    WorkflowResult runWorkflow(String workflowJson);

    OneShotEngineResult executeOneShot(OneShotPayload payload);
}
