/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 */
package com.strategyquant.tradinglib.talib;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.engine.stockpicker.data.BarData;
import com.strategyquant.tradinglib.talib.TALibIndicators;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.io.File;
import java.util.Scanner;

public class TALibIndicatorsTest {
    TALibIndicators indicators = new TALibIndicators();

    public static void main(String[] stringArray) {
        TALibIndicatorsTest tALibIndicatorsTest = new TALibIndicatorsTest();
        tALibIndicatorsTest.run();
    }

    private void run() {
        try {
            this.test("CustomIndy_PercentRank_D1_14_Close.csv", "PercentRank", "TimePeriod", 14);
        }
        catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    private void test(String string, String string2, Object ... objectArray) throws Exception {
        int n;
        System.out.println("***************** " + string2 + " **************");
        ObjectArrayList<BarData> objectArrayList = this.loadData(string);
        SettingsMap settingsMap = new SettingsMap();
        for (n = 0; n < objectArray.length; n += 2) {
            settingsMap.set((String)objectArray[n], objectArray[n + 1]);
        }
        n = this.compare(string2, settingsMap, objectArrayList);
        if (n > 0) {
            System.out.println(String.format("Test '%s' FAILED: %d differences found", string, n));
        } else {
            System.out.println(String.format("Test '%s' SUCCESS: No differences found", string));
        }
    }

    private ObjectArrayList<BarData> loadData(String string) throws Exception {
        BarData barData;
        File file = new File("tests\\stockpicker\\Indicators\\" + string);
        String string2 = SQUtils.fileToString((File)file);
        ObjectArrayList objectArrayList = new ObjectArrayList();
        int n = 0;
        try {
            Scanner scanner = new Scanner(string2);
            while (scanner.hasNextLine()) {
                ++n;
                String string3 = scanner.nextLine();
                String[] stringArray = string3.split("\t", -1);
                barData = new BarData();
                barData.time = SQTime.parseToMilis((String)stringArray[0], (String)"MM/dd/yyyy");
                barData.open = Float.valueOf(stringArray[1]).floatValue();
                barData.high = Float.valueOf(stringArray[2]).floatValue();
                barData.low = Float.valueOf(stringArray[3]).floatValue();
                barData.close = Float.valueOf(stringArray[4]).floatValue();
                barData.volume = Float.valueOf(stringArray[5]).floatValue();
                barData.value = Float.valueOf(stringArray[6]).floatValue();
                objectArrayList.add((Object)barData);
            }
        }
        catch (Exception exception) {
            throw new Exception(String.format("Cannot load file. Error on line %d", n), exception);
        }
        int n2 = objectArrayList.size();
        this.indicators.o = new float[n2];
        this.indicators.h = new float[n2];
        this.indicators.l = new float[n2];
        this.indicators.c = new float[n2];
        for (int i = 0; i < n2; ++i) {
            barData = (BarData)objectArrayList.get(i);
            this.indicators.o[i] = barData.open;
            this.indicators.h[i] = barData.high;
            this.indicators.l[i] = barData.low;
            this.indicators.c[i] = barData.close;
        }
        return objectArrayList;
    }

    private int compare(String string, SettingsMap settingsMap, ObjectArrayList<BarData> objectArrayList) throws Exception {
        int n = 0;
        float[][] fArray = this.indicators.calculate(string, settingsMap, null, settingsMap.getInt("Shift"), 0, "TEST");
        if (fArray == null) {
            throw new Exception("outputs is null");
        }
        for (int i = 150; i < fArray[0].length; ++i) {
            double d = ((BarData)objectArrayList.get((int)i)).value;
            double d2 = fArray[0][i];
            if (SQUtils.round((double)d, (int)4) == SQUtils.round((double)d2, (int)4) || !(Math.abs(d - d2) > 2.0E-4)) continue;
            System.out.println(String.format("%s values don't match - (AMB) %f <> (SQX) %f", SQTime.toDateString((long)((BarData)objectArrayList.get((int)i)).time), d, d2));
            ++n;
        }
        return n;
    }
}

