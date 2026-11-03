/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.snippets.CustomClasses
 *  com.strategyquant.lib.snippets.NonexistingCustomClassException
 */
package com.strategyquant.tradinglib.riskmanagement;

import com.strategyquant.lib.snippets.CustomClasses;
import com.strategyquant.lib.snippets.NonexistingCustomClassException;
import com.strategyquant.tradinglib.RiskManagementMethod;

public class RiskManagementMethodsList
extends CustomClasses<RiskManagementMethod> {
    private static RiskManagementMethodsList instance;

    public static RiskManagementMethodsList get() {
        if (instance == null) {
            instance = new RiskManagementMethodsList();
        }
        return instance;
    }

    private RiskManagementMethodsList() {
        this.setDirName("RiskManagement");
        this.setExpectedClassType(RiskManagementMethod.class);
        this.loadAvailableClasses();
    }

    public static RiskManagementMethod create(String string, Object ... objectArray) throws NonexistingCustomClassException {
        return RiskManagementMethodsList.get()._create(string, objectArray);
    }

    private RiskManagementMethod _create(String string, Object[] objectArray) throws NonexistingCustomClassException {
        for (RiskManagementMethod riskManagementMethod : this.getAvailableClasses()) {
            if (!riskManagementMethod.getClass().getSimpleName().equals(string)) continue;
            try {
                return (RiskManagementMethod)riskManagementMethod.newInstance(objectArray);
            }
            catch (Exception exception) {
                Log.error("Cannot create new instance", (Throwable)exception);
            }
        }
        throw new NonexistingCustomClassException(string);
    }
}

