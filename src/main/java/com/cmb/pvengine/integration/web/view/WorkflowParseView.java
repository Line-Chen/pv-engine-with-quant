package com.cmb.pvengine.integration.web.view;

import java.util.List;

/**
 * 仅解析、不执行工作流的结果。
 */
public final class WorkflowParseView {

    private final String workflowId;

    private final List<String> taskIds;

    private final int taskCount;

    public WorkflowParseView(String workflowId, List<String> taskIds, int taskCount) {
        this.workflowId = workflowId;
        this.taskIds = taskIds;
        this.taskCount = taskCount;
    }

    public String getWorkflowId() {
        return workflowId;
    }

    public List<String> getTaskIds() {
        return taskIds;
    }

    public int getTaskCount() {
        return taskCount;
    }
}
