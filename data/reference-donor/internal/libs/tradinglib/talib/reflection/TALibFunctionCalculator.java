/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.tictactec.ta.lib.CoreAnnotated
 *  com.tictactec.ta.lib.MAType
 *  com.tictactec.ta.lib.MInteger
 *  com.tictactec.ta.lib.meta.annotation.InputParameterType
 *  com.tictactec.ta.lib.meta.annotation.OptInputParameterType
 *  com.tictactec.ta.lib.meta.annotation.OutputParameterType
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 */
package com.strategyquant.tradinglib.talib.reflection;

import com.strategyquant.tradinglib.engine.stockpicker.data.BarData;
import com.strategyquant.tradinglib.talib.reflection.DoubleArray;
import com.strategyquant.tradinglib.talib.reflection.TALibConst;
import com.strategyquant.tradinglib.talib.reflection.TALibFunction;
import com.tictactec.ta.lib.CoreAnnotated;
import com.tictactec.ta.lib.MAType;
import com.tictactec.ta.lib.MInteger;
import com.tictactec.ta.lib.meta.annotation.InputParameterType;
import com.tictactec.ta.lib.meta.annotation.OptInputParameterType;
import com.tictactec.ta.lib.meta.annotation.OutputParameterType;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;

public class TALibFunctionCalculator {
    private TALibFunction TALibFunction;
    private ObjectArrayList<BarData> bars;

    public TALibFunctionCalculator(TALibFunction tALibFunction, ObjectArrayList<BarData> objectArrayList) {
        this.TALibFunction = tALibFunction;
        this.bars = objectArrayList;
    }

    /*
     * WARNING - void declaration
     */
    public void calculate(double ... dArray) {
        int mInteger;
        int n;
        Object[] objectArray;
        ArrayList<Integer> arrayList = new ArrayList<Integer>();
        int n3 = 0;
        for (TALibFunction.Param n4 : this.TALibFunction.getInputs()) {
            if (n4.getType().equals(InputParameterType.TA_Input_Price.name())) {
                objectArray = n4.getName().substring(7, n4.getName().length());
                char[] cArray = objectArray.toCharArray();
                n = cArray.length;
                block23: for (int i = 0; i < n; ++i) {
                    mInteger = cArray[i];
                    switch (mInteger) {
                        case 79: {
                            arrayList.add(TALibConst.OPEN);
                            continue block23;
                        }
                        case 72: {
                            arrayList.add(TALibConst.HIGH);
                            continue block23;
                        }
                        case 76: {
                            arrayList.add(TALibConst.LOW);
                            continue block23;
                        }
                        case 67: {
                            arrayList.add(TALibConst.CLOSE);
                            continue block23;
                        }
                        case 86: {
                            arrayList.add(TALibConst.VOLUME);
                        }
                    }
                }
                continue;
            }
            if (!n4.getType().equals(InputParameterType.TA_Input_Real.name())) continue;
            arrayList.add((int)dArray[n3++]);
        }
        double[][] dArrayArray = new double[arrayList.size()][];
        Object[] objectArray2 = new Object[this.TALibFunction.getOptInputs().length];
        Object[] objectArray3 = new Object[this.TALibFunction.getOutputs().length];
        int n2 = 0;
        for (TALibFunction.Param n5 : this.TALibFunction.getOptInputs()) {
            if (n5.getType().equals(OptInputParameterType.TA_OptInput_IntegerRange.name()) || n5.getType().equals(OptInputParameterType.TA_OptInput_IntegerList.name())) {
                objectArray2[n2++] = (int)dArray[n3++];
                continue;
            }
            if (!n5.getType().equals(OptInputParameterType.TA_OptInput_RealRange.name()) && !n5.getType().equals(OptInputParameterType.TA_OptInput_RealList.name())) continue;
            objectArray2[n2++] = dArray[n3++];
        }
        objectArray = arrayList.toArray(new Integer[arrayList.size()]);
        DoubleArray doubleArray = new DoubleArray(this.bars, (Integer[])objectArray);
        n = 0;
        int n4 = doubleArray.get((Integer)objectArray[0]).length - 1;
        for (mInteger = 0; mInteger < dArrayArray.length; ++mInteger) {
            dArrayArray[mInteger] = doubleArray.get((Integer)objectArray[mInteger]);
        }
        for (mInteger = 0; mInteger < objectArray3.length; ++mInteger) {
            objectArray3[mInteger] = this.TALibFunction.getOutputs()[mInteger].getType().equals(OutputParameterType.TA_Output_Integer.toString()) ? (Object)new int[n4 + 1] : (Object)new double[n4 + 1];
        }
        MInteger mInteger2 = new MInteger();
        MInteger mInteger3 = new MInteger();
        Object[] objectArray4 = new Object[dArrayArray.length + objectArray3.length + objectArray2.length + 4];
        int n5 = 0;
        objectArray4[n5++] = n;
        objectArray4[n5++] = n4;
        for (double[] dArray2 : dArrayArray) {
            objectArray4[n5++] = dArray2;
        }
        boolean bl = false;
        for (Object object : objectArray2) {
            void var16_28;
            Object object2 = this.TALibFunction.getOptInputs()[var16_28];
            if (((TALibFunction.Param)object2).getType().equals(OptInputParameterType.TA_OptInput_IntegerList.toString()) || ((TALibFunction.Param)object2).getType().equals(OptInputParameterType.TA_OptInput_IntegerRange.toString())) {
                int n6 = (Integer)object;
                if (((TALibFunction.Param)object2).getName().equals("optInMAType")) {
                    switch (n6) {
                        case 0: {
                            objectArray4[n5++] = MAType.Sma;
                            break;
                        }
                        case 1: {
                            objectArray4[n5++] = MAType.Ema;
                            break;
                        }
                        case 2: {
                            objectArray4[n5++] = MAType.Wma;
                            break;
                        }
                        case 3: {
                            objectArray4[n5++] = MAType.Dema;
                            break;
                        }
                        case 4: {
                            objectArray4[n5++] = MAType.Tema;
                            break;
                        }
                        case 5: {
                            objectArray4[n5++] = MAType.Trima;
                            break;
                        }
                        case 6: {
                            objectArray4[n5++] = MAType.Kama;
                            break;
                        }
                        case 7: {
                            objectArray4[n5++] = MAType.Mama;
                            break;
                        }
                        case 8: {
                            objectArray4[n5++] = MAType.T3;
                        }
                    }
                } else {
                    objectArray4[n5++] = n6;
                }
            } else {
                objectArray4[n5++] = object;
            }
            ++var16_28;
        }
        objectArray4[n5++] = mInteger2;
        objectArray4[n5++] = mInteger3;
        boolean bl2 = false;
        for (Object object2 : objectArray3) {
            objectArray4[n5++] = object2;
        }
        try {
            this.TALibFunction.getTalibMethod().invoke((Object)new CoreAnnotated(), objectArray4);
        }
        catch (IllegalAccessException invocationTargetException) {
            invocationTargetException.printStackTrace();
        }
        catch (IllegalArgumentException n9) {
            n9.printStackTrace();
        }
        catch (InvocationTargetException invocationTargetException) {
            invocationTargetException.printStackTrace();
        }
        int n7 = 0;
        for (Object object : objectArray3) {
            for (double d : (double[])object) {
                System.out.println(d);
            }
            ++n7;
        }
    }
}

