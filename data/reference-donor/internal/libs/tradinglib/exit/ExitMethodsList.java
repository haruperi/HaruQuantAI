/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.snippets.CustomClasses
 *  com.strategyquant.lib.snippets.NonexistingCustomClassException
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.exit;

import com.strategyquant.lib.snippets.CustomClasses;
import com.strategyquant.lib.snippets.NonexistingCustomClassException;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.ExitMethod;
import com.strategyquant.tradinglib.StrategyBase;
import java.util.ArrayList;
import org.jdom2.Element;

public class ExitMethodsList
extends CustomClasses<ExitMethod> {
    private static ExitMethodsList instance;

    public static ExitMethodsList get() {
        if (instance == null) {
            instance = new ExitMethodsList();
        }
        return instance;
    }

    private ExitMethodsList() {
        this.setDirName("ExitMethod");
        this.setExpectedClassType(ExitMethod.class);
        this.loadAvailableClasses();
    }

    private static ExitMethod getObject(String string, Object ... objectArray) throws NonexistingCustomClassException {
        return ExitMethodsList.get()._getObject(string, objectArray);
    }

    private ExitMethod _getObject(String string, Object[] objectArray) throws NonexistingCustomClassException {
        for (ExitMethod exitMethod : this.getAvailableClasses()) {
            if (!exitMethod.getClass().getSimpleName().equals(string)) continue;
            try {
                return exitMethod;
            }
            catch (Exception exception) {
                Log.error("Cannot create new instance", (Throwable)exception);
            }
        }
        throw new NonexistingCustomClassException(string);
    }

    public static ExitMethod getExitMethodObject(String string, StrategyBase strategyBase, ArrayList<Element> arrayList) throws BlockDefinitionException {
        ExitMethod exitMethod;
        try {
            exitMethod = ExitMethodsList.getObject(string, new Object[0]);
        }
        catch (NonexistingCustomClassException nonexistingCustomClassException) {
            throw new BlockDefinitionException(String.format("Cannot create ExitMethod for snippet '%s'", string), (Exception)((Object)nonexistingCustomClassException));
        }
        exitMethod = exitMethod.newInstance(strategyBase, arrayList);
        return exitMethod;
    }
}

