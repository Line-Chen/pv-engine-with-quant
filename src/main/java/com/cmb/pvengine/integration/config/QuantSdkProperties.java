package com.cmb.pvengine.integration.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * QUANT SDK 运行参数。
 */
@ConfigurationProperties(prefix = "quant.sdk")
public class QuantSdkProperties {

    /**
     * 内核 CMB_HOME / CMB_DATA 目录，需可写。
     */
    private String cmbHome = "runtime/cmb-home";

    /**
     * 同一引擎实例互斥锁等待超时。
     */
    private long lockTimeoutMs = 30000L;

    /**
     * HTTP 传入 JSON 最大字节数，防止超大载荷压垮进程。
     */
    private int maxPayloadBytes = 2097152;

    public String getCmbHome() {
        return cmbHome;
    }

    public void setCmbHome(String cmbHome) {
        this.cmbHome = cmbHome;
    }

    public long getLockTimeoutMs() {
        return lockTimeoutMs;
    }

    public void setLockTimeoutMs(long lockTimeoutMs) {
        this.lockTimeoutMs = lockTimeoutMs;
    }

    public int getMaxPayloadBytes() {
        return maxPayloadBytes;
    }

    public void setMaxPayloadBytes(int maxPayloadBytes) {
        this.maxPayloadBytes = maxPayloadBytes;
    }
}
