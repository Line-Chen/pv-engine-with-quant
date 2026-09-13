package com.cmb.pvengine.integration.application;

import java.nio.charset.StandardCharsets;

import org.springframework.stereotype.Component;

import com.cmb.pvengine.integration.config.QuantSdkProperties;
import com.cmb.pvengine.integration.engine.InvalidEngineInputException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * 外部 JSON 入参的长度与结构校验。不记录原始载荷。
 */
@Component
public class JsonPayloadSupport {

    private final ObjectMapper objectMapper;

    private final QuantSdkProperties properties;

    public JsonPayloadSupport(ObjectMapper objectMapper, QuantSdkProperties properties) {
        this.objectMapper = objectMapper;
        this.properties = properties;
    }

    /**
     * init 切片允许空白，表示按文档清空该切片缓存。
     */
    public String normalizeInitJson(String raw) {
        if (raw == null) {
            return "";
        }
        assertSize(raw);
        String trimmed = raw.trim();
        if (trimmed.isEmpty()) {
            return "";
        }
        assertJsonObject(trimmed);
        return trimmed;
    }

    public String requireJsonObject(String raw) {
        if (raw == null || raw.trim().isEmpty()) {
            throw new InvalidEngineInputException("请求体不能为空");
        }
        assertSize(raw);
        String trimmed = raw.trim();
        assertJsonObject(trimmed);
        return trimmed;
    }

    public String writeObject(JsonNode node, String fieldName) {
        if (node == null || node.isNull()) {
            return null;
        }
        if (!node.isObject()) {
            throw new InvalidEngineInputException(fieldName + " 必须是 JSON 对象");
        }
        try {
            String json = objectMapper.writeValueAsString(node);
            assertSize(json);
            return json;
        } catch (InvalidEngineInputException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new InvalidEngineInputException(fieldName + " 无法序列化", ex);
        }
    }

    private void assertSize(String raw) {
        int bytes = raw.getBytes(StandardCharsets.UTF_8).length;
        if (bytes > properties.getMaxPayloadBytes()) {
            throw new InvalidEngineInputException("请求体超过最大允许长度");
        }
    }

    private void assertJsonObject(String json) {
        try {
            JsonNode node = objectMapper.readTree(json);
            if (node == null || !node.isObject()) {
                throw new InvalidEngineInputException("请求体必须是 JSON 对象");
            }
        } catch (InvalidEngineInputException ex) {
            throw ex;
        } catch (Exception ex) {
            throw new InvalidEngineInputException("请求体不是合法 JSON", ex);
        }
    }
}
