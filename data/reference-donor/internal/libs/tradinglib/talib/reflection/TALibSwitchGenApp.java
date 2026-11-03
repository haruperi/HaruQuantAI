/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib.talib.reflection;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.talib.reflection.TALibFunction;
import com.strategyquant.tradinglib.talib.reflection.TALibFunctions;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

public class TALibSwitchGenApp {
    private String[] BLACK_LIST = new String[]{"ADD", "SIN", "COS", "TAN", "SQRT", "LOG10", "EXP", "MIN", "MAX", "AD", "SUM", "LN", "ASIN", "ACOS", "ATAN", "CEIL", "FLOOR", "SINH", "COSH", "TANH", "SUB", "MULT", "DIV"};
    private StringBuilder sb;
    private Set<String> blackListSet = new HashSet<String>();
    private List<String> hlcIndicators;

    public void generate() {
        TALibFunction[] tALibFunctionArray = TALibFunctions.getTALibFunctions();
        this.sb = new StringBuilder();
        this.hlcIndicators = new LinkedList<String>();
        for (TALibFunction tALibFunction : tALibFunctionArray) {
            this.print(tALibFunction);
        }
        System.out.println(this.sb.toString());
        System.out.println("\n\n\"" + this.hlcIndicators.stream().collect(Collectors.joining("\",\"")) + "\"");
    }

    private void print(TALibFunction tALibFunction) {
        if (this.shouldSkip(tALibFunction)) {
            return;
        }
        this.caseBegin(tALibFunction);
        this.coreFce(tALibFunction);
        this.caseEnd();
    }

    private void coreFce(TALibFunction tALibFunction) {
        this.prepareOutputs(tALibFunction);
        this.sb.append("\t\t");
        this.sb.append("retCode = core." + tALibFunction.getTalibMethod().getName() + "(");
        this.sb.append("startIdx, endIdx, ");
        boolean bl = this.addIns(tALibFunction);
        if (bl) {
            this.hlcIndicators.add(tALibFunction.getName());
        }
        this.addOptParams(tALibFunction);
        this.sb.append("outBegIdx, outNbElement");
        this.addOutputs(tALibFunction);
        this.sb.append(");\n");
    }

    private void addOutputs(TALibFunction tALibFunction) {
        int n = 0;
        int n2 = 0;
        for (TALibFunction.Param param : tALibFunction.getOutputs()) {
            if (param.getType().equals("TA_Output_Real")) {
                this.sb.append(", outDlb[" + n2 + "]");
                ++n2;
                continue;
            }
            if (!param.getType().equals("TA_Output_Integer")) continue;
            this.sb.append(", outInt[" + n + "]");
            ++n;
        }
    }

    private void prepareOutputs(TALibFunction tALibFunction) {
        int n = 0;
        int n2 = 0;
        boolean[] blArray = new boolean[tALibFunction.getOutputs().length];
        int n3 = 0;
        for (TALibFunction.Param param : tALibFunction.getOutputs()) {
            if (param.getType().equals("TA_Output_Real")) {
                ++n2;
                blArray[n3++] = true;
                continue;
            }
            if (!param.getType().equals("TA_Output_Integer")) continue;
            ++n;
            blArray[n3++] = false;
        }
        if (n2 != 0) {
            this.sb.append("\t\toutDlb = new double[" + n2 + "][o.length];\n");
        }
        if (n != 0) {
            this.sb.append("\t\toutInt = new int[" + n + "][o.length];\n");
        }
        if (n3 > 0) {
            this.sb.append("\t\tresultFlags = new boolean[]{");
            for (int i = 0; i < n3; ++i) {
                this.sb.append(blArray[i]);
                if (i >= n3 - 1) continue;
                this.sb.append(", ");
            }
            this.sb.append("};\n");
        }
    }

    private void addOptParams(TALibFunction tALibFunction) {
        for (TALibFunction.Param param : tALibFunction.getOptInputs()) {
            String string;
            String string2 = param.getName();
            if (string2.startsWith("optIn")) {
                string2 = string2.substring(5);
                boolean bl = this.isMin(string2);
                boolean bl2 = this.isMax(string2);
                string = string2;
                string = param.getType().equals("TA_OptInput_IntegerList") ? "params.getInt(\"" + string2 + "\")" : "params.get" + this.getParamTyp(param.getType()) + "(\"" + string2 + "\")";
                if (bl) {
                    string = "getMin(" + string + "," + this.getOpposite(false, string) + ")";
                }
                if (bl2) {
                    string = "getMax(" + string + "," + this.getOpposite(true, string) + ")";
                }
                if (this.isMAType(string2)) {
                    string = "getMAType(" + string + ")";
                }
            } else {
                throw new RuntimeException(L.t((String)"invalid opt param %", (Object[])new Object[]{string2}));
            }
            this.sb.append(string + ",");
        }
    }

    private String getOpposite(boolean bl, String string) {
        if (bl) {
            return string.replace("Max", "Min").replace("Slow", "Fast");
        }
        return string.replace("Min", "Max").replace("Fast", "Slow");
    }

    private boolean isMAType(String string) {
        return string.contains("MAType");
    }

    private boolean isMin(String string) {
        return string.equals("MinPeriod") || string.equals("FastPeriod");
    }

    private boolean isMax(String string) {
        return string.equals("MaxPeriod") || string.equals("SlowPeriod");
    }

    private String getParamTyp(String string) {
        switch (string) {
            case "TA_OptInput_IntegerRange": {
                return "Int";
            }
            case "TA_OptInput_RealRange": {
                return "Double";
            }
        }
        return null;
    }

    private boolean addIns(TALibFunction tALibFunction) {
        boolean bl = false;
        for (TALibFunction.Param param : tALibFunction.getInputs()) {
            String string = param.getName();
            if (string.startsWith("inPrice")) {
                block8: for (int i = 7; i < string.length(); ++i) {
                    char c = string.charAt(i);
                    switch (c) {
                        case 'O': {
                            this.sb.append("o, ");
                            continue block8;
                        }
                        case 'H': {
                            this.sb.append("h, ");
                            bl = true;
                            continue block8;
                        }
                        case 'L': {
                            this.sb.append("l, ");
                            bl = true;
                            continue block8;
                        }
                        case 'C': {
                            this.sb.append("c, ");
                            bl = true;
                            continue block8;
                        }
                        case 'V': {
                            this.sb.append("v, ");
                            continue block8;
                        }
                        default: {
                            throw new RuntimeException("invalid price arg: " + c);
                        }
                    }
                }
                continue;
            }
            if (string.equals("inReal")) {
                this.sb.append("in0, ");
                continue;
            }
            if (string.equals("inReal0")) {
                this.sb.append("in0, ");
                continue;
            }
            if (string.equals("inReal1")) {
                this.sb.append("in1, ");
                continue;
            }
            if (!string.equals("inPeriods")) continue;
            this.sb.append("p, ");
        }
        return bl;
    }

    private boolean shouldSkip(TALibFunction tALibFunction) {
        return this.blackListSet.contains(tALibFunction.getName());
    }

    private void caseEnd() {
        this.sb.append("\t\tbreak;\n");
    }

    private void caseBegin(TALibFunction tALibFunction) {
        this.sb.append("\tcase \"" + tALibFunction.getName() + "\":\n");
    }

    public static void main(String[] stringArray) {
        new TALibSwitchGenApp().generate();
    }
}

