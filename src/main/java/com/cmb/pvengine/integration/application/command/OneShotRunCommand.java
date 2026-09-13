package com.cmb.pvengine.integration.application.command;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonPOJOBuilder;

/**
 * 一次性完成 init + initFinished + run 的测试命令。
 */
@JsonDeserialize(builder = OneShotRunCommand.Builder.class)
public final class OneShotRunCommand {

    private final JsonNode buildRecipe;

    private final JsonNode calendar;

    private final JsonNode conventions;

    private final JsonNode payload;

    private final WorkflowParseMode parseMode;

    private final boolean resetBeforeInit;

    private OneShotRunCommand(Builder builder) {
        this.buildRecipe = builder.buildRecipe;
        this.calendar = builder.calendar;
        this.conventions = builder.conventions;
        this.payload = builder.payload;
        this.parseMode = builder.parseMode == null ? WorkflowParseMode.TASK : builder.parseMode;
        this.resetBeforeInit = builder.resetBeforeInit;
    }

    public JsonNode getBuildRecipe() {
        return buildRecipe;
    }

    public JsonNode getCalendar() {
        return calendar;
    }

    public JsonNode getConventions() {
        return conventions;
    }

    public JsonNode getPayload() {
        return payload;
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

    @JsonPOJOBuilder(withPrefix = "")
    public static final class Builder {

        private JsonNode buildRecipe;

        private JsonNode calendar;

        private JsonNode conventions;

        private JsonNode payload;

        private WorkflowParseMode parseMode = WorkflowParseMode.TASK;

        private boolean resetBeforeInit = true;

        public Builder buildRecipe(JsonNode buildRecipe) {
            this.buildRecipe = buildRecipe;
            return this;
        }

        public Builder calendar(JsonNode calendar) {
            this.calendar = calendar;
            return this;
        }

        public Builder conventions(JsonNode conventions) {
            this.conventions = conventions;
            return this;
        }

        public Builder payload(JsonNode payload) {
            this.payload = payload;
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

        public OneShotRunCommand build() {
            return new OneShotRunCommand(this);
        }
    }
}
