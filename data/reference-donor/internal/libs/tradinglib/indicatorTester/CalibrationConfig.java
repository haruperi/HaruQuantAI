/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.constants.SQPaths
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.indicatorTester;

import com.strategyquant.indicatorTester.CalibrationData;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.constants.SQPaths;
import java.util.ArrayList;
import java.util.HashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CalibrationConfig {
    private static final Logger Log = LoggerFactory.getLogger(CalibrationConfig.class);
    private static final String configFilePath = SQPaths.settingsDirPath + "/calibrationSettings.txt";
    private static HashMap<String, CalibrationData> map = new HashMap();
    public static boolean disableRounding = false;

    public static void load() {
        map.clear();
        disableRounding = false;
        ArrayList arrayList = new ArrayList();
        try {
            SQUtils.fileToArrayList(arrayList, (String)configFilePath, (String)"\n");
            for (int i = 0; i < arrayList.size(); ++i) {
                String string = ((String)arrayList.get(i)).trim();
                if (string.startsWith("#") || string.isEmpty() || !string.contains("=")) continue;
                try {
                    String[] stringArray = string.split("=");
                    if (stringArray.length != 2) {
                        throw new Exception(L.t((String)"Invalid syntax", (Object[])new Object[0]));
                    }
                    String string2 = stringArray[0];
                    String string3 = stringArray[1];
                    if (string2.equals("rounding")) {
                        disableRounding = string3.equals("disabled");
                        continue;
                    }
                    if (string3.contains(",")) {
                        map.put(string2, new CalibrationData(string3));
                        continue;
                    }
                    map.put(string2, new CalibrationData(string3.equals("disabled")));
                    continue;
                }
                catch (Exception exception) {
                    Log.error("Error while parsing line '" + string + "'", (Throwable)exception);
                }
            }
        }
        catch (Exception exception) {
            Log.error("Error while loading calibration settings", (Throwable)exception);
        }
    }

    public static CalibrationData getData(String string, String string2) {
        return map.get(string + "." + string2);
    }
}

