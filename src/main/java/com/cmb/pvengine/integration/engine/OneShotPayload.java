package com.cmb.pvengine.integration.engine;

import com.cmb.pvengine.integration.application.command.WorkflowParseMode;

/**
 * 一次性执行所需的已校验 JSON 文本。
 */
public final class OneShotPayload {

    private final String buildRecipeJson;

    private final String calendarJson;

    private final String conventionsJson;

    private final String payloadJson;

    private final WorkflowParseMode parseMode;

    private final boolean resetBeforeInit;

    private OneShotPayload(Builder builder) {
        this.buildRecipeJson = builder.buildRecipeJson;
        this.calendarJson = builder.calendarJson;
        this.conventionsJson = builder.conventionsJson;
        this.payloadJson = builder.payloadJson;
        this.parseMode = builder.parseMode;
        this.resetBeforeInit = builder.resetBeforeInit;
    }

    public String getBuildRecipeJson() {
        return buildRecipeJson;
    }

    public String getCalendarJson() {
        return calendarJson;
    }

    public String getConventionsJson() {
        return conventionsJson;
    }

    public String getPayloadJson() {
        return payloadJson;
    }

    public WorkflowParseMode getParseMode() {
        return parseMode;
    }

    public boolean isResetBeforeInit() {
        return resetBeforeInit;
    }

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {

        private String buildRecipeJson;

        private String calendarJson;

        private String conventionsJson;

        private String payloadJson;

        private WorkflowParseMode parseMode;

        private boolean resetBeforeInit;

        public Builder buildRecipeJson(String buildRecipeJson) {
            this.buildRecipeJson = buildRecipeJson;
            return this;
        }

        public Builder calendarJson(String calendarJson) {
            this.calendarJson = calendarJson;
            return this;
        }

        public Builder conventionsJson(String conventionsJson) {
            this.conventionsJson = conventionsJson;
            return this;
        }

        public Builder payloadJson(String payloadJson) {
            this.payloadJson = payloadJson;
            return this;
        }

        public Builder parseMode(WorkflowParseMode parseMode) {
            this.parseMode = parseMode;
            return this;
        }

        public Builder resetBeforeInit(boolean resetBeforeInit) {
            this.resetBeforeInit = resetBeforeInit;
            return this;
        }

        public OneShotPayload build() {
            return new OneShotPayload(this);
        }
    }
}
