/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.WalkForwardPeriod;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.optimization.OptimizationParams;
import com.strategyquant.tradinglib.optimization.Parameter;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.results.SpecialValues;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WalkForwardParametersStability {
    private static final Logger Log = LoggerFactory.getLogger(WalkForwardParametersStability.class);
    private static final Comparator<Double> comp = Comparator.naturalOrder();

    public static void compute(ResultsGroup resultsGroup, OptimizationParams optimizationParams) {
        try {
            Object object;
            HashMap<String, Double> hashMap = new HashMap<String, Double>();
            HashMap<String, Double> hashMap2 = new HashMap<String, Double>();
            HashMap<String, ArrayList<Double>> hashMap3 = new HashMap<String, ArrayList<Double>>();
            HashMap<Object, Double> hashMap4 = new HashMap<Object, Double>();
            for (int i = 0; i < optimizationParams.size(); ++i) {
                object = (Parameter)optimizationParams.get(i);
                hashMap.put(((Parameter)object).getName(), ((Parameter)object).getStart());
                hashMap2.put(((Parameter)object).getName(), ((Parameter)object).getStop());
            }
            WalkForwardMatrixResult walkForwardMatrixResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
            if (walkForwardMatrixResult != null) {
                double d;
                object = walkForwardMatrixResult.getResultList();
                for (int i = 0; i < ((ArrayList)object).size(); ++i) {
                    WalkForwardResult walkForwardResult = (WalkForwardResult)((ArrayList)object).get(i);
                    hashMap3.clear();
                    for (int j = 0; j < walkForwardResult.wfPeriods.size(); ++j) {
                        WalkForwardPeriod walkForwardPeriod = walkForwardResult.wfPeriods.get(j);
                        WalkForwardParametersStability.loadParamValues(walkForwardPeriod.testParameters, hashMap3);
                    }
                    d = WalkForwardParametersStability.calculateParametersStability(hashMap, hashMap2, hashMap3);
                    String string = walkForwardResult.getResultKeyName();
                    hashMap4.put(string, d);
                    if (i != 0) continue;
                    resultsGroup.specialValues().set(WalkForwardParametersStability.getSpecialValuesKey(resultsGroup.getMainResultKey()), (Object)d);
                }
                double d2 = 0.0;
                d = Double.MAX_VALUE;
                for (String string : hashMap4.keySet()) {
                    double d3 = (Double)hashMap4.get(string);
                    d2 += d3;
                    d = Math.min(d, d3);
                    resultsGroup.specialValues().set(WalkForwardParametersStability.getSpecialValuesKey(string), (Object)d3);
                }
                resultsGroup.specialValues().set(SpecialValues.AvgParametersStability, (Object)SQUtils.round2((double)(d2 /= (double)hashMap4.size())));
                resultsGroup.specialValues().set(SpecialValues.WorstParametersStability, (Object)SQUtils.round2((double)d));
            }
        }
        catch (Exception exception) {
            Log.error("WF parameters stability calculation failed", (Throwable)exception);
        }
    }

    public static String getSpecialValuesKey(String string) {
        string = string.replaceAll("[^a-zA-Z0-9_]+", "_");
        return String.format("%s_%s", SpecialValues.ParametersStability, string);
    }

    private static void loadParamValues(String string, HashMap<String, ArrayList<Double>> hashMap) {
        if (string == null || string.isEmpty()) {
            return;
        }
        String[] stringArray = string.split(",");
        for (int i = 0; i < stringArray.length; ++i) {
            String string2 = stringArray[i];
            String[] stringArray2 = string2.split("=");
            if (stringArray2.length != 2) continue;
            String string3 = stringArray2[0];
            String string4 = stringArray2[1];
            try {
                double d = Double.parseDouble(string4);
                ArrayList<Double> arrayList = hashMap.get(string3);
                if (arrayList == null) {
                    arrayList = new ArrayList();
                    hashMap.put(string3, arrayList);
                }
                arrayList.add(d);
                continue;
            }
            catch (Exception exception) {
                // empty catch block
            }
        }
    }

    private static double calculateParametersStability(HashMap<String, Double> hashMap, HashMap<String, Double> hashMap2, HashMap<String, ArrayList<Double>> hashMap3) {
        double d = 0.0;
        if (hashMap3.size() == 0) {
            return -1.0;
        }
        for (String string : hashMap3.keySet()) {
            double d2;
            ArrayList<Double> arrayList = hashMap3.get(string);
            if (!hashMap.containsKey(string) || (d2 = hashMap2.get(string) - hashMap.get(string)) == 0.0) continue;
            double d3 = WalkForwardParametersStability.median(arrayList);
            double d4 = 0.0;
            for (int i = 0; i < arrayList.size(); ++i) {
                double d5 = arrayList.get(i);
                d4 += Math.abs(d5 - d3);
            }
            double d6 = 1.0 - (d4 /= (double)arrayList.size()) / d2;
            d += d6;
        }
        return SQUtils.round2((double)(d /= (double)hashMap3.size()));
    }

    private static double median(ArrayList<Double> arrayList) {
        int n = arrayList.size() / 2;
        double d = arrayList.size() % 2 == 0 ? (WalkForwardParametersStability.nth(arrayList, n - 1) + WalkForwardParametersStability.nth(arrayList, n)) / 2.0 : WalkForwardParametersStability.nth(arrayList, n);
        return d;
    }

    private static double nth(ArrayList<Double> arrayList, int n) {
        ArrayList<Double> arrayList2 = new ArrayList<Double>();
        ArrayList<Double> arrayList3 = new ArrayList<Double>();
        ArrayList<Double> arrayList4 = new ArrayList<Double>();
        double d = arrayList.get(n / 2);
        for (double d2 : arrayList) {
            int n2 = comp.compare(d2, d);
            if (n2 < 0) {
                arrayList2.add(d2);
                continue;
            }
            if (n2 > 0) {
                arrayList3.add(d2);
                continue;
            }
            arrayList4.add(d2);
        }
        double d3 = n < arrayList2.size() ? WalkForwardParametersStability.nth(arrayList2, n) : (n < arrayList2.size() + arrayList4.size() ? d : WalkForwardParametersStability.nth(arrayList3, n - arrayList2.size() - arrayList4.size()));
        return d3;
    }
}

