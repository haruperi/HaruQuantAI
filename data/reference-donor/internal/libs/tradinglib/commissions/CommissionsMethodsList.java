/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.snippets.CustomClasses
 *  com.strategyquant.lib.snippets.NonexistingCustomClassException
 */
package com.strategyquant.tradinglib.commissions;

import com.strategyquant.lib.snippets.CustomClasses;
import com.strategyquant.lib.snippets.NonexistingCustomClassException;
import com.strategyquant.tradinglib.CommissionsMethod;

public class CommissionsMethodsList
extends CustomClasses<CommissionsMethod> {
    private static CommissionsMethodsList instance;

    public static CommissionsMethodsList get() {
        if (instance == null) {
            instance = new CommissionsMethodsList();
        }
        return instance;
    }

    private CommissionsMethodsList() {
        this.setDirName("Trading.Commissions");
        this.setExpectedClassType(CommissionsMethod.class);
        this.loadAvailableClasses();
    }

    public static CommissionsMethod create(String string, Object ... objectArray) throws NonexistingCustomClassException {
        return CommissionsMethodsList.get()._create(string, objectArray);
    }

    private CommissionsMethod _create(String string, Object[] objectArray) throws NonexistingCustomClassException {
        if (!this.checkClassExists(string)) {
            throw new NonexistingCustomClassException(string);
        }
        try {
            return (CommissionsMethod)((CommissionsMethod)this.findClassByName(string)).newInstance(objectArray);
        }
        catch (Exception exception) {
            Log.error("Cannot create new instance", (Throwable)exception);
            throw new NonexistingCustomClassException(string);
        }
    }
}

