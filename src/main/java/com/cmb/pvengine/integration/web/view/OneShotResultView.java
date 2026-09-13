package com.cmb.pvengine.integration.web.view;

/**
 * 一次性 init + run 的聚合结果。
 */
public final class OneShotResultView {

    private final InitResultView buildRecipe;

    private final InitResultView calendar;

    private final InitResultView conventions;

    private final WorkflowResultView workflow;

    public OneShotResultView(InitResultView buildRecipe, InitResultView calendar,
            InitResultView conventions, WorkflowResultView workflow) {
        this.buildRecipe = buildRecipe;
        this.calendar = calendar;
        this.conventions = conventions;
        this.workflow = workflow;
    }

    public InitResultView getBuildRecipe() {
        return buildRecipe;
    }

    public InitResultView getCalendar() {
        return calendar;
    }

    public InitResultView getConventions() {
        return conventions;
    }

    public WorkflowResultView getWorkflow() {
        return workflow;
    }
}
