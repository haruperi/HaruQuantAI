/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.IParametersHelperModifier;
import com.strategyquant.tradinglib.NegatersList;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.Variables;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ParametersHelper {
    public static final Logger Log = LoggerFactory.getLogger((String)"ParametersHelper");

    public static void setParameterValue(IBlock iBlock, String string, Object object) throws BlockDefinitionException {
        Class<?> clazz = iBlock.getClass();
        for (Field field : clazz.getFields()) {
            for (Annotation annotation : field.getAnnotations()) {
                if (!(annotation instanceof Parameter) || !field.getName().equals(string)) continue;
                try {
                    field.set(iBlock, object);
                }
                catch (IllegalAccessException | IllegalArgumentException exception) {
                    throw new BlockDefinitionException("Exception setting value of parameter '" + string + "' found!", exception);
                }
            }
        }
    }

    public static Object getParameterValue(IBlock iBlock, String string) throws BlockDefinitionException {
        Class<?> clazz = iBlock.getClass();
        for (Field field : clazz.getFields()) {
            for (Annotation annotation : field.getAnnotations()) {
                if (!(annotation instanceof Parameter) || !field.getName().equals(string)) continue;
                try {
                    return field.get(iBlock);
                }
                catch (IllegalAccessException | IllegalArgumentException exception) {
                    throw new BlockDefinitionException("Exception getting value of parameter '" + string + "' found!", exception);
                }
            }
        }
        throw new BlockDefinitionException("Exception - No parameter '" + string + "' found in block " + clazz.getSimpleName() + " !");
    }

    public static ArrayList<String> getParameters(IBlock iBlock) {
        ArrayList<String> arrayList = new ArrayList<String>();
        Class<?> clazz = iBlock.getClass();
        for (Field field : clazz.getFields()) {
            for (Annotation annotation : field.getAnnotations()) {
                if (!(annotation instanceof Parameter)) continue;
                arrayList.add(field.getName());
            }
        }
        return arrayList;
    }

    public static void setFieldValue(IBlock iBlock, String string, Object object) throws BlockDefinitionException {
        Class<?> clazz = iBlock.getClass();
        for (Field field : clazz.getFields()) {
            if (!field.getName().equals(string)) continue;
            try {
                field.set(iBlock, object);
            }
            catch (IllegalAccessException | IllegalArgumentException exception) {
                throw new BlockDefinitionException("Exception setting value of parameter '" + string + "' found!", exception);
            }
        }
    }

    public static Object getFieldValue(IBlock iBlock, String string) throws BlockDefinitionException {
        Class<?> clazz = iBlock.getClass();
        for (Field field : clazz.getFields()) {
            if (!field.getName().equals(string)) continue;
            try {
                return field.get(iBlock);
            }
            catch (IllegalAccessException | IllegalArgumentException exception) {
                throw new BlockDefinitionException("Exception getting value of parameter '" + string + "' found!", exception);
            }
        }
        throw new BlockDefinitionException("Exception - No parameter '" + string + "' found!");
    }

    public static void copyParametersFromBlockToBlock(IBlock iBlock, IBlock iBlock2, IParametersHelperModifier iParametersHelperModifier) throws BlockDefinitionException {
        ArrayList<Field> arrayList = new ArrayList<Field>();
        Class<?> clazz = iBlock2.getClass();
        for (Field field : clazz.getFields()) {
            for (Annotation annotation : field.getAnnotations()) {
                if (!(annotation instanceof Parameter)) continue;
                arrayList.add(field);
            }
        }
        clazz = iBlock.getClass();
        for (Field field : clazz.getFields()) {
            String string = field.getName();
            block5: for (Annotation annotation : field.getAnnotations()) {
                if (!(annotation instanceof Parameter)) continue;
                try {
                    Object object = iParametersHelperModifier.modifyParameterValue(field.getName(), field.get(iBlock));
                    for (int i = 0; i < arrayList.size(); ++i) {
                        Variable variable;
                        Variables variables;
                        Field field2 = (Field)arrayList.get(i);
                        if (!field2.getName().equals(string)) continue;
                        field2.set(iBlock2, object);
                        StrategyBase strategyBase = iBlock.getStrategy();
                        if (strategyBase == null || (variables = strategyBase.variables()) == null || (variable = variables.getByField(iBlock, string)) == null) continue block5;
                        variable.registerAttachedField(iBlock2, field);
                        continue block5;
                    }
                }
                catch (IllegalAccessException | IllegalArgumentException exception) {
                    throw new BlockDefinitionException("Exception getting value of parameter '" + field.getName() + "' found!", exception);
                }
            }
        }
    }

    public static void negateParametersInClonedBlock(IBlock iBlock, IBlock iBlock2, final NegatersList negatersList, final StrategyBase strategyBase) throws BlockDefinitionException {
        ParametersHelper.copyParametersFromBlockToBlock(iBlock, iBlock2, new IParametersHelperModifier(){

            @Override
            public Object modifyParameterValue(String string, Object object) throws BlockDefinitionException {
                if (object instanceof IBlock) {
                    return negatersList.negate((IBlock)object, strategyBase);
                }
                return object;
            }
        });
    }

    public static void negateDataSeries(IBlock iBlock, IBlock iBlock2) {
        int n = ParametersHelper.getField(iBlock, "ComputedFrom");
        int n2 = -1;
        if (n == 2) {
            n2 = 3;
        }
        if (n == 3) {
            n2 = 2;
        }
        if (n > 0) {
            if (n2 != -1) {
                ParametersHelper.setField(iBlock2, "ComputedFrom", n2);
            }
            return;
        }
        n = iBlock.getCustomData("InputComputedFrom");
        n2 = -1;
        if (n == 2) {
            n2 = 3;
        }
        if (n == 3) {
            n2 = 2;
        }
        if (n2 != -1) {
            iBlock2.setCustomData("InputComputedFrom", n2);
            return;
        }
        n = iBlock.getCustomData("ChartComputedFrom");
        if (n == 2) {
            n2 = 3;
        }
        if (n == 3) {
            n2 = 2;
        }
        if (n2 != -1) {
            iBlock2.setCustomData("ChartComputedFrom", n2);
        }
    }

    public static int getField(Object object, String string) {
        Class<?> clazz = object.getClass();
        try {
            Field field = clazz.getDeclaredField(string);
            Object object2 = field.get(object);
            return (Integer)object2;
        }
        catch (Exception exception) {
            return Integer.MIN_VALUE;
        }
    }

    public static void setField(Object object, String string, int n) {
        Class<?> clazz = object.getClass();
        try {
            Field field = clazz.getDeclaredField(string);
            field.set(object, n);
        }
        catch (Exception exception) {
            // empty catch block
        }
    }
}

