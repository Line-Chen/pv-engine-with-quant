package com.cmb.pvengine.integration.web.assembler;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.springframework.stereotype.Component;

import com.cmb.pvengine.integration.engine.OneShotEngineResult;
import com.cmb.pvengine.integration.web.view.EngineErrorView;
import com.cmb.pvengine.integration.web.view.InitConfigStatusView;
import com.cmb.pvengine.integration.web.view.InitResultView;
import com.cmb.pvengine.integration.web.view.OneShotResultView;
import com.cmb.pvengine.integration.web.view.ResultTableView;
import com.cmb.pvengine.integration.web.view.SessionStateView;
import com.cmb.pvengine.integration.web.view.TaskResultView;
import com.cmb.pvengine.integration.web.view.WorkflowParseView;
import com.cmb.pvengine.integration.web.view.WorkflowResultView;
import com.cmb.pvengine.integration.web.view.WorkflowSummaryView;
import com.cmb.pvengine.model.TaskInput;
import com.cmb.pvengine.model.enumeration.EngineSessionStateEnum;
import com.cmb.pvengine.model.result.InitConfigStatus;
import com.cmb.pvengine.model.result.InitResult;
import com.cmb.pvengine.model.result.PREngineError;
import com.cmb.pvengine.model.result.ResultTable;
import com.cmb.pvengine.model.result.TaskResult;
import com.cmb.pvengine.model.result.WorkflowResult;
import com.cmb.pvengine.model.result.WorkflowSummary;
import com.cmb.pvengine.task.Workflow;

/**
 * 将 SDK 值对象转换为可 JSON 序列化的视图。SDK 使用 workflowId() 等访问器，Jackson 默认无法识别。
 */
@Component
public class QuantResultAssembler {

    public InitResultView toInitResultView(InitResult result) {
        if (result == null) {
            return null;
        }
        String section = result.getSection() == null ? null : result.getSection().name();
        String status = result.getStatus() == null ? null : result.getStatus().name();
        return new InitResultView(section, status, result.getMessage(), result.getTimestamp());
    }

    public List<InitConfigStatusView> toInitStatusViews(List<InitConfigStatus> statuses) {
        if (statuses == null || statuses.isEmpty()) {
            return Collections.emptyList();
        }
        List<InitConfigStatusView> views = new ArrayList<InitConfigStatusView>(statuses.size());
        for (InitConfigStatus status : statuses) {
            views.add(toInitStatusView(status));
        }
        return views;
    }

    public SessionStateView toSessionStateView(EngineSessionStateEnum state) {
        String name = state == null ? null : state.name();
        return new SessionStateView(name);
    }

    public WorkflowParseView toParseView(Workflow workflow) {
        if (workflow == null) {
            throw new IllegalArgumentException("workflow 不能为空");
        }
        List<String> taskIds = new ArrayList<String>();
        List<TaskInput> tasks = workflow.tasks();
        if (tasks != null) {
            for (TaskInput task : tasks) {
                if (task != null) {
                    taskIds.add(task.id());
                }
            }
        }
        return new WorkflowParseView(workflow.workflowId(), taskIds, taskIds.size());
    }

    public WorkflowResultView toWorkflowResultView(WorkflowResult result) {
        if (result == null) {
            return null;
        }
        return new WorkflowResultView(result.workflowId(), toSummaryView(result.summary()),
                toTaskViews(result.tasks()));
    }

    public OneShotResultView toOneShotView(OneShotEngineResult result) {
        if (result == null) {
            return null;
        }
        return new OneShotResultView(
                toInitResultView(result.getBuildRecipe()),
                toInitResultView(result.getCalendar()),
                toInitResultView(result.getConventions()),
                toWorkflowResultView(result.getWorkflowResult()));
    }

    private InitConfigStatusView toInitStatusView(InitConfigStatus status) {
        if (status == null) {
            return null;
        }
        String section = status.getSection() == null ? null : status.getSection().name();
        String statusName = status.getStatus() == null ? null : status.getStatus().name();
        return new InitConfigStatusView(section, statusName, status.getMessage(),
                status.getLastReloadAt(), status.getEntryCount());
    }

    private WorkflowSummaryView toSummaryView(WorkflowSummary summary) {
        if (summary == null) {
            return null;
        }
        return new WorkflowSummaryView(summary.totalTasks(), summary.succeeded(),
                summary.failed(), summary.cancelled(), summary.elapsedMillis());
    }

    private List<TaskResultView> toTaskViews(List<TaskResult> tasks) {
        if (tasks == null || tasks.isEmpty()) {
            return Collections.emptyList();
        }
        List<TaskResultView> views = new ArrayList<TaskResultView>(tasks.size());
        for (TaskResult task : tasks) {
            views.add(toTaskView(task));
        }
        return views;
    }

    private TaskResultView toTaskView(TaskResult task) {
        if (task == null) {
            return null;
        }
        String status = task.status() == null ? null : task.status().name();
        return new TaskResultView(task.id(), task.type(), status, toTableView(task.resultTable()),
                toErrorView(task.error()), task.elapsedMillis());
    }

    private ResultTableView toTableView(ResultTable table) {
        if (table == null) {
            return null;
        }
        List<String> headers = table.headers() == null
                ? Collections.<String>emptyList() : table.headers();
        List<List<String>> data = table.data() == null
                ? Collections.<List<String>>emptyList() : table.data();
        return new ResultTableView(headers, data);
    }

    private EngineErrorView toErrorView(PREngineError error) {
        if (error == null) {
            return null;
        }
        String code = error.code() == null ? null : error.code().name();
        return new EngineErrorView(code, error.wireCode(), error.message(), error.detail());
    }
}
