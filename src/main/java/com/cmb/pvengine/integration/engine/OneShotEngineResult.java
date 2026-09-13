package com.cmb.pvengine.integration.engine;

import com.cmb.pvengine.model.result.InitResult;
import com.cmb.pvengine.model.result.WorkflowResult;

/**
 * 一次性执行的 init 切片结果与工作流结果。
 */
public final class OneShotEngineResult {

    private final InitResult buildRecipe;

    private final InitResult calendar;

    private final InitResult conventions;

    private final WorkflowResult workflowResult;

    public OneShotEngineResult(InitResult buildRecipe, InitResult calendar,
            InitResult conventions, WorkflowResult workflowResult) {
        this.buildRecipe = buildRecipe;
        this.calendar = calendar;
        this.conventions = conventions;
        this.workflowResult = workflowResult;
    }

    public InitResult getBuildRecipe() {
        return buildRecipe;
    }

    public InitResult getCalendar() {
        return calendar;
    }

    public InitResult getConventions() {
        return conventions;
    }

    public WorkflowResult getWorkflowResult() {
        return workflowResult;
    }
}
