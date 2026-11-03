/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.gp.strategies;

import org.jdom2.Element;

public class NodeElement {
    public Element element;
    public Element elementParent;

    public NodeElement(Element element, Element element2) {
        this.element = element;
        this.elementParent = element2;
    }

    public NodeElement(Element element) {
        this.element = element;
        this.elementParent = element.getParentElement();
    }
}

