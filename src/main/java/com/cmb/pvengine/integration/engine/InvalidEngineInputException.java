package com.cmb.pvengine.integration.engine;

/**
 * HTTP 入参未通过本地校验，尚未进入 SDK。
 */
public class InvalidEngineInputException extends RuntimeException {

    public InvalidEngineInputException(String message) {
        super(message);
    }

    public InvalidEngineInputException(String message, Throwable cause) {
        super(message, cause);
    }
}
