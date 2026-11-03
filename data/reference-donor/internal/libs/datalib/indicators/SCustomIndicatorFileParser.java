/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 */
package com.strategyquant.datalib.indicators;

import com.strategyquant.datalib.indicators.SCustomIndicator;
import com.strategyquant.datalib.indicators.SParameter;
import com.strategyquant.datalib.indicators.SParametersParser;
import com.strategyquant.lib.SQUtils;
import java.io.File;

public class SCustomIndicatorFileParser {
    /*
     * Unable to fully structure code
     */
    public static SCustomIndicator parse(File var0) throws Exception {
        var1_1 = new SCustomIndicator();
        var2_3 = var0.getName().indexOf(".mq4");
        if (var2_3 == -1) {
            var2_3 = var0.getName().indexOf(".xml");
        }
        var1_1.fileName = var0.getName().substring(0, var2_3);
        var1_1.shortName = var1_1.fileName.replaceAll("\\s", "_");
        var1_1.longName = var1_1.fileName;
        var3_4 = new String[]{"UTF-8", "UTF-16"};
        var4_5 = null;
        var5_6 = null;
        for (var6_7 = 0; var6_7 < var3_4.length && !(var4_5 = (var5_6 = SQUtils.fileToString((File)var0, (String)var3_4[var6_7])).replaceAll("\\s", "")).contains("property"); ++var6_7) {
        }
        if (var4_5.contains("#propertyindicator_chart_window")) {
            var1_1.returnType = 1;
        } else if (var4_5.contains("#propertyindicator_separate_window")) {
            var1_1.returnType = 2;
        } else {
            throw new Exception("Unknown return type!");
        }
        var6_8 = 1;
        var7_9 = 0;
        block5: while (true) {
            ++var7_9;
            if ((var7_9 = var5_6.indexOf("extern", var7_9)) == -1) break;
            var8_10 = var7_9 - 1024;
            if (var8_10 < 0) {
                var8_10 = 0;
            }
            var9_12 = var5_6.substring(var8_10, var7_9);
            try {
                if (var9_12.substring(var9_12.lastIndexOf("\n")).contains("//")) {
                    continue;
                }
            }
            catch (Exception var10_13) {
                // empty catch block
            }
            var9_12 = var5_6.substring(var7_9 + 6);
            var9_12 = var9_12.replaceAll("\\s", "");
            if (!(var9_12 = var9_12.substring(0, 6)).contains("ENUM") && !var9_12.contains("int") && !var9_12.contains("double") && !var9_12.contains("color") && !var9_12.contains("string") && !var9_12.contains("bool")) continue;
            var10_14 = var5_6.indexOf(";", var7_9);
            var11_16 = new SParametersParser(var5_6.substring(var7_9, var10_14).trim());
            var11_16.parse();
            var12_17 = var11_16.list.iterator();
            while (true) {
                if (var12_17.hasNext()) ** break;
                continue block5;
                var13_18 = var12_17.next();
                var1_1.parameterList.add(new SParameter(var13_18.name.trim(), var11_16.type, var13_18.value, var6_8));
                var14_19 = var6_8;
                var6_8 = var6_8 + 1;
            }
            break;
        }
        var7_9 = var4_5.indexOf("indicator_buffers");
        if (var7_9 == -1) {
            throw new Exception("Indicator doesn't contain any output data, it cannot be used as EA.");
        }
        var7_9 += 17;
        var8_11 = "";
        while (true) {
            if (Character.isDigit(var4_5.charAt(var7_9))) {
                var8_11 = var8_11 + var4_5.charAt(var7_9);
            } else if (!Character.isDigit(var4_5.charAt(var7_9)) && !var8_11.equals("")) break;
            ++var7_9;
        }
        var9_12 = Integer.parseInt(var8_11);
        if (var9_12.intValue() == 1) {
            var1_1.outputList.add(var1_1.fileName);
            return var1_1;
        }
        var7_9 = 0;
        var6_8 = 1;
        while (true) {
            ++var7_9;
            if ((var7_9 = var5_6.indexOf("SetIndexBuffer", var7_9)) == -1) break;
            var10_15 = var5_6.indexOf(")", var7_9);
            var11_16 = var5_6.substring(var7_9, var10_15);
            var12_17 = var11_16.split("[,]+");
            if (var12_17.length < 2) {
                throw new Exception(String.format("Invalid output definition: '%s'", new Object[]{var11_16}));
            }
            var1_1.outputList.add(var12_17[1].trim());
            if (var9_12 == var6_8) break;
            var13_18 = var6_8;
            var6_8 = var6_8 + 1;
        }
        return var1_1;
    }
}

