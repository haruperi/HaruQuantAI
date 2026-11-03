/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.settings.IXMLAble
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntIterator
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.results;

import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.settings.IXMLAble;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntIterator;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ResultsMap
implements IXMLAble,
Serializable {
    public static final Logger Log = LoggerFactory.getLogger((String)"ResultsMap");
    private final ArrayList<String> resultKeys = new ArrayList();
    final List<String> unmodifiableResultKeys = Collections.unmodifiableList(this.resultKeys);
    private Int2ObjectOpenHashMap<Result> results = new Int2ObjectOpenHashMap();
    private String mainResultKey = null;
    private ResultsGroup resultsGroup;

    public ResultsMap(ResultsGroup resultsGroup) {
        this.resultsGroup = resultsGroup;
    }

    public ResultsMap clone(ResultsGroup resultsGroup) {
        ResultsMap resultsMap = new ResultsMap(resultsGroup);
        resultsGroup.updated = true;
        resultsMap.resultKeys.addAll(this.resultKeys);
        resultsMap.results.clear();
        IntIterator intIterator = this.results.keySet().iterator();
        while (intIterator.hasNext()) {
            int n = (Integer)intIterator.next();
            Result result = (Result)((Object)this.results.get(n));
            resultsMap.results.put(n, (Object)result.clone(resultsGroup));
        }
        resultsMap.mainResultKey = this.mainResultKey;
        return resultsMap;
    }

    public void removeResult(String string, boolean bl) {
        int n = string.hashCode();
        if (!this.results.containsKey(n)) {
            return;
        }
        Result result = (Result)((Object)this.results.get(n));
        if (bl) {
            result.clear();
        }
        this.resultKeys.remove(string);
        this.results.remove(n);
        if (this.mainResultKey.equals(string)) {
            this.mainResultKey = null;
        }
        this.resultsGroup.updated = true;
    }

    public Result get(String string) {
        if (string == null || string.equals("*")) {
            string = "Portfolio";
        }
        if (this.results.size() == 0) {
            throw new IllegalArgumentException("ResultGroup doesn't contain any results!");
        }
        int n = string.hashCode();
        if (this.resultKeys.contains(string)) {
            return (Result)((Object)this.results.get(n));
        }
        if (string.equals("Portfolio")) {
            if (this.isPortfolio()) {
                return (Result)((Object)this.results.get(n));
            }
            return (Result)((Object)this.results.get(this.getMainResultKey().hashCode()));
        }
        if (this.resultKeys.contains(string = string.replace("/*", ""))) {
            return (Result)((Object)this.results.get(n));
        }
        throw new IllegalArgumentException("ResultGroup doesn't contain result with key '" + string + "'!");
    }

    public void addResult(String string, SettingsMap settingsMap) {
        this.addResult(string, settingsMap, null);
    }

    public void addResult(String string, SettingsMap settingsMap, Result result) {
        Object object;
        int n = string.hashCode();
        if (this.results.containsKey(n)) {
            object = (Result)((Object)this.results.get(n));
            object.clear();
        }
        if (this.mainResultKey == null) {
            this.mainResultKey = string;
        }
        if (result == null) {
            result = new Result(string, this.resultsGroup, settingsMap);
        }
        this.resultKeys.add(string);
        if (string.equals("Portfolio") && this.resultKeys.size() > 1) {
            object = new ArrayList();
            ((ArrayList)object).add("Portfolio");
            for (int i = 0; i < this.resultKeys.size() - 1; ++i) {
                ((ArrayList)object).add(this.resultKeys.get(i));
            }
            this.resultKeys.clear();
            this.resultKeys.addAll((Collection<String>)object);
        }
        this.results.put(n, (Object)result);
        this.resultsGroup.updated = true;
    }

    public boolean hasResult(String string) {
        return this.resultKeys.contains(string);
    }

    public List<String> keys() {
        return this.unmodifiableResultKeys;
    }

    public List<String> additionalMarketKeys() {
        ArrayList<String> arrayList = new ArrayList<String>();
        for (int i = 0; i < this.unmodifiableResultKeys.size(); ++i) {
            String string = this.unmodifiableResultKeys.get(i);
            if (!string.startsWith("AdditionalMarket")) continue;
            arrayList.add(string);
        }
        return arrayList;
    }

    public boolean isPortfolio() {
        return this.resultKeys.contains("Portfolio");
    }

    public Element getXML() {
        Element element = new Element("ResultsMap");
        Element element2 = new Element("Results");
        for (int i = 0; i < this.resultKeys.size(); ++i) {
            String string = this.resultKeys.get(i);
            Result result = (Result)((Object)this.results.get(string.hashCode()));
            Element element3 = result.getXML();
            element2.addContent((Content)element3);
        }
        element.addContent((Content)element2);
        return element;
    }

    public void setFromXML(Element element) {
        this.results.clear();
        this.resultKeys.clear();
        Element element2 = element.getChild("Results");
        if (element2 != null) {
            List list = element2.getChildren("Result");
            for (int i = 0; i < list.size(); ++i) {
                Element element3 = (Element)list.get(i);
                Result result = new Result(this.resultsGroup);
                result.setFromXML(element3);
                String string = result.getResultKey();
                this.results.put(string.hashCode(), (Object)result);
                this.resultKeys.add(string);
            }
        }
        this.resultsGroup.updated = true;
    }

    public void computeAllStats(SettingsMap settingsMap, OutOfSample outOfSample) throws Exception {
        IntIterator intIterator = this.results.keySet().iterator();
        while (intIterator.hasNext()) {
            int n = (Integer)intIterator.next();
            Result result = (Result)((Object)this.results.get(n));
            result.computeAllStats(settingsMap, outOfSample);
        }
    }

    public void clear(boolean bl, boolean bl2) {
        if (this.results != null) {
            IntIterator intIterator = this.results.keySet().iterator();
            while (intIterator.hasNext()) {
                int n = (Integer)intIterator.next();
                Result result = (Result)((Object)this.results.get(n));
                result.clear(bl, bl2);
            }
        }
        this.resultsGroup.updated = true;
    }

    public void clearTempData() {
        if (this.results != null) {
            IntIterator intIterator = this.results.keySet().iterator();
            while (intIterator.hasNext()) {
                int n = (Integer)intIterator.next();
                Result result = (Result)((Object)this.results.get(n));
                result.clear(true, true);
            }
        }
        this.resultsGroup.updated = true;
    }

    public String getMainResultKey() {
        if (this.mainResultKey == null) {
            String string;
            int n;
            if (this.results.size() == 0) {
                throw new IllegalArgumentException("ResultGroup doesn't contain any results!");
            }
            for (n = 0; n < this.results.size(); ++n) {
                string = this.resultKeys.get(n);
                if (!string.startsWith("Main:")) continue;
                this.mainResultKey = string;
                break;
            }
            if (this.mainResultKey == null) {
                for (n = 0; n < this.results.size(); ++n) {
                    Result result;
                    string = this.resultKeys.get(n);
                    if (string.startsWith("Portfolio") || string.startsWith("AdditionalMarket") || string.startsWith("CrossCheck") || (result = (Result)((Object)this.results.get(string.hashCode()))).isSpecial()) continue;
                    this.mainResultKey = string;
                    break;
                }
            }
            if (this.mainResultKey == null) {
                this.mainResultKey = this.resultKeys.get(0);
            }
        }
        return this.mainResultKey;
    }

    public void removeUnsavableSettings() {
        IntIterator intIterator = this.results.keySet().iterator();
        while (intIterator.hasNext()) {
            int n = (Integer)intIterator.next();
            Result result = (Result)((Object)this.results.get(n));
            result.removeUnsavableSettings();
        }
        this.resultsGroup.updated = true;
    }

    public int size() {
        return this.resultKeys.size();
    }
}

