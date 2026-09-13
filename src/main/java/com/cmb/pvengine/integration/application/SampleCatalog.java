package com.cmb.pvengine.integration.application;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;
import org.springframework.util.StreamUtils;

import com.cmb.pvengine.integration.engine.InvalidEngineInputException;

/**
 * 内置样例 JSON 白名单，禁止按用户路径读取文件。
 */
@Component
public class SampleCatalog {

    private static final Map<String, String> SAMPLES = new LinkedHashMap<String, String>();

    static {
        SAMPLES.put("init-build-recipe", "samples/init-build-recipe.json");
        SAMPLES.put("init-calendar", "samples/init-calendar.json");
        SAMPLES.put("init-conventions", "samples/init-conventions.json");
        SAMPLES.put("task-cny-fr007", "samples/task-cny-fr007.json");
        SAMPLES.put("oneshot-cny-fr007", "samples/oneshot-cny-fr007.json");
    }

    public List<String> names() {
        return Collections.unmodifiableList(Arrays.asList(SAMPLES.keySet().toArray(new String[0])));
    }

    public String load(String name) {
        if (name == null || !SAMPLES.containsKey(name)) {
            throw new InvalidEngineInputException("未知样例名");
        }
        String path = SAMPLES.get(name);
        ClassPathResource resource = new ClassPathResource(path);
        if (!resource.exists()) {
            throw new IllegalStateException("样例资源缺失");
        }
        try {
            InputStream inputStream = resource.getInputStream();
            try {
                return StreamUtils.copyToString(inputStream, StandardCharsets.UTF_8);
            } finally {
                inputStream.close();
            }
        } catch (Exception ex) {
            throw new IllegalStateException("读取样例失败", ex);
        }
    }
}
