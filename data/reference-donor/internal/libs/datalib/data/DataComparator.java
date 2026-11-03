/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data;

import com.strategyquant.datalib.DataInfo;
import java.util.Comparator;

public class DataComparator
implements Comparator<DataInfo> {
    @Override
    public int compare(DataInfo dataInfo, DataInfo dataInfo2) {
        return dataInfo.symbol.compareToIgnoreCase(dataInfo2.symbol);
    }
}

