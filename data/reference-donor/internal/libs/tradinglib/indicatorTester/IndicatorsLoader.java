/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.lib.snippets.CustomClassesLoader
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.indicatorTester;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.indicatorTester.CalibrationConfig;
import com.strategyquant.indicatorTester.CalibrationData;
import com.strategyquant.indicatorTester.IndicatorInfo;
import com.strategyquant.indicatorTester.IndyParameter;
import com.strategyquant.lib.snippets.CustomClassesLoader;
import com.strategyquant.tradinglib.BuildingBlock;
import com.strategyquant.tradinglib.Editor;
import com.strategyquant.tradinglib.IgnoreInBuilder;
import com.strategyquant.tradinglib.Output;
import com.strategyquant.tradinglib.Parameter;
import java.lang.reflect.Field;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class IndicatorsLoader {
    private static final Logger Log = LoggerFactory.getLogger(IndicatorsLoader.class);
    private static ArrayList<IndicatorInfo> indicators = new ArrayList();
    private static CustomClassesLoader loader;

    public static ArrayList<IndicatorInfo> getIndicators() {
        CalibrationConfig.load();
        IndicatorsLoader.loadAll();
        return indicators;
    }

    public static void loadAll() {
        indicators.clear();
        loader = new CustomClassesLoader("Blocks/Indicators");
        while (loader.hasNext()) {
            IndicatorInfo indicatorInfo = new IndicatorInfo();
            indicatorInfo.className = loader.getNext();
            String[] stringArray = indicatorInfo.className.split("\\.");
            indicatorInfo.simpleName = stringArray[stringArray.length - 1];
            try {
                Object object = loader.createInstance(indicatorInfo.className);
                indicatorInfo.returnType = 0;
                if (object.getClass().isAnnotationPresent(BuildingBlock.class)) {
                    Field[] fieldArray = object.getClass().getAnnotation(BuildingBlock.class);
                    indicatorInfo.returnType = fieldArray.returnType();
                    indicatorInfo.title = fieldArray.name();
                }
                if (object.getClass().isAnnotationPresent(IgnoreInBuilder.class) || indicatorInfo.className.endsWith("FixedPips")) {
                    indicatorInfo.ignored = true;
                }
                for (Field field : object.getClass().getDeclaredFields()) {
                    Object object2;
                    CalibrationData calibrationData = CalibrationConfig.getData(indicatorInfo.simpleName, field.getName());
                    if (field.isAnnotationPresent(Output.class)) {
                        if (calibrationData != null && calibrationData.disabled) continue;
                        object2 = field.getName();
                        indicatorInfo.outputBuffers.add((String)object2);
                        continue;
                    }
                    if (!field.isAnnotationPresent(Parameter.class)) continue;
                    object2 = new IndyParameter();
                    Parameter parameter = field.getAnnotation(Parameter.class);
                    ((IndyParameter)object2).name = field.getName();
                    ((IndyParameter)object2).className = field.getType().getSimpleName();
                    ((IndyParameter)object2).options = null;
                    try {
                        Editor editor = field.getAnnotation(Editor.class);
                        if (editor.type() == 40) {
                            ((IndyParameter)object2).options = editor.values();
                        }
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                    try {
                        ((IndyParameter)object2).defaultValue = parameter.defaultValue();
                        if (((IndyParameter)object2).defaultValue == null && ((IndyParameter)object2).className.equals(DataSeries.class.getSimpleName())) {
                            ((IndyParameter)object2).defaultValue = "Close";
                        }
                        if (((IndyParameter)object2).defaultValue == null) {
                            ((IndyParameter)object2).defaultValue = String.valueOf(field.get(object));
                        }
                    }
                    catch (Exception exception) {
                        ((IndyParameter)object2).defaultValue = null;
                        Log.error("Error getting default parameter of indicator '" + indicatorInfo.className + "'", (Throwable)exception);
                    }
                    if (calibrationData != null && calibrationData.values != null && !calibrationData.values.isEmpty()) {
                        ((IndyParameter)object2).calibrationValues = calibrationData.values;
                    }
                    indicatorInfo.parameters.add((IndyParameter)object2);
                }
                indicators.add(indicatorInfo);
            }
            catch (Exception exception) {
                Log.error("Cannot instantiate indicator '" + indicatorInfo.simpleName + "'", (Throwable)exception);
            }
        }
    }

    public static JSONArray toJSONArray() {
        JSONArray jSONArray = new JSONArray();
        for (IndicatorInfo indicatorInfo : IndicatorsLoader.getIndicators()) {
            for (JSONObject jSONObject : indicatorInfo.getJSONList()) {
                jSONArray.put((Object)jSONObject);
            }
        }
        return jSONArray;
    }

    public static String correctIndyName(String string) {
        return string.split("\\.")[0];
    }

    public static String getBufferName(String string) {
        if (string.contains(".")) {
            String[] stringArray = string.split("\\.");
            return stringArray[stringArray.length - 1];
        }
        return "Value";
    }

    public static IndicatorInfo getIndyByName(String string) {
        String string2 = IndicatorsLoader.correctIndyName(string);
        for (IndicatorInfo indicatorInfo : IndicatorsLoader.getIndicators()) {
            if (!indicatorInfo.simpleName.equals(string2)) continue;
            return indicatorInfo;
        }
        return null;
    }
}

