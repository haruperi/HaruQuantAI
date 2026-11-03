/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataBinReader
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.data;

import com.strategyquant.datalib.customData.CustomDataBinReader;
import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.data.CustomDataIndyMap;
import it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CustomDataIndyCache {
    private static final Logger Log = LoggerFactory.getLogger(CustomDataIndyCache.class);
    private static Long2ObjectOpenHashMap<CustomDataIndyMap> cache = new Long2ObjectOpenHashMap();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static CustomDataIndyMap getMapForIndy(Element element) {
        Long2ObjectOpenHashMap<CustomDataIndyMap> long2ObjectOpenHashMap = cache;
        synchronized (long2ObjectOpenHashMap) {
            long l;
            String string;
            String string2 = element.getAttributeValue("key");
            if (string2 == null) {
                return null;
            }
            String string3 = CustomDataManager.getCDataIndyId((String)string2);
            if (string3 == null) {
                return null;
            }
            int n = 0;
            Element element2 = XMLUtil.findFirstWithKey((Element)element, (String)"Param", (String)"#Value#");
            if (element2 != null && (string = element2.getText()) != null && !string.equals("")) {
                n = Integer.parseInt(string);
            }
            if (!cache.containsKey(l = SQUtils.longHashCode((String)string3) + (long)n)) {
                return CustomDataIndyCache.loadCustomDataIndy(string3, n);
            }
            return (CustomDataIndyMap)cache.get(l);
        }
    }

    private static CustomDataIndyMap loadCustomDataIndy(String string, int n) {
        CustomDataInfo customDataInfo = CustomDataManager.getDataInfo((String)string);
        if (customDataInfo == null) {
            Log.error("Cannot load data info for {}", (Object)string);
            return null;
        }
        CustomDataIndyMap[] customDataIndyMapArray = new CustomDataIndyMap[customDataInfo.values];
        for (int i = 0; i < customDataInfo.values; ++i) {
            customDataIndyMapArray[i] = new CustomDataIndyMap(string, customDataInfo, i);
        }
        try {
            int n2;
            CustomDataBinReader customDataBinReader = new CustomDataBinReader(customDataInfo);
            customDataBinReader.open();
            while (customDataBinReader.hasNextData()) {
                customDataBinReader.loadData();
                for (n2 = 0; n2 < customDataInfo.values; ++n2) {
                    customDataIndyMapArray[n2].put(customDataBinReader.loadedData.time, customDataBinReader.loadedData.values[n2]);
                }
            }
            for (n2 = 0; n2 < customDataInfo.values; ++n2) {
                long l = SQUtils.longHashCode((String)string) + (long)n2;
                cache.put(l, (Object)customDataIndyMapArray[n2]);
            }
            if (n < 0 || n >= customDataInfo.values) {
                Log.error("Custom Data Indicator {} has only {} values, index {} requested!", new Object[]{string, customDataInfo.values, n});
                return null;
            }
            long l = SQUtils.longHashCode((String)string) + (long)n;
            return (CustomDataIndyMap)cache.get(l);
        }
        catch (Exception exception) {
            Log.error("Cannot load custom indy values for {}->Value{}", (Object)string, (Object)n);
            return null;
        }
    }
}

