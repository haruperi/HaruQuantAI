/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.tictactec.ta.lib.meta.annotation.FuncInfo
 *  com.tictactec.ta.lib.meta.annotation.InputParameterInfo
 *  com.tictactec.ta.lib.meta.annotation.IntegerList
 *  com.tictactec.ta.lib.meta.annotation.IntegerRange
 *  com.tictactec.ta.lib.meta.annotation.OptInputParameterInfo
 *  com.tictactec.ta.lib.meta.annotation.OutputParameterInfo
 *  com.tictactec.ta.lib.meta.annotation.RealRange
 */
package com.strategyquant.tradinglib.talib.reflection;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.talib.reflection.TALibFunction;
import com.tictactec.ta.lib.meta.annotation.FuncInfo;
import com.tictactec.ta.lib.meta.annotation.InputParameterInfo;
import com.tictactec.ta.lib.meta.annotation.IntegerList;
import com.tictactec.ta.lib.meta.annotation.IntegerRange;
import com.tictactec.ta.lib.meta.annotation.OptInputParameterInfo;
import com.tictactec.ta.lib.meta.annotation.OutputParameterInfo;
import com.tictactec.ta.lib.meta.annotation.RealRange;
import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.util.ArrayList;

public class TALibFunctions {
    private static TALibFunction[] talibFunctions = TALibFunctions.loadFunctions();

    public static TALibFunction getFunction(String string) {
        for (TALibFunction tALibFunction : talibFunctions) {
            if (!tALibFunction.getName().equals(string)) continue;
            return tALibFunction;
        }
        throw new RuntimeException(L.t((String)"No such function %s", (Object[])new Object[]{string}));
    }

    public static TALibFunction[] getTALibFunctions() {
        return talibFunctions;
    }

    private static TALibFunction[] loadFunctions() {
        Method[] methodArray = null;
        try {
            methodArray = TALibFunctions.class.getClassLoader().loadClass("com.tictactec.ta.lib.CoreAnnotated").getMethods();
        }
        catch (SecurityException securityException) {
            securityException.printStackTrace();
        }
        catch (ClassNotFoundException classNotFoundException) {
            classNotFoundException.printStackTrace();
        }
        ArrayList<TALibFunction> arrayList = new ArrayList<TALibFunction>();
        for (Method method : methodArray) {
            Annotation[][] annotationArray;
            FuncInfo funcInfo = method.getAnnotation(FuncInfo.class);
            if (funcInfo == null) continue;
            TALibFunction tALibFunction = new TALibFunction(method, funcInfo.name(), funcInfo.nbInput(), funcInfo.nbOptInput(), funcInfo.nbOutput());
            arrayList.add(tALibFunction);
            Annotation[][] annotationArray2 = annotationArray = method.getParameterAnnotations();
            int n = annotationArray2.length;
            for (int i = 0; i < n; ++i) {
                Annotation[] annotationArray3;
                for (Annotation annotation : annotationArray3 = annotationArray2[i]) {
                    OutputParameterInfo outputParameterInfo;
                    if (annotation instanceof OutputParameterInfo) {
                        outputParameterInfo = (OutputParameterInfo)annotation;
                        tALibFunction.addOutput(new TALibFunction.Param(outputParameterInfo.paramName(), outputParameterInfo.type().name(), outputParameterInfo.flags()));
                        continue;
                    }
                    if (annotation instanceof InputParameterInfo) {
                        outputParameterInfo = (InputParameterInfo)annotation;
                        tALibFunction.addInput(new TALibFunction.Param(outputParameterInfo.paramName(), outputParameterInfo.type().name(), outputParameterInfo.flags()));
                        continue;
                    }
                    if (annotation instanceof OptInputParameterInfo) {
                        outputParameterInfo = (OptInputParameterInfo)annotation;
                        tALibFunction.addOptInput(new TALibFunction.Param(outputParameterInfo.paramName(), outputParameterInfo.type().name(), outputParameterInfo.displayName(), outputParameterInfo.flags()));
                        continue;
                    }
                    if (annotation instanceof IntegerRange) {
                        outputParameterInfo = (IntegerRange)annotation;
                        tALibFunction.addIntegerRange(outputParameterInfo.paramName(), new TALibFunction.IntegerParams(outputParameterInfo.min(), outputParameterInfo.max(), outputParameterInfo.defaultValue(), outputParameterInfo.suggested_start(), outputParameterInfo.suggested_end(), outputParameterInfo.suggested_increment()));
                        continue;
                    }
                    if (annotation instanceof RealRange) {
                        outputParameterInfo = (RealRange)annotation;
                        tALibFunction.addDoubleRange(outputParameterInfo.paramName(), new TALibFunction.DoubleParams(outputParameterInfo.min(), outputParameterInfo.max(), outputParameterInfo.defaultValue(), outputParameterInfo.suggested_start(), outputParameterInfo.suggested_end(), outputParameterInfo.suggested_increment()));
                        continue;
                    }
                    if (!(annotation instanceof IntegerList)) continue;
                    outputParameterInfo = (IntegerList)annotation;
                    tALibFunction.addIntegerRange(outputParameterInfo.paramName(), new TALibFunction.IntegerParams(0, 0, outputParameterInfo.defaultValue(), 0, 0, 0));
                }
            }
        }
        return arrayList.toArray(new TALibFunction[arrayList.size()]);
    }
}

