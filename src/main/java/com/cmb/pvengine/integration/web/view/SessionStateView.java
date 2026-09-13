package com.cmb.pvengine.integration.web.view;

/**
 * 引擎会话状态。
 */
public final class SessionStateView {

    private final String state;

    public SessionStateView(String state) {
        this.state = state;
    }

    public String getState() {
        return state;
    }
}
