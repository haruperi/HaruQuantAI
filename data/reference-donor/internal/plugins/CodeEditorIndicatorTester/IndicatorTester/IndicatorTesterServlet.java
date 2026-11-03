/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.indicatorTester.CalibrationInfo
 *  com.strategyquant.indicatorTester.CalibrationRangesInfo
 *  com.strategyquant.indicatorTester.IndicatorCalibrator
 *  com.strategyquant.indicatorTester.IndicatorInfo
 *  com.strategyquant.indicatorTester.IndicatorTesterConfig
 *  com.strategyquant.indicatorTester.IndicatorsLoader
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.simulator.Engines
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.CodeEditor.impl.IndicatorTester;

import com.strategyquant.indicatorTester.CalibrationInfo;
import com.strategyquant.indicatorTester.CalibrationRangesInfo;
import com.strategyquant.indicatorTester.IndicatorCalibrator;
import com.strategyquant.indicatorTester.IndicatorInfo;
import com.strategyquant.indicatorTester.IndicatorTesterConfig;
import com.strategyquant.indicatorTester.IndicatorsLoader;
import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.DownloadProgressPublisher;
import com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.IndicatorTestExecutor;
import com.strategyquant.plugin.CodeEditor.impl.IndicatorTester.IndicatorTestsDownloader;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.simulator.Engines;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.ArrayList;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class IndicatorTesterServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(IndicatorTesterServlet.class);
    private static IndicatorTesterServlet instance;

    public IndicatorTesterServlet() {
        instance = this;
    }

    public static IndicatorTesterServlet getInstance() {
        return instance;
    }

    protected String execute(String command, Map<String, String[]> args, String method) {
        switch (command) {
            case "listIndicators": {
                return this.onListIndicators();
            }
            case "createNewConfig": {
                return this.onCreateNewConfig(args);
            }
            case "addTests": {
                return this.onAddTests(args);
            }
            case "loadConfig": {
                return this.onLoadConfig(args);
            }
            case "saveConfig": {
                return this.onSaveConfig(args);
            }
            case "startTesting": {
                return this.onStartTesting(args);
            }
            case "stopTesting": {
                return this.onStopTesting();
            }
            case "downloadTests": {
                return this.onDownloadTests();
            }
            case "calibrate": {
                return this.onCalibrate(args);
            }
        }
        return IndicatorTesterServlet.apiErrorJSON((String)L.t((String)"Execution failed. Unknown command '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onListIndicators() {
        JSONObject response = new JSONObject();
        JSONArray indicators = new JSONArray();
        for (IndicatorInfo indy : IndicatorsLoader.getIndicators()) {
            for (JSONObject indyObj : indy.getJSONList()) {
                indicators.put((Object)indyObj);
            }
        }
        response.put("indicators", (Object)indicators);
        response.put("success", (Object)L.t((String)"Indicators listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCreateNewConfig(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String engine = this.tryGetParam(args, "engine")[0];
            String barsToReserve = this.tryGetParam(args, "barsToReserve")[0];
            IndicatorTesterConfig.resetConfigPath();
            response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)IndicatorTesterConfig.createDefaultConfig((String)engine, (String)barsToReserve)));
        }
        catch (Exception e) {
            return IndicatorTesterServlet.apiErrorJSON((String)L.t((String)"Adding tests failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Tests added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onAddTests(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String[] indicators = this.tryGetParam(args, "indicators")[0].split(",");
            String xmlConfig = this.tryGetParam(args, "xmlConfig")[0];
            IndicatorTesterConfig.updateConfig((Element)XMLUtil.stringToElement((String)xmlConfig));
            response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)IndicatorTesterConfig.createNewConfig((String[])indicators)));
        }
        catch (Exception e) {
            return IndicatorTesterServlet.apiErrorJSON((String)L.t((String)"Adding tests failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Tests added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoadConfig(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        String filePath = null;
        try {
            filePath = this.tryGetParam(args, "filePath")[0];
        }
        catch (Exception exception) {
            // empty catch block
        }
        response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)IndicatorTesterConfig.load(filePath)));
        response.put("success", (Object)L.t((String)"Config loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSaveConfig(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String xmlConfig = this.tryGetParam(args, "xmlConfig")[0];
            String filePath = null;
            try {
                filePath = this.tryGetParam(args, "filePath")[0];
            }
            catch (Exception exception) {
                // empty catch block
            }
            IndicatorTesterConfig.save((Element)XMLUtil.stringToElement((String)xmlConfig), filePath);
        }
        catch (Exception e) {
            return IndicatorTesterServlet.apiErrorJSON((String)L.t((String)"Adding tests failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Config saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onStartTesting(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String xmlConfig = this.tryGetParam(args, "xmlConfig")[0];
            IndicatorTesterConfig.updateConfig((Element)XMLUtil.stringToElement((String)xmlConfig));
            IndicatorTestExecutor.get().start();
        }
        catch (Exception e) {
            return IndicatorTesterServlet.apiErrorJSON((String)e.getMessage(), null);
        }
        response.put("success", (Object)L.t((String)"Config loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onStopTesting() {
        JSONObject response = new JSONObject();
        IndicatorTestExecutor.get().stop();
        response.put("success", (Object)L.t((String)"Config loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onDownloadTests() {
        JSONObject response = new JSONObject();
        try {
            if (IndicatorTestExecutor.get().getRunningStatus() == 1) {
                throw new Exception("Indicator tests are running.<br>Please wait until the tests finish or stop the execution and try again.");
            }
            IndicatorTestsDownloader.downloadTests(DownloadProgressPublisher.get());
        }
        catch (Exception e) {
            return IndicatorTesterServlet.apiErrorJSON((String)L.t((String)"Cannot start indicator tests download.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Download started.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCalibrate(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParamValue(args, "projectName");
            String taskName = null;
            try {
                taskName = this.tryGetParamValue(args, "taskName");
            }
            catch (Exception exception) {
                // empty catch block
            }
            String symbolsStr = this.tryGetParamValue(args, "symbols");
            String timeframesStr = this.tryGetParamValue(args, "timeframes");
            String[] symbols = symbolsStr.split(",");
            String[] timeframes = timeframesStr.split(",");
            int engine = Engines.getEngine((String)this.tryGetParamValue(args, "engine"));
            if (engine == 1316847364 || engine == -1816889229) {
                throw new Exception(L.t((String)"Indicator calibration is not supported for AlgoCloud Stockpicker / Single-asset engine.", (Object[])new Object[0]));
            }
            try {
                CalibrationRangesInfo.maxSteps = Integer.parseInt(this.tryGetParamValue(args, "maxSteps"));
            }
            catch (Exception e) {
                CalibrationRangesInfo.maxSteps = -1;
            }
            String logInfo = taskName != null ? L.t((String)"Starting indicators calibration for task %s...", (Object[])new Object[]{taskName}) : L.t((String)"Starting indicators calibration...", (Object[])new Object[0]);
            ProgressEngine progressEngine = ProjectEngine.get((String)projectName).progressEngine;
            progressEngine.printToLog(logInfo);
            IndicatorCalibrator calibrator = new IndicatorCalibrator();
            ArrayList results = calibrator.calibrate(symbols, timeframes, engine);
            JSONArray calibrationResults = new JSONArray();
            for (int a = 0; a < results.size(); ++a) {
                CalibrationInfo result = (CalibrationInfo)results.get(a);
                calibrationResults.put((Object)result.toJSON());
            }
            progressEngine.printToLog(L.t((String)"Indicators calibration done", (Object[])new Object[0]));
            response.put("calibrationResults", (Object)calibrationResults);
        }
        catch (Exception e) {
            return IndicatorTesterServlet.apiErrorJSON((String)L.t((String)"Cannot start calibration", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Calibration finished.", (Object[])new Object[0]));
        return response.toString();
    }
}

