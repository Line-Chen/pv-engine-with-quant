package com.cmb.pvengine.integration.engine;

import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

import javax.annotation.PreDestroy;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.cmb.pvengine.CmbPREngine;
import com.cmb.pvengine.integration.application.command.WorkflowParseMode;
import com.cmb.pvengine.integration.config.QuantSdkProperties;
import com.cmb.pvengine.model.enumeration.EngineSessionStateEnum;
import com.cmb.pvengine.model.result.InitConfigStatus;
import com.cmb.pvengine.model.result.InitResult;
import com.cmb.pvengine.model.result.WorkflowResult;
import com.cmb.pvengine.task.Workflow;

/**
 * 进程内单例引擎适配器。文档约束：同实例禁止并发 run。
 */
public class CmbQuantEngineGateway implements QuantEngineGateway {

    private static final Logger LOGGER = LoggerFactory.getLogger(CmbQuantEngineGateway.class);

    private final CmbPREngine engine;

    private final QuantSdkProperties properties;

    private final ReentrantLock lock = new ReentrantLock();

    public CmbQuantEngineGateway(CmbPREngine engine, QuantSdkProperties properties) {
        if (engine == null) {
            throw new IllegalArgumentException("engine 不能为空");
        }
        if (properties == null) {
            throw new IllegalArgumentException("properties 不能为空");
        }
        this.engine = engine;
        this.properties = properties;
    }

    @Override
    public InitResult initBuildRecipe(String json) {
        return executeLocked("initBuildRecipe", new EngineAction<InitResult>() {
            @Override
            public InitResult run() {
                return engine.initBuildRecipe(json);
            }
        });
    }

    @Override
    public InitResult initCalendar(String json) {
        return executeLocked("initCalendar", new EngineAction<InitResult>() {
            @Override
            public InitResult run() {
                return engine.initCalendar(json);
            }
        });
    }

    @Override
    public InitResult initConventions(String json) {
        return executeLocked("initConventions", new EngineAction<InitResult>() {
            @Override
            public InitResult run() {
                return engine.initConventions(json);
            }
        });
    }

    @Override
    public void initFinished() {
        executeLocked("initFinished", new EngineAction<Void>() {
            @Override
            public Void run() {
                engine.initFinished();
                return null;
            }
        });
    }

    @Override
    public void resetInit() {
        executeLocked("resetInit", new EngineAction<Void>() {
            @Override
            public Void run() {
                engine.resetInit();
                return null;
            }
        });
    }

    @Override
    public List<InitConfigStatus> initStatus() {
        return executeLocked("initStatus", new EngineAction<List<InitConfigStatus>>() {
            @Override
            public List<InitConfigStatus> run() {
                return engine.initStatus();
            }
        });
    }

    @Override
    public EngineSessionStateEnum sessionState() {
        return executeLocked("sessionState", new EngineAction<EngineSessionStateEnum>() {
            @Override
            public EngineSessionStateEnum run() {
                return engine.sessionState();
            }
        });
    }

    @Override
    public Workflow parseTask(String taskJson) {
        return Workflow.fromTask(taskJson);
    }

    @Override
    public Workflow parseWorkflow(String workflowJson) {
        return Workflow.fromJson(workflowJson);
    }

    @Override
    public WorkflowResult runTask(String taskJson) {
        return executeLocked("runTask", new EngineAction<WorkflowResult>() {
            @Override
            public WorkflowResult run() {
                return engine.run(Workflow.fromTask(taskJson));
            }
        });
    }

    @Override
    public WorkflowResult runWorkflow(String workflowJson) {
        return executeLocked("runWorkflow", new EngineAction<WorkflowResult>() {
            @Override
            public WorkflowResult run() {
                return engine.run(Workflow.fromJson(workflowJson));
            }
        });
    }

    @Override
    public OneShotEngineResult executeOneShot(final OneShotPayload payload) {
        if (payload == null) {
            throw new InvalidEngineInputException("oneshot 载荷不能为空");
        }
        return executeLocked("executeOneShot", new EngineAction<OneShotEngineResult>() {
            @Override
            public OneShotEngineResult run() {
                return doOneShot(payload);
            }
        });
    }

    @PreDestroy
    public void destroy() {
        lock.lock();
        try {
            engine.close();
        } finally {
            lock.unlock();
        }
    }

    private OneShotEngineResult doOneShot(OneShotPayload payload) {
        if (payload.isResetBeforeInit()) {
            engine.resetInit();
        }
        InitResult recipeResult = null;
        if (payload.getBuildRecipeJson() != null) {
            recipeResult = engine.initBuildRecipe(payload.getBuildRecipeJson());
        }
        InitResult calendarResult = null;
        if (payload.getCalendarJson() != null) {
            calendarResult = engine.initCalendar(payload.getCalendarJson());
        }
        InitResult conventionResult = null;
        if (payload.getConventionsJson() != null) {
            conventionResult = engine.initConventions(payload.getConventionsJson());
        }
        engine.initFinished();
        Workflow workflow = resolveWorkflow(payload);
        WorkflowResult workflowResult = engine.run(workflow);
        return new OneShotEngineResult(recipeResult, calendarResult, conventionResult, workflowResult);
    }

    private Workflow resolveWorkflow(OneShotPayload payload) {
        if (payload.getParseMode() == WorkflowParseMode.WORKFLOW) {
            return Workflow.fromJson(payload.getPayloadJson());
        }
        return Workflow.fromTask(payload.getPayloadJson());
    }

    private <T> T executeLocked(String action, EngineAction<T> engineAction) {
        boolean acquired = false;
        try {
            acquired = lock.tryLock(properties.getLockTimeoutMs(), TimeUnit.MILLISECONDS);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new EngineBusyException("等待引擎锁被中断: " + action);
        }
        if (!acquired) {
            throw new EngineBusyException("引擎忙碌，请稍后重试: " + action);
        }
        try {
            LOGGER.info("QUANT SDK 动作开始, action={}", action);
            return engineAction.run();
        } finally {
            lock.unlock();
        }
    }

    /**
     * 引擎动作回调，避免 Java 8 下在锁内写过多重复代码。
     */
    private interface EngineAction<T> {

        T run();
    }
}
