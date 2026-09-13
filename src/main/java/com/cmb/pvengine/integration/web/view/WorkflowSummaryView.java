package com.cmb.pvengine.integration.web.view;

/**
 * 工作流汇总计数。
 */
public final class WorkflowSummaryView {

    private final int totalTasks;

    private final int succeeded;

    private final int failed;

    private final int cancelled;

    private final long elapsedMillis;

    public WorkflowSummaryView(int totalTasks, int succeeded, int failed,
            int cancelled, long elapsedMillis) {
        this.totalTasks = totalTasks;
        this.succeeded = succeeded;
        this.failed = failed;
        this.cancelled = cancelled;
        this.elapsedMillis = elapsedMillis;
    }

    public int getTotalTasks() {
        return totalTasks;
    }

    public int getSucceeded() {
        return succeeded;
    }

    public int getFailed() {
        return failed;
    }

    public int getCancelled() {
        return cancelled;
    }

    public long getElapsedMillis() {
        return elapsedMillis;
    }
}
