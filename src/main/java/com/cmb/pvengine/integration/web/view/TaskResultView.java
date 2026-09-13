package com.cmb.pvengine.integration.web.view;

/**
 * 单任务执行结果。
 */
public final class TaskResultView {

    private final String id;

    private final String type;

    private final String status;

    private final ResultTableView resultTable;

    private final EngineErrorView error;

    private final long elapsedMillis;

    public TaskResultView(String id, String type, String status,
            ResultTableView resultTable, EngineErrorView error, long elapsedMillis) {
        this.id = id;
        this.type = type;
        this.status = status;
        this.resultTable = resultTable;
        this.error = error;
        this.elapsedMillis = elapsedMillis;
    }

    public String getId() {
        return id;
    }

    public String getType() {
        return type;
    }

    public String getStatus() {
        return status;
    }

    public ResultTableView getResultTable() {
        return resultTable;
    }

    public EngineErrorView getError() {
        return error;
    }

    public long getElapsedMillis() {
        return elapsedMillis;
    }
}
