package com.cmb.pvengine.integration.web.assembler;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.cmb.pvengine.integration.web.view.InitResultView;
import com.cmb.pvengine.integration.web.view.TaskResultView;
import com.cmb.pvengine.integration.web.view.WorkflowResultView;
import com.cmb.pvengine.model.enumeration.ErrorCodeEnum;
import com.cmb.pvengine.model.enumeration.InitSectionStatusEnum;
import com.cmb.pvengine.model.enumeration.InitSectionTypeEnum;
import com.cmb.pvengine.model.result.InitResult;
import com.cmb.pvengine.model.result.PREngineError;
import com.cmb.pvengine.model.result.ResultTable;
import com.cmb.pvengine.model.result.TaskResult;
import com.cmb.pvengine.model.result.WorkflowResult;
import com.cmb.pvengine.model.result.WorkflowSummary;

class QuantResultAssemblerTest {

    private final QuantResultAssembler assembler = new QuantResultAssembler();

    @Test
    void shouldMapInitResult() {
        InitResult result = new InitResult(InitSectionTypeEnum.BUILD_RECIPE,
                InitSectionStatusEnum.LOADED, "ok", "2026-09-13T00:00:00Z");
        InitResultView view = assembler.toInitResultView(result);
        assertEquals("BUILD_RECIPE", view.getSection());
        assertEquals("LOADED", view.getStatus());
        assertEquals("ok", view.getMessage());
    }

    @Test
    void shouldReturnNullWhenInitResultMissing() {
        assertNull(assembler.toInitResultView(null));
    }

    @Test
    void shouldMapWorkflowResultAndTaskError() {
        ResultTable table = new ResultTable(Arrays.asList("REQUEST_ID"),
                Collections.singletonList(Collections.singletonList("wf-1")));
        TaskResult success = TaskResult.success("t1", "BUILD_MODELS", table);
        PREngineError error = new PREngineError(ErrorCodeEnum.EMPTY_QUOTE_SET, "empty");
        TaskResult failed = TaskResult.failed("t2", "BUILD_MODELS", error);
        WorkflowSummary summary = new WorkflowSummary(2, 1, 1, 0, 12L);
        List<TaskResult> tasks = Arrays.asList(success, failed);
        WorkflowResult result = new WorkflowResult("wf-1", summary, tasks);

        WorkflowResultView view = assembler.toWorkflowResultView(result);
        assertEquals("wf-1", view.getWorkflowId());
        assertEquals(2, view.getSummary().getTotalTasks());
        assertEquals(2, view.getTasks().size());
        TaskResultView second = view.getTasks().get(1);
        assertEquals("EMPTY_QUOTE_SET", second.getError().getCode());
    }
}
