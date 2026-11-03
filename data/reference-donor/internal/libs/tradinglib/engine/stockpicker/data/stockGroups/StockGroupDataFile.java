/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  org.nustaq.serialization.FSTObjectInput
 *  org.nustaq.serialization.FSTObjectOutput
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.LoadedStockGroupData;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FilterInputStream;
import java.io.FilterOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import org.nustaq.serialization.FSTObjectInput;
import org.nustaq.serialization.FSTObjectOutput;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StockGroupDataFile {
    public static final Logger Log = LoggerFactory.getLogger(StockGroupDataFile.class);

    public void save(String string, LoadedStockGroupData loadedStockGroupData) throws Exception {
        Log.info(String.format("Saving picker data to cache file '%s'.", string));
        FilterOutputStream filterOutputStream = null;
        File file = null;
        try {
            file = new File(string);
            file.getParentFile().mkdirs();
            filterOutputStream = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(string)));
            FSTObjectOutput fSTObjectOutput = new FSTObjectOutput((OutputStream)filterOutputStream);
            fSTObjectOutput.writeObject((Object)loadedStockGroupData, new Class[]{LoadedStockGroupData.class});
            fSTObjectOutput.close();
        }
        catch (Exception exception) {
            if (file != null) {
                file.delete();
            }
            Log.error(String.format("Error while loading picker data from cache file '%s'.", string), (Throwable)exception);
            throw new Exception(L.t((String)"Error while saving picker data to cache file '%s'. ", (Object[])new Object[]{string}) + exception.getMessage());
        }
        finally {
            if (filterOutputStream != null) {
                try {
                    filterOutputStream.close();
                }
                catch (IOException iOException) {}
            }
        }
    }

    public LoadedStockGroupData load(String string) throws Exception {
        Log.info(String.format("Loading picker data from cache file '%s'.", string));
        FilterInputStream filterInputStream = null;
        LoadedStockGroupData loadedStockGroupData = null;
        try {
            File file = new File(string);
            if (!file.exists()) {
                throw new Exception(L.t((String)"File '%s' doesn't exist.", (Object[])new Object[]{string}));
            }
            filterInputStream = new DataInputStream(new BufferedInputStream(new FileInputStream(string)));
            FSTObjectInput fSTObjectInput = new FSTObjectInput((InputStream)filterInputStream);
            loadedStockGroupData = (LoadedStockGroupData)fSTObjectInput.readObject(new Class[]{LoadedStockGroupData.class});
            fSTObjectInput.close();
        }
        catch (Exception exception) {
            Log.error(String.format("Error while loading picker data from cache file '%s'.", string), (Throwable)exception);
            throw new Exception(L.t((String)"Error while loading picker data from cache file '%s'. ", (Object[])new Object[]{string}) + exception.getMessage());
        }
        finally {
            if (filterInputStream != null) {
                try {
                    filterInputStream.close();
                }
                catch (IOException iOException) {}
            }
        }
        return loadedStockGroupData;
    }
}

