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
import com.strategyquant.tradinglib.Negater;
import com.strategyquant.tradinglib.NegatersList;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.generator.NegaterComparatorByOrder;
import java.util.Collections;
import java.util.Comparator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Negaters
implements ICustomClasses {
    public static final Logger Log = LoggerFactory.getLogger((String)"Negaters");
    private static Negaters instance;
    private NegatersList negaters = new NegatersList();
    private Comparator<Negater> comparatorByOrder;

    public Negaters() {
        CustomClassesReg.add((ICustomClasses)this);
        this.comparatorByOrder = new NegaterComparatorByOrder();
        this.initClassesMap("Negater");
    }

    public static void init() throws Exception {
        if (instance != null) {
            throw new Exception("Negaters.init() called more than once!");
        }
        instance = new Negaters();
    }

    private void initClassesMap(String string) {
        try {
            this.negaters.clear();
            CustomClassesLoader customClassesLoader = new CustomClassesLoader(string);
            while (customClassesLoader.hasNext()) {
                String string2 = customClassesLoader.getNext();
                Object object = customClassesLoader.createInstance(string2);
                if (object instanceof Negater) {
                    Negater negater = (Negater)object;
                    this.negaters.add(negater);
                    continue;
                }
                if (!Log.isDebugEnabled()) continue;
                Log.debug("Class: " + string2 + " is not an instance of Negater");
            }
            this.sortClasses();
        }
        catch (Exception exception) {
            Log.error("An error occured while loading custom classes.", (Throwable)exception);
        }
    }

    private void sortClasses() {
        Collections.sort(this.negaters, this.comparatorByOrder);
    }

    public static NegatersList list() throws GenerateException {
        if (instance == null) {
            throw new GenerateException("You have to call Negaters.init() on program startup!");
        }
        return Negaters.instance.negaters;
    }

    public void reload() throws Exception {
        this.initClassesMap("Negater");
    }
}

