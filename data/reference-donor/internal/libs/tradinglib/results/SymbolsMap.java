/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.settings.IXMLAble
 *  com.strategyquant.lib.utils.ISQCloneable
 *  org.jdom2.Content
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.results;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.results.SymbolInfo;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import org.jdom2.Content;
import org.jdom2.Element;

public class SymbolsMap
implements IXMLAble,
Serializable,
ISQCloneable<SymbolsMap> {
    private ArrayList<SymbolInfo> aSymbolInfo = new ArrayList();
    private ArrayList<String> aSymbols = new ArrayList();
    private HashMap<String, Integer> symbolIndex = new HashMap();
    private HashMap<Integer, Integer> symbolHashIndex = new HashMap();

    public synchronized void add(String string, String string2, InstrumentInfo instrumentInfo) {
        if (!this.contains(string)) {
            this.aSymbolInfo.add(new SymbolInfo(string, string2, instrumentInfo));
            this.aSymbols.add(string);
            this.symbolIndex.put(string, this.aSymbolInfo.size() - 1);
            this.symbolHashIndex.put(string.hashCode(), this.aSymbolInfo.size() - 1);
        }
    }

    public boolean contains(String string) {
        return this.symbolIndex.containsKey(string);
    }

    public ArrayList<String> list() {
        return this.aSymbols;
    }

    public SymbolInfo get(String string) {
        if (!this.contains(string)) {
            return null;
        }
        return this.aSymbolInfo.get(this.symbolIndex.get(string));
    }

    public SymbolInfo get(int n) {
        if (!this.symbolHashIndex.containsKey(n)) {
            return null;
        }
        return this.aSymbolInfo.get(this.symbolHashIndex.get(n));
    }

    public void add(SymbolsMap symbolsMap) {
        for (String string : symbolsMap.list()) {
            SymbolInfo symbolInfo = symbolsMap.get(string);
            this.add(symbolInfo.Symbol(), symbolInfo.Instrument(), symbolInfo.InstrumentInfo());
        }
    }

    public Element getXML() {
        Element element = new Element("SymbolsMap");
        for (String string : this.symbolIndex.keySet()) {
            SymbolInfo symbolInfo = this.get(string);
            InstrumentInfo instrumentInfo = null;
            if (symbolInfo == null) continue;
            instrumentInfo = symbolInfo.InstrumentInfo();
            Element element2 = new Element("SymbolInfo");
            element2.setAttribute("symbolName", string);
            if (symbolInfo.Instrument() != null) {
                element2.setAttribute("instrumentName", symbolInfo.Instrument());
            }
            if (instrumentInfo != null) {
                Element element3 = instrumentInfo.getXML();
                element2.addContent((Content)element3);
            }
            element.addContent((Content)element2);
        }
        return element;
    }

    public void setFromXML(Element element) {
        this.aSymbolInfo.clear();
        this.aSymbols.clear();
        this.symbolIndex.clear();
        this.symbolHashIndex.clear();
        for (Element element2 : element.getChildren("SymbolInfo")) {
            String string = element2.getAttributeValue("symbolName").intern();
            String string2 = element2.getAttributeValue("instrumentName").intern();
            Element element3 = element2.getChild("InstrumentInfo");
            if (element3 == null) continue;
            InstrumentInfo instrumentInfo = new InstrumentInfo();
            instrumentInfo.setFromXML(element3);
            this.add(string, string2, instrumentInfo);
        }
    }

    public SymbolsMap getClone() throws Exception {
        SymbolsMap symbolsMap = new SymbolsMap();
        for (SymbolInfo symbolInfo : this.aSymbolInfo) {
            symbolsMap.aSymbolInfo.add(symbolInfo.getClone());
        }
        symbolsMap.aSymbols.addAll(this.aSymbols);
        symbolsMap.symbolHashIndex.putAll(this.symbolHashIndex);
        symbolsMap.symbolIndex.putAll(this.symbolIndex);
        return symbolsMap;
    }

    public InstrumentInfo getDefaultInstrumentInfo() {
        if (this.aSymbolInfo.size() == 1) {
            return this.aSymbolInfo.get(0).InstrumentInfo();
        }
        for (SymbolInfo symbolInfo : this.aSymbolInfo) {
            if (!DataManager.isGroupAlias((String)symbolInfo.Symbol())) continue;
            return symbolInfo.InstrumentInfo();
        }
        return null;
    }
}

