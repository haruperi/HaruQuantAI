/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.tictactec.ta.lib.MAType
 */
package com.strategyquant.tradinglib.talib.reflection;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.talib.TALibIndicators;
import com.strategyquant.tradinglib.talib.reflection.TALibFunction;
import com.strategyquant.tradinglib.talib.reflection.TALibFunctions;
import com.tictactec.ta.lib.MAType;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

public class TALibXmlGenApp {
    private static final String OUT_PREFIX = "out";
    private static final String OUT_REAL_PREFIX = "outReal";
    private String[] BLACK_LIST = new String[]{"ADD", "SIN", "COS", "TAN", "SQRT", "LOG10", "EXP", "MIN", "MAX", "AD", "SUM", "LN", "ASIN", "ACOS", "ATAN", "CEIL", "FLOOR", "SINH", "COSH", "TANH", "SUB", "MULT", "DIV"};
    private static final Map<String, double[]> minMaxMap = new HashMap<String, double[]>();
    private StringBuilder sb;
    private StringBuilder problems;
    private Set<String> blackListSet;
    private Map<String, String> namesMap = new HashMap<String, String>();
    private Map<String, String> typesMap = new HashMap<String, String>();
    private Map<String, String> returnTypeMap = new HashMap<String, String>();
    private Map<String, String> categoryTypeMap = new HashMap<String, String>();

    public TALibXmlGenApp() throws IOException {
        this.blackListSet = new HashSet<String>();
        this.initNiceNameMap();
        this.initMinMax();
    }

    private void initMinMax() {
        minMaxMap.put("BBANDS", new double[]{0.0, 10.0});
        minMaxMap.put("STDDEV", new double[]{0.0, 10.0});
        minMaxMap.put("VAR", new double[]{0.0, 10.0});
        minMaxMap.put("SAR", new double[]{0.0, 1.0});
        minMaxMap.put("SAREXT", new double[]{0.0, 1.0});
        minMaxMap.put("CDLABANDONEDBABY", new double[]{0.0, 10.0});
        minMaxMap.put("CDLDARKCLOUDCOVER", new double[]{0.0, 10.0});
        minMaxMap.put("CDLEVENINGDOJISTAR", new double[]{0.0, 10.0});
        minMaxMap.put("CDLEVENINGSTAR", new double[]{0.0, 10.0});
        minMaxMap.put("CDLMATHOLD", new double[]{0.0, 10.0});
        minMaxMap.put("CDLMORNINGDOJISTAR", new double[]{0.0, 10.0});
        minMaxMap.put("CDLMORNINGSTAR", new double[]{0.0, 10.0});
    }

    private void initNiceNameMap() throws IOException {
        try (InputStream inputStream = TALibXmlGenApp.class.getResourceAsStream("talibdesc.txt");){
            List list = new BufferedReader(new InputStreamReader(inputStream, StandardCharsets.UTF_8)).lines().collect(Collectors.toList());
            for (String string : list) {
                if (string.isBlank()) continue;
                String[] stringArray = string.split("=");
                if (stringArray.length == 2) {
                    String string2 = stringArray[0];
                    String string3 = stringArray[1];
                    String[] stringArray2 = string3.split(";");
                    this.namesMap.put(string2, stringArray2[0]);
                    this.typesMap.put(string2, stringArray2[1]);
                    this.returnTypeMap.put(string2, stringArray2[2]);
                    this.categoryTypeMap.put(string2, stringArray2[3]);
                    continue;
                }
                System.out.println("Ignoring line:" + string);
            }
        }
    }

    public void generate() {
        TALibFunction[] tALibFunctionArray = TALibFunctions.getTALibFunctions();
        Arrays.sort(tALibFunctionArray, new Comparator<TALibFunction>(){

            @Override
            public int compare(TALibFunction tALibFunction, TALibFunction tALibFunction2) {
                return tALibFunction.getName().compareTo(tALibFunction2.getName());
            }
        });
        this.sb = new StringBuilder();
        this.problems = new StringBuilder();
        this.sb.append("<Talib>\n");
        this.printType("indy", "Indicators", tALibFunctionArray);
        this.printType("candle", "Candles", tALibFunctionArray);
        this.printType("func", "Functions", tALibFunctionArray);
        this.printType("price", "Prices", tALibFunctionArray);
        this.sb.append("</Talib>\n");
        System.out.println(this.sb.toString());
        System.out.println(this.problems.toString());
    }

    private String getCategoryType(String string) {
        String string2 = "indicator";
        if (string.equals("candle")) {
            string2 = "simpleRules";
        } else if (string.equals("func")) {
            string2 = "other";
        }
        return string2;
    }

    private void printType(String string, String string2, TALibFunction[] tALibFunctionArray) {
        this.sb.append("\t<" + string2 + ">\n");
        for (TALibFunction tALibFunction : tALibFunctionArray) {
            this.print(tALibFunction, string);
        }
        this.sb.append("\t</" + string2 + ">\n");
    }

    private String getType(TALibFunction tALibFunction) {
        return this.typesMap.get("talib_" + tALibFunction.getName());
    }

    private void print(TALibFunction tALibFunction, String string) {
        if (this.shouldSkip(tALibFunction)) {
            return;
        }
        if (!string.equals(this.getType(tALibFunction))) {
            return;
        }
        String string2 = this.getCategoryType(tALibFunction);
        this.begin(tALibFunction, string);
        this.params(tALibFunction, string2);
        this.end();
    }

    private void params(TALibFunction tALibFunction, String string) {
        this.sb.append("\t\t\t<paramCategory name=\"Default\" expanded=\"true\">\n");
        this.addStdParams(tALibFunction);
        this.addOptParams(tALibFunction);
        this.addOutParams(tALibFunction);
        this.addShift(string);
        this.sb.append("\t\t\t</paramCategory>\n");
    }

    private void addOutParams(TALibFunction tALibFunction) {
        TALibFunction.Param[] paramArray = tALibFunction.getOutputs();
        if (paramArray == null || paramArray.length < 2) {
            return;
        }
        StringBuilder stringBuilder = new StringBuilder();
        int n = 0;
        for (TALibFunction.Param param : paramArray) {
            String string;
            if (stringBuilder.length() != 0) {
                stringBuilder.append(",");
            }
            if ((string = param.getName()).startsWith(OUT_REAL_PREFIX)) {
                string = string.substring(OUT_REAL_PREFIX.length());
            } else if (string.startsWith(OUT_PREFIX)) {
                string = string.substring(OUT_PREFIX.length());
            }
            stringBuilder.append(string + "=" + n);
            ++n;
        }
        String string = "0";
        String string2 = stringBuilder.toString();
        this.sb.append("\t\t\t\t");
        this.sb.append("<Param key=\"#Line#\" type=\"int\" name=\"Line\" controlType=\"combo\" values=\"" + string2 + "\" defaultValue=\"" + string + "\" />\n");
    }

    private void addStdParams(TALibFunction tALibFunction) {
        this.sb.append("\t\t\t\t");
        this.sb.append("<Param key=\"#Chart#\" name=\"Chart\" type=\"data\" controlType=\"dataVar\" defaultValue=\"0\" />\n");
        for (TALibFunction.Param param : tALibFunction.getInputs()) {
            String string = param.getName();
            if (string.equals("inReal")) {
                this.sb.append("\t\t\t\t");
                this.sb.append("<Param key=\"#ComputedFrom#\" name=\"Computed From\" type=\"int\" controlType=\"combo\" values=\"Close=0,Open=1,High=2,Low=3,Median=4,Typical=5,Weighted=6,Volume=7\" defaultValue=\"0\" />\n");
                continue;
            }
            if (string.equals("inReal0")) {
                this.sb.append("\t\t\t\t");
                this.sb.append("<Param key=\"#ComputedFrom#\" name=\"Computed From 0\" type=\"int\" controlType=\"combo\" values=\"Close=0,Open=1,High=2,Low=3,Median=4,Typical=5,Weighted=6,Volume=7\" defaultValue=\"0\" />\n");
                continue;
            }
            if (!string.equals("inReal1")) continue;
            this.sb.append("\t\t\t\t");
            this.sb.append("<Param key=\"#ComputedFrom1#\" name=\"Computed From 1\" type=\"int\" controlType=\"combo\" values=\"Close=0,Open=1,High=2,Low=3,Median=4,Typical=5,Weighted=6,Volume=7\" defaultValue=\"0\" />\n");
        }
    }

    private void addShift(String string) {
        this.sb.append("\t\t\t\t");
        if ("simpleRules".equals(string)) {
            this.sb.append("<Param key=\"#Shift#\" name=\"Shift\" type=\"int\" defaultValue=\"1\" controlType=\"jspinnerVar\" minValue=\"0\" maxValue=\"100\" genMinValue=\"-1000001\" genMaxValue=\"-1000002\" paramType=\"shift\" step=\"1\" builderStep=\"1\" />\n");
        } else {
            this.sb.append("<Param key=\"#Shift#\" name=\"Shift\" type=\"int\" defaultValue=\"1\" controlType=\"jspinnerVar\" minValue=\"0\" maxValue=\"1000\" genMinValue=\"-1000001\" genMaxValue=\"-1000002\" paramType=\"shift\" step=\"1\" builderStep=\"1\" />\n");
        }
    }

    private void addOptParams(TALibFunction tALibFunction) {
        for (TALibFunction.Param param : tALibFunction.getOptInputs()) {
            String string = param.getName();
            if (!string.startsWith("optIn")) {
                throw new RuntimeException(L.t((String)"invalid opt param %s", (Object[])new Object[]{string}));
            }
            string = string.substring(5);
            String string2 = this.evalType(param);
            String string3 = this.evalAdditional(tALibFunction, param);
            this.sb.append("\t\t\t\t");
            this.sb.append("<Param key=\"#" + string + "#\" name=\"" + param.getDisplayName() + "\" type=\"" + string2 + "\" " + string3 + " />\n");
        }
    }

    private Object getDefault(TALibFunction tALibFunction, TALibFunction.Param param) {
        TALibFunction.IntegerParams integerParams = tALibFunction.getIntParameter(param.getName());
        TALibFunction.DoubleParams doubleParams = tALibFunction.getDoubleParameter(param.getName());
        if (integerParams != null) {
            return integerParams.getDef();
        }
        if (doubleParams != null) {
            return doubleParams.getDef();
        }
        return 0;
    }

    private Object getMinValue(TALibFunction tALibFunction, TALibFunction.Param param) {
        TALibFunction.IntegerParams integerParams = tALibFunction.getIntParameter(param.getName());
        TALibFunction.DoubleParams doubleParams = tALibFunction.getDoubleParameter(param.getName());
        if (integerParams != null) {
            return integerParams.getMin();
        }
        if (doubleParams != null) {
            return this.normalizeMinMaxValue(tALibFunction, doubleParams.getMin(), true);
        }
        throw new RuntimeException("Cannot evaluate min value for: " + tALibFunction.getName());
    }

    private Object getMaxValue(TALibFunction tALibFunction, TALibFunction.Param param) {
        TALibFunction.IntegerParams integerParams = tALibFunction.getIntParameter(param.getName());
        TALibFunction.DoubleParams doubleParams = tALibFunction.getDoubleParameter(param.getName());
        if (integerParams != null) {
            return integerParams.getMax();
        }
        if (doubleParams != null) {
            return this.normalizeMinMaxValue(tALibFunction, doubleParams.getMax(), false);
        }
        throw new RuntimeException("Cannot evaluate max value for: " + tALibFunction.getName());
    }

    private double normalizeMinMaxValue(TALibFunction tALibFunction, double d, boolean bl) {
        String string = String.valueOf(d);
        if (string.contains("E")) {
            double[] dArray = minMaxMap.get(tALibFunction.getName());
            if (dArray == null) {
                throw new RuntimeException("Unknown min/max for: " + tALibFunction.getName());
            }
            return bl ? dArray[0] : dArray[1];
        }
        return d;
    }

    private Object getStep(TALibFunction tALibFunction, TALibFunction.Param param) {
        TALibFunction.IntegerParams integerParams = tALibFunction.getIntParameter(param.getName());
        TALibFunction.DoubleParams doubleParams = tALibFunction.getDoubleParameter(param.getName());
        if (integerParams != null) {
            return integerParams.getStep();
        }
        if (doubleParams != null) {
            return doubleParams.getStep();
        }
        return 1;
    }

    private Object getSuggestedStart(TALibFunction tALibFunction, TALibFunction.Param param) {
        TALibFunction.IntegerParams integerParams = tALibFunction.getIntParameter(param.getName());
        TALibFunction.DoubleParams doubleParams = tALibFunction.getDoubleParameter(param.getName());
        if (integerParams != null) {
            return integerParams.getSuggStart();
        }
        if (doubleParams != null) {
            return doubleParams.getSuggStart();
        }
        return null;
    }

    private Object getSuggestedEnd(TALibFunction tALibFunction, TALibFunction.Param param) {
        TALibFunction.IntegerParams integerParams = tALibFunction.getIntParameter(param.getName());
        TALibFunction.DoubleParams doubleParams = tALibFunction.getDoubleParameter(param.getName());
        if (integerParams != null) {
            return integerParams.getSuggEnd();
        }
        if (doubleParams != null) {
            return doubleParams.getSuggEnd();
        }
        return null;
    }

    private String evalAdditional(TALibFunction tALibFunction, TALibFunction.Param param) {
        String string = param.getType();
        String string2 = "jspinnerVar";
        String string3 = " defaultValue=\"" + this.getDefault(tALibFunction, param) + "\" step=\"" + this.getStep(tALibFunction, param) + "\" builderStep=\"" + this.getStep(tALibFunction, param) + "\" minValue=\"" + this.getMinValue(tALibFunction, param) + "\" maxValue=\"" + this.getMaxValue(tALibFunction, param) + "\" builderMinValue=\"" + this.getSuggestedStart(tALibFunction, param) + "\" builderMaxValue=\"" + this.getSuggestedEnd(tALibFunction, param) + "\" builderStepValue=\"" + this.getStep(tALibFunction, param) + "\" ";
        this.checkMinMax(tALibFunction, param);
        if (string.equals("TA_OptInput_IntegerList")) {
            string2 = "combo";
            int n = 0;
            String string4 = "";
            for (MAType mAType : MAType.values()) {
                string4 = string4 + mAType.name() + "=" + n + ",";
                ++n;
            }
            string3 = " values=\"" + string4.substring(0, string4.length() - 1) + "\" defaultValue=\"" + this.getDefault(tALibFunction, param) + "\" ";
        } else if (TALibIndicators.isPeriod(param.getName())) {
            string3 = string3 + " paramType=\"period\" genMinValue=\"-1000003\" genMaxValue=\"-1000004\"";
        }
        return "controlType=\"" + string2 + "\"" + string3;
    }

    private void checkMinMax(TALibFunction tALibFunction, TALibFunction.Param param) {
        Double d = Double.valueOf(this.getMinValue(tALibFunction, param).toString());
        Double d2 = Double.valueOf(this.getMaxValue(tALibFunction, param).toString());
        if (TALibIndicators.isPeriod(param.getName()) && (d2 < 2.0 || d > 2.0)) {
            this.problems.append(tALibFunction.getName() + " - " + param.getName() + ": min=" + d + ", max:" + d2 + "\n");
        }
    }

    private String evalType(TALibFunction.Param param) {
        switch (param.getType()) {
            case "TA_OptInput_IntegerRange": 
            case "TA_OptInput_IntegerList": {
                return "int";
            }
            case "TA_OptInput_RealRange": {
                return "double";
            }
        }
        throw new RuntimeException(L.t((String)"Invalid type %s.", (Object[])new Object[]{param.getType()}));
    }

    private boolean shouldSkip(TALibFunction tALibFunction) {
        return this.blackListSet.contains(tALibFunction.getName());
    }

    private void end() {
        this.sb.append("\t\t</Item>\n");
    }

    private void begin(TALibFunction tALibFunction, String string) {
        String string2 = this.getDisplay(tALibFunction);
        String string3 = this.getCategoryType(tALibFunction);
        String string4 = "";
        if (string.equals("candle")) {
            string2 = this.getCandleDisplay(tALibFunction);
        } else if (string.equals("func")) {
            string4 = " mI=\"Functions\"";
        } else if (string.equals("price")) {
            string4 = " mI=\"Price\"";
        }
        if (tALibFunction.getName().equals("MAVP")) {
            string4 = string4 + " ignoreInBuilder=\"true\"";
        }
        this.sb.append("\t\t<Item key=\"talib_" + tALibFunction.getName() + "\" name=\"" + this.getUserFriendlyName(tALibFunction) + "\" display=\"" + string2 + "\" returnType=\"" + this.getReturnType(tALibFunction, string, string3) + "\" categoryType=\"" + string3 + "\"" + string4 + ">\n");
    }

    private String getCategoryType(TALibFunction tALibFunction) {
        return this.categoryTypeMap.get("talib_" + tALibFunction.getName());
    }

    private String getUserFriendlyName(TALibFunction tALibFunction) {
        String string = tALibFunction.getName();
        String string2 = this.namesMap.get("talib_" + string);
        if (string2 != null) {
            return string2;
        }
        return string;
    }

    private String getReturnType(TALibFunction tALibFunction, String string, String string2) {
        if ("simpleRules".equals(string2)) {
            return "boolean";
        }
        return this.returnTypeMap.get("talib_" + tALibFunction.getName());
    }

    private String getDisplay(TALibFunction tALibFunction) {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(tALibFunction.getName() + "(@Chart@");
        for (int i = 0; i < tALibFunction.getOptInputs().length; ++i) {
            TALibFunction.Param param = tALibFunction.getOptInputs()[i];
            String string = param.getName().substring(5);
            if (i != 0) {
                stringBuilder.append(",");
            }
            stringBuilder.append("#" + string + "#");
        }
        stringBuilder.append(")[#Shift#]");
        return stringBuilder.toString();
    }

    private String getCandleDisplay(TALibFunction tALibFunction) {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(this.getUserFriendlyName(tALibFunction));
        stringBuilder.append(" pattern #Shift# bar(s) ago");
        return stringBuilder.toString();
    }

    public static void main(String[] stringArray) throws IOException {
        new TALibXmlGenApp().generate();
    }
}

