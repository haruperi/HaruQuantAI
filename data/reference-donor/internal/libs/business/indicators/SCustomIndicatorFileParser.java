/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.wizard.desktop.indicators;

import com.strategyquant.lib.L;
import com.strategyquant.wizard.desktop.indicators.SCustomIndicator;
import com.strategyquant.wizard.desktop.indicators.SParameter;
import com.strategyquant.wizard.desktop.indicators.SParametersParser;
import java.io.File;
import java.nio.file.Files;

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
        var3_4 = new String(Files.readAllBytes(var0.toPath()));
        var4_5 = var3_4.replaceAll("\\s", "");
        if (var4_5.contains("#propertyindicator_chart_window")) {
            var1_1.returnType = "price";
        } else if (var4_5.contains("#propertyindicator_separate_window")) {
            var1_1.returnType = "number";
        } else {
            throw new Exception(L.t((String)"Unknown return type!", (Object[])new Object[0]));
        }
        var5_6 = 1;
        var6_7 = 0;
        block4: while (true) {
            ++var6_7;
            if ((var6_7 = var3_4.indexOf("extern", var6_7)) == -1) break;
            var7_8 = var6_7 - 1024;
            if (var7_8 < 0) {
                var7_8 = 0;
            }
            var8_10 = var3_4.substring(var7_8, var6_7);
            try {
                if (var8_10.substring(var8_10.lastIndexOf("\n")).contains("//")) {
                    continue;
                }
            }
            catch (Exception var9_11) {
                // empty catch block
            }
            var8_10 = var3_4.substring(var6_7 + 6);
            var8_10 = var8_10.replaceAll("\\s", "");
            if (!(var8_10 = var8_10.substring(0, 6)).contains("ENUM") && !var8_10.contains("int") && !var8_10.contains("double") && !var8_10.contains("color") && !var8_10.contains("string") && !var8_10.contains("bool")) continue;
            var9_12 = var3_4.indexOf(";", var6_7);
            var10_14 = new SParametersParser(var3_4.substring(var6_7, var9_12).trim());
            var10_14.parse();
            var11_15 = var10_14.list.iterator();
            while (true) {
                if (var11_15.hasNext()) ** break;
                continue block4;
                var12_16 = var11_15.next();
                var1_1.parameterList.add(new SParameter(var12_16.name.trim(), var10_14.type, var12_16.value, var5_6));
                var13_17 = var5_6;
                var5_6 = var5_6 + 1;
            }
            break;
        }
        var6_7 = var4_5.indexOf("indicator_buffers");
        if (var6_7 == -1) {
            throw new Exception(L.t((String)"Indicator doesn't contain any output data, it cannot be used as EA.", (Object[])new Object[0]));
        }
        var6_7 += 17;
        var7_9 = "";
        while (true) {
            if (Character.isDigit(var4_5.charAt(var6_7))) {
                var7_9 = var7_9 + var4_5.charAt(var6_7);
            } else if (!Character.isDigit(var4_5.charAt(var6_7)) && !var7_9.equals("")) break;
            ++var6_7;
        }
        var8_10 = Integer.parseInt(var7_9);
        if (var8_10.intValue() == 1) {
            var1_1.outputList.add(var1_1.fileName);
            return var1_1;
        }
        var6_7 = 0;
        var5_6 = 1;
        while (true) {
            ++var6_7;
            if ((var6_7 = var3_4.indexOf("SetIndexBuffer", var6_7)) == -1) break;
            var9_13 = var3_4.indexOf(")", var6_7);
            var10_14 = var3_4.substring(var6_7, var9_13).split("[,]+");
            if (var10_14.length != 2) {
                throw new Exception(L.t((String)"Unknown output definition!", (Object[])new Object[0]));
            }
            var1_1.outputList.add(var10_14[1].trim());
            if (var8_10 == var5_6) break;
            var11_15 = var5_6;
            var5_6 = var5_6 + 1;
        }
        return var1_1;
    }
}

