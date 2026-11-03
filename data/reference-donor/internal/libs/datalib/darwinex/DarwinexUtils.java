/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.longs.Long2ObjectAVLTreeMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.darwinex;

import com.strategyquant.datalib.data.io.VersatileData;
import it.unimi.dsi.fastutil.longs.Long2ObjectAVLTreeMap;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.zip.GZIPInputStream;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DarwinexUtils {
    public static final Logger Log = LoggerFactory.getLogger(DarwinexUtils.class);

    public static void getTickData(File file, Long2ObjectAVLTreeMap<VersatileData> long2ObjectAVLTreeMap, boolean bl) throws Exception {
        if (!file.exists()) {
            return;
        }
        try {
            String string;
            GZIPInputStream gZIPInputStream = new GZIPInputStream(new FileInputStream(file));
            BufferedReader bufferedReader = new BufferedReader(new InputStreamReader((InputStream)gZIPInputStream, StandardCharsets.UTF_8));
            VersatileData versatileData = new VersatileData();
            while ((string = bufferedReader.readLine()) != null) {
                long l;
                String[] stringArray = string.split(",");
                if (stringArray.length != 3) continue;
                String string2 = stringArray[0];
                try {
                    l = Long.valueOf(string2);
                }
                catch (Exception exception) {
                    if (string2.length() > 13) {
                        string2 = string2.substring(0, 13);
                    }
                    l = Long.valueOf(string2);
                }
                double d = Double.parseDouble(stringArray[1]);
                versatileData = (VersatileData)long2ObjectAVLTreeMap.get(l);
                if (versatileData == null) {
                    versatileData = new VersatileData();
                    versatileData.time = l;
                    long2ObjectAVLTreeMap.put(l, (Object)versatileData);
                }
                if (bl) {
                    versatileData.ask = d;
                    continue;
                }
                versatileData.bid = d;
                versatileData.volume = Double.parseDouble(stringArray[2]);
            }
            gZIPInputStream.close();
            bufferedReader.close();
        }
        catch (Exception exception) {
            Log.error("Failed to load data from file: " + file.getAbsolutePath(), (Throwable)exception);
            throw new Exception("Failed to load data from file: " + file.getAbsolutePath(), exception);
        }
    }
}

