/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.data.io.columns.DefaultCol;
import java.util.ArrayList;

public class ImportDataInfo {
    public static final int DT_OHLC = 1;
    public static final int DT_TICK = 2;
    public String name = null;
    public String filePath = null;
    public String separator = null;
    public int skipRows;
    public int skipCols;
    public String dateFormat;
    public String timeFormat = null;
    public int rowCount;
    public String uniqImportString = "ABCDEFGH";
    public ArrayList<DefaultCol> columnTypes = new ArrayList();
    public int dataType = -1;
    public String timeframe;
    public int importFileRows;
    public long beginTimeNewFile;
    public long endTimeNewFile;
    public boolean reversedFile = false;
    public boolean hasTwoVolumes = false;
    public int errorHandling = 0;
    public String timezone;
    private String lastAsk = null;
    private String lastBid = null;

    public boolean isMT5TickImport() {
        return this.name != null && this.name.equals("MetaTrader5 Tick Data");
    }

    public void resetLastAskBid() {
        this.lastAsk = null;
        this.lastBid = null;
    }

    public String[] correctMT5TickData(String[] stringArray) {
        String[] stringArray2 = new String[4];
        stringArray2[0] = stringArray[0];
        stringArray2[1] = stringArray[1];
        if (stringArray.length > 2 && !stringArray[2].isBlank()) {
            this.lastBid = stringArray[2];
        }
        if (stringArray.length > 3 && !stringArray[3].isBlank()) {
            this.lastAsk = stringArray[3];
        }
        stringArray2[2] = this.lastBid;
        stringArray2[3] = this.lastAsk;
        if (stringArray2[2] == null || stringArray2[3] == null) {
            return null;
        }
        return stringArray2;
    }
}

