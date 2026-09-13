package com.cmb.pvengine.integration.web.view;

/**
 * initStatus 单项快照。
 */
public final class InitConfigStatusView {

    private final String section;

    private final String status;

    private final String message;

    private final String lastReloadAt;

    private final int entryCount;

    public InitConfigStatusView(String section, String status, String message,
            String lastReloadAt, int entryCount) {
        this.section = section;
        this.status = status;
        this.message = message;
        this.lastReloadAt = lastReloadAt;
        this.entryCount = entryCount;
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

    public String getLastReloadAt() {
        return lastReloadAt;
    }

    public int getEntryCount() {
        return entryCount;
    }
}
