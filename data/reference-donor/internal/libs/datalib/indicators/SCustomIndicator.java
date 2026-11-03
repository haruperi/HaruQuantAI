/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.indicators;

import com.strategyquant.datalib.indicators.SParameter;
import java.util.ArrayList;

public class SCustomIndicator {
    public String fileName;
    public String shortName;
    public String longName;
    public int returnType;
    public ArrayList<SParameter> parameterList = new ArrayList();
    public ArrayList<String> outputList = new ArrayList();

    public String toString() {
        int n;
        String string = "-----------------------------------------------------------------\nCustom indicator: " + this.fileName + ", shortName: " + this.shortName + ", longName: " + this.longName + ", type:" + this.returnType;
        for (n = 0; n < this.parameterList.size(); ++n) {
            string = string + "\nparameter " + n + ": " + this.parameterList.get(n).toString();
        }
        for (n = 0; n < this.outputList.size(); ++n) {
            string = string + "\noutput " + n + ": " + this.outputList.get(n);
        }
        string = string + "\n-----------------------------------------------------------------";
        return string;
    }
}

