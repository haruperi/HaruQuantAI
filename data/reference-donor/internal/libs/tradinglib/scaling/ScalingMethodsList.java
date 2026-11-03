/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.snippets.CustomClasses
 *  com.strategyquant.lib.snippets.NonexistingCustomClassException
 */
package com.strategyquant.tradinglib.scaling;

import com.strategyquant.lib.snippets.CustomClasses;
import com.strategyquant.lib.snippets.NonexistingCustomClassException;
import com.strategyquant.tradinglib.ScalingMethod;

public class ScalingMethodsList
extends CustomClasses<ScalingMethod> {
    private static ScalingMethodsList instance;

    public static ScalingMethodsList get() {
        if (instance == null) {
            instance = new ScalingMethodsList();
        }
        return instance;
    }

    private ScalingMethodsList() {
        this.setDirName("Trading.Scaling");
        this.setExpectedClassType(ScalingMethod.class);
        this.loadAvailableClasses();
    }

    public static ScalingMethod create(String string, Object ... objectArray) throws NonexistingCustomClassException {
        return ScalingMethodsList.get()._create(string, objectArray);
    }

    private ScalingMethod _create(String string, Object[] objectArray) throws NonexistingCustomClassException {
        for (ScalingMethod scalingMethod : this.getAvailableClasses()) {
            if (!scalingMethod.getClass().getSimpleName().equals(string)) continue;
            try {
                return (ScalingMethod)scalingMethod.newInstance(objectArray);
            }
            catch (Exception exception) {
                Log.error("Cannot create new instance", (Throwable)exception);
            }
        }
        throw new NonexistingCustomClassException(string);
    }
}

