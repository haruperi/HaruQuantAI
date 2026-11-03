/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.ResultsGroup
 */
package com.strategyquant.plugin.Loader.impl.SQ3;

import com.strategyquant.plugin.Loader.impl.SQ3.SQ3FileLoaderOldXml;
import com.strategyquant.tradinglib.ResultsGroup;

public class SQ3FileLoader {
    private SQ3FileLoaderOldXml oldXmlLoader = null;

    public ResultsGroup load(String fileName, boolean exceptionOnMissingInstrument, String missingInstrumentReplacement) throws Exception {
        if (this.oldXmlLoader == null) {
            this.oldXmlLoader = new SQ3FileLoaderOldXml();
        }
        return this.oldXmlLoader.load(fileName, exceptionOnMissingInstrument, missingInstrumentReplacement);
    }
}

