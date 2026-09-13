package com.cmb.pvengine.integration.web.view;

/**
 * SDK 结构化错误。
 */
public final class EngineErrorView {

    private final String code;

    private final String wireCode;

    private final String message;

    private final String detail;

    public EngineErrorView(String code, String wireCode, String message, String detail) {
        this.code = code;
        this.wireCode = wireCode;
        this.message = message;
        this.detail = detail;
    }

    public String getCode() {
        return code;
    }

    public String getWireCode() {
        return wireCode;
    }

    public String getMessage() {
        return message;
    }

    public String getDetail() {
        return detail;
    }
}
