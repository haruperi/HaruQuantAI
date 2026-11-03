/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.generator;

import org.jdom2.Element;

class RandomAndOr {
    public static final int Unset = -1;
    public static final int Random = 1;
    public static final int Copied = 2;
    Element elRnd;
    int id;
    int type;
    public String key;

    public RandomAndOr(Element element) {
        this.elRnd = element;
        this.id = element.getAttributeValue("identification").hashCode();
        this.type = -1;
    }
}

