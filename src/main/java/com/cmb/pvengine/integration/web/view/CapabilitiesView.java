package com.cmb.pvengine.integration.web.view;

import java.util.List;

/**
 * 当前 jar 实际暴露的能力，与接口文档差异一并列出。
 */
public final class CapabilitiesView {

    private final String sdkApiVersion;

    private final List<String> supportedInitMethods;

    private final List<String> supportedTaskTypes;

    private final List<String> documentedButMissingInJar;

    public CapabilitiesView(String sdkApiVersion, List<String> supportedInitMethods,
            List<String> supportedTaskTypes, List<String> documentedButMissingInJar) {
        this.sdkApiVersion = sdkApiVersion;
        this.supportedInitMethods = supportedInitMethods;
        this.supportedTaskTypes = supportedTaskTypes;
        this.documentedButMissingInJar = documentedButMissingInJar;
    }

    public String getSdkApiVersion() {
        return sdkApiVersion;
    }

    public List<String> getSupportedInitMethods() {
        return supportedInitMethods;
    }

    public List<String> getSupportedTaskTypes() {
        return supportedTaskTypes;
    }

    public List<String> getDocumentedButMissingInJar() {
        return documentedButMissingInJar;
    }
}
