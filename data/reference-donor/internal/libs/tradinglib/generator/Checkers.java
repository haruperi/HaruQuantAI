/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.snippets.CustomClassesLoader
 *  com.strategyquant.lib.snippets.CustomClassesReg
 *  com.strategyquant.lib.snippets.ICustomClasses
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.lib.snippets.CustomClassesLoader;
import com.strategyquant.lib.snippets.CustomClassesReg;
import com.strategyquant.lib.snippets.ICustomClasses;
import com.strategyquant.tradinglib.Checker;
import com.strategyquant.tradinglib.generator.CheckersList;
import com.strategyquant.tradinglib.generator.GenerateException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Checkers
implements ICustomClasses {
    public static final Logger Log = LoggerFactory.getLogger((String)"Checkers");
    private static Checkers instance;
    private CheckersList checkers = new CheckersList();

    public Checkers() {
        CustomClassesReg.add((ICustomClasses)this);
        this.initClassesMap("Checker");
    }

    public static void init() throws Exception {
        if (instance != null) {
            throw new Exception("Checkers.init() called more than once!");
        }
        instance = new Checkers();
    }

    private void initClassesMap(String string) {
        try {
            CustomClassesLoader customClassesLoader = new CustomClassesLoader(string);
            while (customClassesLoader.hasNext()) {
                String string2 = customClassesLoader.getNext();
                Object object = customClassesLoader.createInstance(string2);
                if (object instanceof Checker) {
                    Checker checker = (Checker)object;
                    this.checkers.add(checker);
                    continue;
                }
                if (!Log.isDebugEnabled()) continue;
                Log.debug("Class: " + string2 + " is not an instance of Checker");
            }
        }
        catch (Exception exception) {
            Log.error("An error occured while loading custom classes.", (Throwable)exception);
        }
    }

    public static CheckersList list() throws GenerateException {
        if (instance == null) {
            throw new GenerateException("You have to call Checkers.init() on program startup!");
        }
        return Checkers.instance.checkers;
    }

    public void reload() throws Exception {
        this.initClassesMap("Checker");
    }
}

