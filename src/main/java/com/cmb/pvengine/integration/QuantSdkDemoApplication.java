package com.cmb.pvengine.integration;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

import com.cmb.pvengine.integration.config.QuantSdkProperties;

/**
 * QUANT SDK Spring 集成 Demo 启动类。
 */
@SpringBootApplication
@EnableConfigurationProperties(QuantSdkProperties.class)
public class QuantSdkDemoApplication {

    public static void main(String[] args) {
        SpringApplication.run(QuantSdkDemoApplication.class, args);
    }
}
