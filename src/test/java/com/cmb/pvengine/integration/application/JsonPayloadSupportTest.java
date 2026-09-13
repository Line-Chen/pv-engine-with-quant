package com.cmb.pvengine.integration.application;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import com.cmb.pvengine.integration.config.QuantSdkProperties;
import com.cmb.pvengine.integration.engine.InvalidEngineInputException;
import com.fasterxml.jackson.databind.ObjectMapper;

class JsonPayloadSupportTest {

    private JsonPayloadSupport support;

    @BeforeEach
    void setUp() {
        QuantSdkProperties properties = new QuantSdkProperties();
        properties.setMaxPayloadBytes(64);
        support = new JsonPayloadSupport(new ObjectMapper(), properties);
    }

    @Test
    void shouldAllowBlankInitJson() {
        assertEquals("", support.normalizeInitJson("   "));
    }

    @Test
    void shouldRejectNonObject() {
        assertThrows(InvalidEngineInputException.class, new org.junit.jupiter.api.function.Executable() {
            @Override
            public void execute() {
                support.requireJsonObject("[1,2]");
            }
        });
    }

    @Test
    void shouldRejectOversizedPayload() {
        StringBuilder builder = new StringBuilder("{\"k\":\"");
        for (int i = 0; i < 80; i++) {
            builder.append('x');
        }
        builder.append("\"}");
        final String oversized = builder.toString();
        assertThrows(InvalidEngineInputException.class, new org.junit.jupiter.api.function.Executable() {
            @Override
            public void execute() {
                support.requireJsonObject(oversized);
            }
        });
    }
}
