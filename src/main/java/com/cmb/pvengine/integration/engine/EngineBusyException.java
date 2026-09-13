package com.cmb.pvengine.integration.engine;

/**
 * 同一 CmbPREngine 实例正在执行，拒绝并发 run/init。
 */
public class EngineBusyException extends RuntimeException {

    public EngineBusyException(String message) {
        super(message);
    }
}
