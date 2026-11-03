/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.gridlib.config.Config
 *  com.strategyquant.gridlib.config.SingleFolderConfig
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.memory.CpuInfo
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.performance;

import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.gridlib.config.Config;
import com.strategyquant.gridlib.config.SingleFolderConfig;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.memory.CpuInfo;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Performance {
    private static final Logger LOGGER = LoggerFactory.getLogger(Performance.class);
    public static int totalCores = 2;
    public static final String CORE_USAGE_SINGLE = "1";
    public static final String CORE_USAGE_RES1CORE = "-1";
    public static final String CORE_USAGE_MAXPERF = "100%";
    public static final String CORE_USAGE_CUSTOM = "X";
    public static final String benchmarkTimePerTickKey = "BenchmarkTimePerTick";
    public static double benchmarkTimePerTick = 0.0;

    public static void init() throws Exception {
        totalCores = CpuInfo.getAvailableProcessors();
        SQGrid.init((Config)Performance.createGridConfig());
        benchmarkTimePerTick = Double.parseDouble(MainApp.settings().get(benchmarkTimePerTickKey, "0"));
    }

    public static JSONObject getCoreUsageOptions() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("singleCore", (Object)CORE_USAGE_SINGLE);
        jSONObject.put("reserve1Core", (Object)CORE_USAGE_RES1CORE);
        jSONObject.put("maxPerformance", (Object)CORE_USAGE_MAXPERF);
        jSONObject.put("customCores", (Object)CORE_USAGE_CUSTOM);
        return jSONObject;
    }

    public static boolean isCustomCoreUsage(String string) {
        if (string.equals(CORE_USAGE_SINGLE) || string.equals(CORE_USAGE_RES1CORE) || string.equals(CORE_USAGE_MAXPERF)) {
            return false;
        }
        try {
            Integer.parseInt(string);
            return true;
        }
        catch (Exception exception) {
            return false;
        }
    }

    private static Config createGridConfig() {
        Config config = new Config(null);
        config.setFinishedJobsInDesc(100);
        config.setUseAffinity(MainApp.settings().getBoolean("threadAffinity", false));
        String string = MainApp.settings().get("coreUsage", CORE_USAGE_RES1CORE);
        config.setCoreUsage(string.startsWith(CORE_USAGE_CUSTOM) ? string.replaceAll("\\D+", "") : string);
        boolean bl = MainApp.settings().getBoolean("highPriority", false);
        LOGGER.info("High priority: " + (bl ? "ON" : "OFF"));
        config.setAdjustTopSizeOfCores(bl);
        config.getFolderConfigs().setDataFolderRoot(MainApp.getDataPath());
        config.getFolderConfigs().getFolderConfig().add(new SingleFolderConfig("internal/libs", false));
        config.getFolderConfigs().getFolderConfig().add(new SingleFolderConfig("data", false));
        config.getFolderConfigs().getFolderConfig().add(new SingleFolderConfig("extends", true));
        config.setFoldersWithJars(new String[]{MainApp.getDataPath() + "internal/libs", MainApp.getDataPath() + "internal/plugins/ProjectBuilder", MainApp.getDataPath() + "internal/plugins/ProjectRetester", MainApp.getDataPath() + "internal/plugins"});
        return config;
    }
}

