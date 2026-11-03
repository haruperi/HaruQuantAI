/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.Indicator;
import com.strategyquant.tradinglib.NegatersList;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.debug.Debugger;
import java.lang.reflect.Field;

public abstract class Negater
extends Debugger {
    public abstract IBlock negate(NegatersList var1, IBlock var2, int var3, int var4, StrategyBase var5) throws BlockDefinitionException;

    protected double getOscillatorMiddleValue(IBlock iBlock) throws BlockDefinitionException {
        Indicator indicator = iBlock.getClass().getAnnotation(Indicator.class);
        if (indicator == null) {
            throw new BlockDefinitionException("Block '" + iBlock.getClass().getSimpleName() + "' is not an oscillator");
        }
        return indicator.middleValue();
    }

    protected boolean isOscillatorIndicator(IBlock iBlock) {
        Indicator indicator = iBlock.getClass().getAnnotation(Indicator.class);
        if (indicator != null) {
            return indicator.oscillator();
        }
        return false;
    }

    protected Field getOutputIndexField(IBlock iBlock) {
        Class<?> clazz = iBlock.getClass();
        for (Field field : clazz.getFields()) {
            if (!field.getName().equals("OutputIndex")) continue;
            return field;
        }
        return null;
    }
}

