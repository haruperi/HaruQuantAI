/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomData
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.datalib.data.io.AbstractDataCsvLoader
 *  com.strategyquant.datalib.data.io.ImportDataInfo
 *  com.strategyquant.datalib.data.io.columns.DefaultCol
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.CustomData.job;

import com.strategyquant.datalib.customData.CustomData;
import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.data.io.AbstractDataCsvLoader;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.datalib.data.io.columns.DefaultCol;
import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.IProgressListener;
import java.util.Arrays;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CustomDataCsvLoader
extends AbstractDataCsvLoader {
    public static final Logger Log = LoggerFactory.getLogger((String)"CustomDataCsvLoader");
    public CustomData loadedData;
    public long fromDate = -1L;
    public long toDate = -1L;

    public CustomDataCsvLoader(IProgressListener listener, CustomDataInfo dataInfo, ImportDataInfo importInfo) {
        this.listener = listener;
        this.importInfo = importInfo;
        this.loadedData = new CustomData(dataInfo.values);
    }

    public boolean readData() throws Exception {
        String line;
        if (this.rows == 0 && this.importInfo.skipRows > 0) {
            for (int i = 0; i < this.importInfo.skipRows; ++i) {
                this.readLine();
            }
        }
        if ((line = this.reader.readLine()) == null || line.equals("")) {
            return false;
        }
        ++this.loadedRows;
        String[] csvColumns = null;
        int dataColumns = this.importInfo.columnTypes.size();
        String[] dataCsvColumns = new String[dataColumns];
        try {
            csvColumns = line.split(this.importInfo.separator);
            if (this.importInfo.skipCols > 0) {
                if (csvColumns.length - this.importInfo.skipCols <= 0) {
                    throw new Exception(L.t((String)"There are less columns than specified in Skip Columns parameter!", (Object[])new Object[0]));
                }
                if (csvColumns.length - this.importInfo.skipCols < dataColumns) {
                    throw new Exception(L.t((String)"There are not enough data columns in the file! Found: %d, Required: %d", (Object[])new Object[]{csvColumns.length - this.importInfo.skipCols, dataColumns}));
                }
                dataCsvColumns = Arrays.copyOfRange(csvColumns, this.importInfo.skipCols, csvColumns.length);
            } else {
                dataCsvColumns = csvColumns;
            }
            Object[] data = this.parseLine(dataCsvColumns, this.importInfo);
            this.parseCustomData(data);
            if (this.loadedData.time == Long.MIN_VALUE) {
                throw new Exception(L.t((String)"Cannot recognize date and time!", (Object[])new Object[0]));
            }
            if (this.loadedData.time > 0L && this.loadedData.time < this.previousTime) {
                if (this.importInfo.errorHandling == 1) {
                    Log.error(String.format("Error parsing on row: %d, line contents: %s, message: %s", this.rows, line, "Invalid time consecution. Each row must have same or latter time than the previous one"));
                } else {
                    throw new Exception("Invalid time consecution. Each row must have same or latter time than the previous one");
                }
            }
            if (this.fromDate == -1L) {
                this.fromDate = this.loadedData.time;
            }
            this.toDate = this.loadedData.time;
            if (this.loadedRows < 100000) {
                this.tfRecognizer.processTime(this.loadedData.time);
            }
            this.previousTime = this.loadedData.time;
            return true;
        }
        catch (Exception ex) {
            Log.error("Error parsing on line: " + this.rows + ", message: " + ex.getMessage(), (Throwable)ex);
            throw new Exception(L.t((String)"Error parsing on line: %d, message: %s", (Object[])new Object[]{this.rows, ex.getMessage()}));
        }
    }

    private void parseCustomData(Object[] data) {
        this.loadedData.reset();
        int valueIndex = 0;
        block4: for (int i = 0; i < this.importInfo.columnTypes.size(); ++i) {
            DefaultCol col = (DefaultCol)this.importInfo.columnTypes.get(i);
            switch (col.getDataType()) {
                case 9: {
                    this.loadedData.time = (Long)data[i];
                    continue block4;
                }
                case 9999: {
                    double d;
                    this.loadedData.values[valueIndex] = d = ((Double)data[i]).doubleValue();
                    ++valueIndex;
                }
            }
        }
    }

    public void restart() {
    }
}

