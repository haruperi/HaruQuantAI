/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.atm.ATMGenerateConfig;
import com.strategyquant.tradinglib.generator.StrategyGenerator;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.io.IOException;
import java.util.ArrayList;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyGeneratorCache {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategyGeneratorCache");
    private static Int2ObjectOpenHashMap<ArrayList<StrategyGenerator>> mapGenerators = new Int2ObjectOpenHashMap();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static StrategyGenerator getGenerator(int n, IRandomGenerator iRandomGenerator, Element element, Element element2, SettingsMap settingsMap, ATMGenerateConfig aTMGenerateConfig) throws JDOMException, IOException, Exception {
        Int2ObjectOpenHashMap<ArrayList<StrategyGenerator>> int2ObjectOpenHashMap = mapGenerators;
        synchronized (int2ObjectOpenHashMap) {
            ArrayList arrayList;
            StrategyGenerator strategyGenerator = null;
            boolean bl = false;
            if (mapGenerators.containsKey(n)) {
                arrayList = (ArrayList)mapGenerators.get(n);
                int n2 = 0;
                for (int i = 0; i < arrayList.size(); ++i) {
                    StrategyGenerator strategyGenerator2 = (StrategyGenerator)arrayList.get(i);
                    if (strategyGenerator2.isFree()) {
                        strategyGenerator = strategyGenerator2;
                        strategyGenerator2.setRandomGenerator(iRandomGenerator);
                        if (Log.isDebugEnabled()) {
                            Log.debug(String.format("Found existing StrategyGenerator with hash %d - %s", n, strategyGenerator2.toString()));
                        }
                        break;
                    }
                    ++n2;
                }
            } else {
                arrayList = new ArrayList();
                bl = true;
            }
            if (strategyGenerator == null) {
                strategyGenerator = new StrategyGenerator(element, element2, iRandomGenerator, settingsMap, aTMGenerateConfig);
                arrayList.add(strategyGenerator);
                if (bl) {
                    mapGenerators.put(n, (Object)arrayList);
                }
                if (Log.isDebugEnabled()) {
                    Log.debug(String.format("New StrategyGenerator created with hash: %d -%s", n, strategyGenerator.toString()));
                }
            }
            strategyGenerator.setUsed();
            return strategyGenerator;
        }
    }

    public static int getHash(Element element, Element element2, SettingsMap settingsMap, ATMGenerateConfig aTMGenerateConfig) {
        String string = XMLUtil.xmlToStringRaw((Element)element);
        String string2 = XMLUtil.xmlToStringRaw((Element)element2);
        int n = string.hashCode();
        int n2 = string2.hashCode();
        int n3 = settingsMap.hashCode();
        int n4 = n + n2 + n3;
        if (aTMGenerateConfig != null) {
            n4 += aTMGenerateConfig.getHash();
        }
        return n4;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void clearTooFullCache() {
        Int2ObjectOpenHashMap<ArrayList<StrategyGenerator>> int2ObjectOpenHashMap = mapGenerators;
        synchronized (int2ObjectOpenHashMap) {
            if (mapGenerators.size() > 50) {
                mapGenerators.clear();
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void clear() {
        Int2ObjectOpenHashMap<ArrayList<StrategyGenerator>> int2ObjectOpenHashMap = mapGenerators;
        synchronized (int2ObjectOpenHashMap) {
            mapGenerators.clear();
        }
    }
}

