/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.tictactec.ta.lib.meta.annotation.InputParameterType
 */
package com.strategyquant.tradinglib.talib.reflection;

import com.tictactec.ta.lib.meta.annotation.InputParameterType;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public class TALibFunction {
    private String name;
    private int inputCount;
    private int optInputCount;
    private int outputCount;
    private Method talibMethod;
    private ArrayList<Param> inputs = new ArrayList();
    private ArrayList<Param> optInputs = new ArrayList();
    private ArrayList<Param> outputs = new ArrayList();
    private Map<String, IntegerParams> intParams = new HashMap<String, IntegerParams>();
    private Map<String, DoubleParams> dblParams = new HashMap<String, DoubleParams>();

    public TALibFunction(Method method, String string, int n, int n2, int n3) {
        this.talibMethod = method;
        this.name = string;
        this.inputCount = n;
        this.optInputCount = n2;
        this.outputCount = n3;
    }

    public Method getTalibMethod() {
        return this.talibMethod;
    }

    public void addInput(Param param) {
        this.inputs.add(param);
    }

    public void addOptInput(Param param) {
        this.optInputs.add(param);
    }

    public void addOutput(Param param) {
        this.outputs.add(param);
    }

    public Param[] getInputs() {
        return this.inputs.toArray(new Param[this.inputs.size()]);
    }

    public Param[] getOptInputs() {
        return this.optInputs.toArray(new Param[this.optInputs.size()]);
    }

    public Param[] getOutputs() {
        return this.outputs.toArray(new Param[this.outputs.size()]);
    }

    public int getInputParameterCount() {
        int n = 0;
        if (this.outputs.size() > 1) {
            ++n;
        }
        for (Param param : this.inputs) {
            if (param.getType().equals(InputParameterType.TA_Input_Price.toString())) continue;
            ++n;
        }
        return this.optInputCount + n;
    }

    public String getName() {
        return this.name;
    }

    public String toString() {
        String string = this.name + "(" + this.inputCount + "," + this.optInputCount + "," + this.outputCount + ") \n";
        for (Param param : this.inputs) {
            string = string + "\t" + param.getName() + "=" + param.getType() + "\n";
        }
        for (Param param : this.optInputs) {
            string = string + "\t" + param.getName() + "=" + param.getType() + "\n";
        }
        for (Param param : this.outputs) {
            string = string + "\t" + param.getName() + "=" + param.getType() + "\n";
        }
        return string;
    }

    public IntegerParams getIntParameter(String string) {
        return this.intParams.get(string);
    }

    public void addIntegerRange(String string, IntegerParams integerParams) {
        this.intParams.put(string, integerParams);
    }

    public DoubleParams getDoubleParameter(String string) {
        return this.dblParams.get(string);
    }

    public void addDoubleRange(String string, DoubleParams doubleParams) {
        this.dblParams.put(string, doubleParams);
    }

    public static class Param {
        private String name;
        private String type;
        private String displayName;
        private int flags;

        public Param(String string, String string2, int n) {
            this(string, string2, string, n);
        }

        public Param(String string, String string2, String string3, int n) {
            this.name = string;
            this.type = string2;
            this.flags = n;
            this.setDisplayName(string3);
        }

        public int getFlags() {
            return this.flags;
        }

        public String getName() {
            return this.name;
        }

        public void setName(String string) {
            this.name = string;
        }

        public String getType() {
            return this.type;
        }

        public void setType(String string) {
            this.type = string;
        }

        public boolean isSame(Param param) {
            return this.name.equals(param.getName()) && this.type.equals(param.getType());
        }

        public String getDisplayName() {
            return this.displayName;
        }

        public void setDisplayName(String string) {
            this.displayName = string;
        }
    }

    public static class IntegerParams {
        private int min;
        private int max;
        private int def;
        private int step;
        private int suggStart;
        private int suggEnd;

        public IntegerParams(int n, int n2, int n3, int n4, int n5, int n6) {
            this.min = n;
            this.max = n2;
            this.def = n3;
            this.suggStart = n4;
            this.suggEnd = n5;
            this.step = n6;
        }

        public int getSuggStart() {
            return this.suggStart;
        }

        public void setSuggStart(int n) {
            this.suggStart = n;
        }

        public int getSuggEnd() {
            return this.suggEnd;
        }

        public void setSuggEnd(int n) {
            this.suggEnd = n;
        }

        public int getMin() {
            return this.min;
        }

        public void setMin(int n) {
            this.min = n;
        }

        public int getMax() {
            return this.max;
        }

        public void setMax(int n) {
            this.max = n;
        }

        public int getDef() {
            return this.def;
        }

        public void setDef(int n) {
            this.def = n;
        }

        public int getStep() {
            return this.step;
        }

        public void setStep(int n) {
            this.step = n;
        }
    }

    public static class DoubleParams {
        private double min;
        private double max;
        private double def;
        private double step;
        private double suggStart;
        private double suggEnd;

        public DoubleParams(double d, double d2, double d3, double d4, double d5, double d6) {
            this.min = d;
            this.max = d2;
            this.def = d3;
            this.suggStart = d4;
            this.suggEnd = d5;
            this.step = d6;
        }

        public double getSuggStart() {
            return this.suggStart;
        }

        public void setSuggStart(double d) {
            this.suggStart = d;
        }

        public double getSuggEnd() {
            return this.suggEnd;
        }

        public void setSuggEnd(double d) {
            this.suggEnd = d;
        }

        public double getMin() {
            return this.min;
        }

        public void setMin(double d) {
            this.min = d;
        }

        public double getMax() {
            return this.max;
        }

        public void setMax(double d) {
            this.max = d;
        }

        public double getDef() {
            return this.def;
        }

        public void setDef(double d) {
            this.def = d;
        }

        public double getStep() {
            return this.step;
        }

        public void setStep(double d) {
            this.step = d;
        }
    }
}

