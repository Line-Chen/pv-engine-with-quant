package com.cmb.pvengine.integration.web.view;

import java.util.List;

/**
 * 工作流执行结果。
 */
public final class WorkflowResultView {

    private final String workflowId;

    private final WorkflowSummaryView summary;

    private final List<TaskResultView> tasks;

    public WorkflowResultView(String workflowId, WorkflowSummaryView summary,
            List<TaskResultView> tasks) {
        this.workflowId = workflowId;
        this.summary = summary;
        this.tasks = tasks;
    }

    public String getWorkflowId() {
        return workflowId;
    }

    public WorkflowSummaryView getSummary() {
        return summary;
    }

    public List<TaskResultView> getTasks() {
        return tasks;
    }
}
