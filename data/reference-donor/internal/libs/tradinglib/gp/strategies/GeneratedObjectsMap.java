/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.utils.SQUUID
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.utils.SQUUID;
import com.strategyquant.tradinglib.gp.strategies.GeneratedObject;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Element;

public class GeneratedObjectsMap {
    private Int2ObjectOpenHashMap<GeneratedObject> generatedObjectsMap = new Int2ObjectOpenHashMap();
    private ArrayList<GeneratedObject> generatedObjectsArray = new ArrayList();

    public GeneratedObject get(int n) {
        if (n >= this.size()) {
            throw new IllegalArgumentException("Index must be smaller than size!");
        }
        return this.generatedObjectsArray.get(n);
    }

    public int size() {
        return this.generatedObjectsArray.size();
    }

    public void addItem(Element element) {
        int n = SQUUID.randomUUID().hashCode();
        String string = Integer.toString(n);
        element.setAttribute("gid", string);
        GeneratedObject generatedObject = new GeneratedObject(n, element);
        this.generatedObjectsMap.put(n, (Object)generatedObject);
        this.generatedObjectsArray.add(generatedObject);
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string2 = element2.getAttributeValue("generated");
            String string3 = element2.getAttributeValue("type");
            if (string3 != null && string3.equals("data") || string2 != null && !string2.equals("random")) continue;
            int n2 = SQUUID.randomUUID().hashCode();
            String string4 = Integer.toString(n2);
            element2.setAttribute("gid", string4);
            this.addParameter(n2, element2, n);
        }
    }

    public void addParam(Element element) {
        String string = element.getAttributeValue("type");
        if (string.equals("data")) {
            return;
        }
        String string2 = SQUUID.randomUUID();
        int n = string2.hashCode();
        element.setAttribute("gid", string2);
        this.addParameter(n, element, 0);
    }

    private void addParameter(int n, Element element, int n2) {
        GeneratedObject generatedObject = new GeneratedObject(n, element, n2);
        this.generatedObjectsMap.put(n, (Object)generatedObject);
        this.generatedObjectsArray.add(generatedObject);
    }

    public void print() {
        System.out.println("--------------------------------------");
        System.out.println(" GENERATED OBJ MAP");
        System.out.println("--------------------------------------");
        for (int i = 0; i < this.size(); ++i) {
            this.get(i).print();
        }
        System.out.println("--------------------------------------");
    }

    public void clear() {
        this.generatedObjectsMap.clear();
        this.generatedObjectsArray.clear();
    }
}

