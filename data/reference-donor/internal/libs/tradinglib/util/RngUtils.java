/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 */
package com.strategyquant.tradinglib.util;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.WalkForwardPeriod;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.optimization.FitnessMetricComparator;
import com.strategyquant.tradinglib.optimization.MetricForFitness;
import com.strategyquant.tradinglib.optimization.OptimizationSettings;
import com.strategyquant.tradinglib.optimization.OrdersIndexComparator;
import com.strategyquant.tradinglib.optimization.StandardFitnessComparator;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;

public class RngUtils {
    private static final OrdersIndexComparator comparatorIndex = new OrdersIndexComparator();
    private static final StandardFitnessComparator comparatorFitness = new StandardFitnessComparator();

    public static void sortCandidatesByIndexFitness(ArrayList<ResultsGroup> arrayList, IFitnessFunction iFitnessFunction) {
        for (int i = 0; i < arrayList.size(); ++i) {
            ResultsGroup resultsGroup = arrayList.get(i);
            resultsGroup.specialValues().set("OptIndexFitness", (Object)0.0);
        }
        ArrayList<MetricForFitness> arrayList2 = iFitnessFunction.getMetricsForFitness();
        for (int i = 0; i < arrayList2.size(); ++i) {
            MetricForFitness metricForFitness = arrayList2.get(i);
            RngUtils.setIndexByMetric(arrayList, metricForFitness, iFitnessFunction);
        }
        arrayList.sort(comparatorIndex);
    }

    public static void setIndexByMetric(ArrayList<ResultsGroup> arrayList, MetricForFitness metricForFitness, IFitnessFunction iFitnessFunction) {
        FitnessMetricComparator fitnessMetricComparator = new FitnessMetricComparator(metricForFitness, iFitnessFunction);
        arrayList.sort(fitnessMetricComparator);
        try {
            for (int i = 0; i < arrayList.size(); ++i) {
                ResultsGroup resultsGroup = arrayList.get(i);
                double d = resultsGroup.specialValues().getDouble("OptIndexFitness");
                double d2 = d + metricForFitness.weight * ((double)i + 1.0);
                resultsGroup.specialValues().set("OptIndexFitness", (Object)d2);
            }
        }
        catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    public static void sortCandidatesByStandardFitness(ArrayList<ResultsGroup> arrayList, IFitnessFunction iFitnessFunction) throws Exception {
        ResultsGroup resultsGroup;
        int n;
        for (n = 0; n < arrayList.size(); ++n) {
            resultsGroup = arrayList.get(n);
            resultsGroup.specialValues().set("OptIndexFitness", (Object)0.0);
        }
        for (n = 0; n < arrayList.size(); ++n) {
            resultsGroup = arrayList.get(n);
            RngUtils.computeFitness(resultsGroup, iFitnessFunction);
        }
        arrayList.sort(comparatorFitness);
    }

    private static void computeFitness(ResultsGroup resultsGroup, IFitnessFunction iFitnessFunction) throws Exception {
        double d = iFitnessFunction.computeFitness(resultsGroup, (byte)0, (byte)10);
        resultsGroup.portfolio().setFitness((byte)10, d);
        resultsGroup.portfolio().setFitness((byte)20, d);
        resultsGroup.portfolio().setFitness((byte)127, d);
    }

    public static void printCandidates(String string, ArrayList<ResultsGroup> arrayList, String string2) {
        System.out.println("==========================================");
        System.out.println(string);
        System.out.println("==========================================");
        try {
            for (int i = 0; i < arrayList.size(); ++i) {
                ResultsGroup resultsGroup = arrayList.get(i);
                double d = resultsGroup.subResult(resultsGroup.getMainResultKey()).statsOrNull((byte)0, (byte)10, (byte)10).getDouble(string2);
                double d2 = resultsGroup.specialValues().getDouble("OptIndexFitness");
                System.out.println("#" + i + " : " + resultsGroup.getName() + " : " + d + " : fitness: " + d2);
            }
        }
        catch (Exception exception) {
            exception.printStackTrace();
        }
        System.out.println("------------------------------------------");
    }

    public static String getString(HashMap<String, Object> hashMap, String string, String string2) {
        String string3 = (String)hashMap.get(string);
        if (string3 == null || string3.isEmpty()) {
            return string2;
        }
        return string3;
    }

    public static int getInt(HashMap<String, Object> hashMap, String string, int n) {
        String string2 = (String)hashMap.get(string);
        if (string2 == null || string2.isEmpty()) {
            return n;
        }
        int n2 = Integer.parseInt(string2);
        return n2;
    }

    public static boolean getBool(HashMap<String, Object> hashMap, String string, boolean bl) {
        String string2 = (String)hashMap.get(string);
        if (string2 == null || string2.isEmpty()) {
            return bl;
        }
        boolean bl2 = Boolean.parseBoolean(string2);
        return bl2;
    }

    public static String getFitnessNameFromOptimizationType(int n) throws Exception {
        switch (n) {
            case 1: {
                return "fitnessSimple";
            }
            case 2: {
                return "fitnessWF";
            }
            case 3: {
                return "fitnessCA";
            }
        }
        throw new Exception(L.t((String)"Cannot recognize Optimization type from settings!", (Object[])new Object[0]));
    }

    public static String printStrategiesToLog(ArrayList<ResultsGroup> arrayList, String string) throws Exception {
        IFitnessFunction iFitnessFunction = null;
        iFitnessFunction = ProjectConfigHelper.getFitnessFunction(null);
        RngUtils.sortCandidatesByStandardFitness(arrayList, iFitnessFunction);
        StringBuffer stringBuffer = new StringBuffer();
        stringBuffer.append("List of all evaluated strategies, sorted by their fitness (output as CSV format, tab-delimited) ---------------------------------\n");
        ArrayList<String> arrayList2 = RngUtils.printStrategyResultsHeader(stringBuffer, false, iFitnessFunction);
        for (int i = 0; i < arrayList.size(); ++i) {
            ResultsGroup resultsGroup = arrayList.get(i);
            RngUtils.printStrategyResultToLog(stringBuffer, resultsGroup, false, arrayList2);
        }
        stringBuffer.append("------------------------------------------------------------------\n");
        return stringBuffer.toString();
    }

    public static ArrayList<String> printStrategyResultsHeader(StringBuffer stringBuffer, boolean bl, IFitnessFunction iFitnessFunction) {
        ArrayList<String> arrayList = new ArrayList<String>();
        if (iFitnessFunction != null) {
            ArrayList<MetricForFitness> arrayList2 = iFitnessFunction.getMetricsForFitness();
            for (int i = 0; i < arrayList2.size(); ++i) {
                MetricForFitness metricForFitness = arrayList2.get(i);
                arrayList.add(metricForFitness.metric);
            }
        }
        RngUtils.addIfNotExist(arrayList, "NumberOfTrades");
        RngUtils.addIfNotExist(arrayList, "NetProfit");
        stringBuffer.append("Strategy name\t");
        stringBuffer.append("Parameters\t");
        stringBuffer.append("Fitness\t");
        stringBuffer.append("FitnessIndex\t");
        for (int i = 0; i < arrayList.size(); ++i) {
            stringBuffer.append(arrayList.get(i));
            stringBuffer.append("\t");
        }
        stringBuffer.append("\n");
        return arrayList;
    }

    private static void printStrategyResultToLog(StringBuffer stringBuffer, ResultsGroup resultsGroup, boolean bl, ArrayList<String> arrayList) throws Exception {
        stringBuffer.append(resultsGroup.getName());
        stringBuffer.append("\t");
        stringBuffer.append(RngUtils.getParameters(resultsGroup));
        stringBuffer.append("\t");
        double d = resultsGroup.portfolio().getFitness((byte)10);
        stringBuffer.append(String.format("%.6f", d));
        stringBuffer.append("\t");
        double d2 = resultsGroup.specialValues().getDouble("OptIndexFitness", 0.0);
        stringBuffer.append(String.format("%.2f", d2));
        stringBuffer.append("\t");
        for (int i = 0; i < arrayList.size(); ++i) {
            String string = arrayList.get(i);
            double d3 = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127).getDouble(string);
            stringBuffer.append(String.format("%.2f", d3));
            stringBuffer.append("\t");
        }
        stringBuffer.append("\n");
    }

    private static String getParameters(ResultsGroup resultsGroup) {
        try {
            WalkForwardMatrixResult walkForwardMatrixResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
            WalkForwardResult walkForwardResult = walkForwardMatrixResult.getWFResult(resultsGroup.getBestWFResultKey(), true);
            return walkForwardResult.testParams;
        }
        catch (Exception exception) {
            return resultsGroup.getParams();
        }
    }

    private static void addIfNotExist(ArrayList<String> arrayList, String string) {
        for (int i = 0; i < arrayList.size(); ++i) {
            if (!arrayList.get(i).equals(string)) continue;
            return;
        }
        arrayList.add(string);
    }

    public static void debugWFLogCandidate(StringBuffer stringBuffer, String string, ResultsGroup resultsGroup, ArrayList<String> arrayList) throws Exception {
        stringBuffer.append(string);
        stringBuffer.append("\t");
        stringBuffer.append(resultsGroup.specialValues().getString("OptimizationParameters"));
        stringBuffer.append("\t");
        double d = resultsGroup.portfolio().getFitness((byte)10);
        stringBuffer.append(String.format("%.6f", d));
        stringBuffer.append("\t");
        double d2 = resultsGroup.specialValues().getDouble("OptIndexFitness", 0.0);
        stringBuffer.append(String.format("%.2f", d2));
        stringBuffer.append("\t");
        for (int i = 0; i < arrayList.size(); ++i) {
            String string2 = arrayList.get(i);
            double d3 = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127).getDouble(string2);
            stringBuffer.append(String.format("%.2f", d3));
            stringBuffer.append("\t");
        }
        stringBuffer.append("\n");
    }

    public static void debugWFLogWriteFile(OptimizationSettings optimizationSettings, String string, String string2, StringBuffer stringBuffer, WalkForwardPeriod walkForwardPeriod) {
        String string3 = RngUtils.getDebugFilePath(optimizationSettings, string, string2, walkForwardPeriod);
        File file = new File(string3);
        if (file.exists()) {
            boolean bl;
            boolean bl2 = bl = true;
        }
        if (string3 != null) {
            SQUtils.stringToFile((File)new File(string3), (String)stringBuffer.toString());
        }
    }

    private static String getDebugFilePath(OptimizationSettings optimizationSettings, String string, String string2, WalkForwardPeriod walkForwardPeriod) {
        StringBuffer stringBuffer = new StringBuffer(optimizationSettings.debugWFFitnessPath);
        stringBuffer.append("/");
        if (optimizationSettings.type == 2) {
            stringBuffer.append("WF_");
        } else {
            stringBuffer.append("CA_");
        }
        stringBuffer.append(SQTime.toDateString((long)walkForwardPeriod.runFrom));
        stringBuffer.append("_");
        stringBuffer.append(SQTime.toDateString((long)walkForwardPeriod.runTo));
        stringBuffer.append("_");
        stringBuffer.append(string);
        string2 = string2.replace(":", "");
        stringBuffer.append(string2);
        stringBuffer.append(".csv");
        return stringBuffer.toString();
    }
}

