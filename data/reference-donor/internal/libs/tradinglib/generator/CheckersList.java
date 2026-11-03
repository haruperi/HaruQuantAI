/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.tradinglib.Checker;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CheckersList
extends ObjectArrayList<Checker> {
    private static final long serialVersionUID = 4262797492784530749L;
    public static final Logger Log = LoggerFactory.getLogger((String)"CheckersList");

    public boolean check(Element element) {
        for (int i = 0; i < this.size(); ++i) {
            Checker checker = (Checker)this.get(i);
            if (checker.check(element)) continue;
            return false;
        }
        return true;
    }
}

