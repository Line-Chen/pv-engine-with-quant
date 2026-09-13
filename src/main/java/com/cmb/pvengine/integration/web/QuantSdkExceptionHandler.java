package com.cmb.pvengine.integration.web;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import com.cmb.pvengine.exception.AbstractPREngineException;
import com.cmb.pvengine.integration.engine.EngineBusyException;
import com.cmb.pvengine.integration.engine.InvalidEngineInputException;
import com.cmb.pvengine.integration.web.view.ApiResponse;
import com.cmb.pvengine.integration.web.view.EngineErrorView;
import com.cmb.pvengine.model.result.PREngineError;

/**
 * 将 SDK 生命周期异常与入参异常映射为 HTTP 状态，不回传堆栈。
 */
@RestControllerAdvice
public class QuantSdkExceptionHandler {

    private static final Logger LOGGER = LoggerFactory.getLogger(QuantSdkExceptionHandler.class);

    @ExceptionHandler(InvalidEngineInputException.class)
    public ResponseEntity<ApiResponse<Void>> handleInvalidInput(InvalidEngineInputException ex) {
        LOGGER.warn("入参校验失败, reasonLength={}", safeLength(ex.getMessage()));
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.<Void>fail("INVALID_INPUT", ex.getMessage(), null));
    }

    @ExceptionHandler(EngineBusyException.class)
    public ResponseEntity<ApiResponse<Void>> handleBusy(EngineBusyException ex) {
        LOGGER.warn("引擎忙碌");
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(ApiResponse.<Void>fail("ENGINE_BUSY", ex.getMessage(), null));
    }

    @ExceptionHandler(AbstractPREngineException.class)
    public ResponseEntity<ApiResponse<EngineErrorView>> handleEngine(AbstractPREngineException ex) {
        PREngineError error = ex.error();
        String code = error == null || error.code() == null ? "UNKNOWN" : error.code().name();
        String message = error == null ? ex.getMessage() : error.message();
        EngineErrorView view = toErrorView(error);
        LOGGER.warn("SDK 结构化异常, code={}", code);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.fail(code, message, view));
    }

    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<ApiResponse<Void>> handleIllegalState(IllegalStateException ex) {
        LOGGER.warn("引擎生命周期冲突, reasonLength={}", safeLength(ex.getMessage()));
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(ApiResponse.<Void>fail("ILLEGAL_STATE", ex.getMessage(), null));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ApiResponse<Void>> handleIllegalArgument(IllegalArgumentException ex) {
        LOGGER.warn("SDK 参数非法, reasonLength={}", safeLength(ex.getMessage()));
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.<Void>fail("ILLEGAL_ARGUMENT", ex.getMessage(), null));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleUnknown(Exception ex) {
        LOGGER.error("未分类异常, type={}", ex.getClass().getSimpleName());
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.<Void>fail("INTERNAL_ERROR", "服务内部错误", null));
    }

    private EngineErrorView toErrorView(PREngineError error) {
        if (error == null) {
            return null;
        }
        String code = error.code() == null ? null : error.code().name();
        return new EngineErrorView(code, error.wireCode(), error.message(), error.detail());
    }

    private int safeLength(String text) {
        return text == null ? 0 : text.length();
    }
}
