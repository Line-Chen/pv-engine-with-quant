package com.cmb.pvengine.integration.config;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import com.cmb.pvengine.CmbPREngine;
import com.cmb.pvengine.integration.engine.CmbQuantEngineGateway;
import com.cmb.pvengine.integration.engine.QuantEngineGateway;

/**
 * 初始化内核运行目录并装配引擎网关。
 */
@Configuration
public class QuantSdkConfiguration {

    private static final Logger LOGGER = LoggerFactory.getLogger(QuantSdkConfiguration.class);

    private static final String CMB_HOME_KEY = "CMB_HOME";

    private static final String CMB_DATA_KEY = "CMB_DATA";

    @Bean
    public QuantEngineGateway quantEngineGateway(QuantSdkProperties properties) {
        Path home = prepareCmbHome(properties.getCmbHome());
        System.setProperty(CMB_HOME_KEY, home.toString());
        System.setProperty(CMB_DATA_KEY, home.toString());
        LOGGER.info("QUANT SDK 运行目录已就绪, cmbHomeLength={}", home.toString().length());
        CmbPREngine engine = new CmbPREngine();
        return new CmbQuantEngineGateway(engine, properties);
    }

    /**
     * 创建可写运行目录；路径来自本地配置，不接受 HTTP 入参。
     */
    private Path prepareCmbHome(String configuredHome) {
        if (configuredHome == null || configuredHome.trim().isEmpty()) {
            throw new IllegalStateException("quant.sdk.cmb-home 不能为空");
        }
        Path home = Paths.get(configuredHome).toAbsolutePath().normalize();
        try {
            Files.createDirectories(home);
        } catch (IOException ex) {
            throw new IllegalStateException("无法创建 CMB_HOME 目录", ex);
        }
        return home;
    }
}
