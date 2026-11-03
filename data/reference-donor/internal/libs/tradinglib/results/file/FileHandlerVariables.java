/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 */
package com.strategyquant.tradinglib.results.file;

import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.file.ILoaderPlugin;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayList;

public class FileHandlerVariables {
    public ResultsGroup loadedResult = null;
    public String loadedFilePath = null;
    public ILoaderPlugin pluginLoaderUsed = null;
    public String loadingErrorMessages = null;
    public Exception lastLoaderExc = null;
    public Int2ObjectOpenHashMap<ArrayList<ILoaderPlugin>> mapLoaders = new Int2ObjectOpenHashMap();
}

