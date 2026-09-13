package com.cmb.pvengine.integration.web.view;

/**
 * initXxx 装载结果视图。
 */
public final class InitResultView {

    private final String section;

    private final String status;

    private final String message;

    private final String timestamp;

    public InitResultView(String section, String status, String message, String timestamp) {
        this.section = section;
        this.status = status;
        this.message = message;
        this.timestamp = timestamp;
    }

    public String getSection() {
        return section;
    }

    public String getStatus() {
        return status;
    }

    public String getMessage() {
        return message;
    }

    public String getTimestamp() {
        return timestamp;
    }
}
