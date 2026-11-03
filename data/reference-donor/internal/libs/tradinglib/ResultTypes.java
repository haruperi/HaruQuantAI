/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.SQPluginManager
 */
package com.strategyquant.tradinglib;

import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import java.util.ArrayList;

public class ResultTypes {
    public static final String Main = "main";
    public static final String Portfolio = "portfolio";
    public static ArrayList<ICrossCheck> allCrossChecks;
    public static int[] crossCheckHashes;

    public static String typeToString(String string) {
        switch (string) {
            case "main": {
                return "Main data";
            }
            case "portfolio": {
                return "Portfolio";
            }
        }
        Object object = ResultTypes.getCrossCheckMethod(string);
        return object != null ? object.getName() : "?";
    }

    public static boolean isCrossCheck(String string) {
        ICrossCheck iCrossCheck = ResultTypes.getCrossCheckMethod(string);
        return iCrossCheck != null;
    }

    public static ICrossCheck findCrossCheckByType(String string) {
        return ResultTypes.getCrossCheckMethod(string);
    }

    public static boolean isValid(String string) {
        switch (string) {
            case "main": 
            case "portfolio": {
                return true;
            }
        }
        Object object = ResultTypes.getCrossCheckMethod(string);
        return object != null;
    }

    private static ICrossCheck getCrossCheckMethod(String string) {
        ResultTypes.checkCrossCheckHashesLoaded();
        int n = string.hashCode();
        for (int i = 0; i < crossCheckHashes.length; ++i) {
            if (n != crossCheckHashes[i]) continue;
            return allCrossChecks.get(i);
        }
        return null;
    }

    private static void checkCrossCheckHashesLoaded() {
        if (crossCheckHashes == null) {
            allCrossChecks = SQPluginManager.getPlugins(ICrossCheck.class);
            crossCheckHashes = new int[allCrossChecks.size()];
            for (int i = 0; i < allCrossChecks.size(); ++i) {
                ICrossCheck iCrossCheck = allCrossChecks.get(i);
                ResultTypes.crossCheckHashes[i] = iCrossCheck.getSettingName().hashCode();
            }
        }
    }
}

