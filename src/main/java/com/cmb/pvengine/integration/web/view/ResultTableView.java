package com.cmb.pvengine.integration.web.view;

import java.util.List;

/**
 * 内存结果表。
 */
public final class ResultTableView {

    private final List<String> headers;

    private final List<List<String>> data;

    public ResultTableView(List<String> headers, List<List<String>> data) {
        this.headers = headers;
        this.data = data;
    }

    public List<String> getHeaders() {
        return headers;
    }

    public List<List<String>> getData() {
        return data;
    }
}
