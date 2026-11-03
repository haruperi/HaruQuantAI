/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.MassImportDataInfo
 *  com.strategyquant.datalib.data.io.MassImportDataInfo$OverwriteStrategy
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  org.apache.commons.io.FilenameUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Files.job;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.MassImportDataInfo;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;
import org.apache.commons.io.FilenameUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataMassImporter {
    public static final Logger Log = LoggerFactory.getLogger(DataMassImporter.class);
    private static final String ACTION_LINK = "dataSourceDukascopy/importDataAction";
    private volatile boolean canceled;
    private MassImportDataInfo importInfo;
    private File file;
    private Set<String> existingSymbols;
    private MultiProgressListener progressListener;

    public DataMassImporter(MassImportDataInfo importInfo, File file, Set<String> existingSymbols) {
        this.importInfo = importInfo;
        this.file = file;
        this.existingSymbols = existingSymbols;
    }

    public void cancel() {
        this.canceled = true;
    }

    public boolean isCanceled() {
        return this.canceled;
    }

    public String performImport() throws Exception {
        boolean symbolExists;
        if (this.canceled) {
            return null;
        }
        String tickerFromFilename = FilenameUtils.removeExtension((String)this.file.getName());
        tickerFromFilename = tickerFromFilename + this.importInfo.getPostfix();
        this.progressListener = DataManagerDataProgress.get().createListener(tickerFromFilename);
        this.progressListener.setMessage(L.t((String)"Importing...", (Object[])new Object[0]));
        this.progressListener.onProgress(0.2);
        DataInfo dataInfo = DataManager.getDataInfo((String)this.importInfo.getConnection(), (String)tickerFromFilename);
        boolean bl = symbolExists = dataInfo != null;
        if (symbolExists && this.importInfo.getOverwriteStrategy() == MassImportDataInfo.OverwriteStrategy.skip) {
            this.progressListener.setMessage(L.t((String)"Skipped", (Object[])new Object[0]));
            this.progressListener.onProgress(100.0);
            return tickerFromFilename + " skipped";
        }
        boolean shoudlOverwrite = this.importInfo.getOverwriteStrategy() == MassImportDataInfo.OverwriteStrategy.overwrite;
        String symbol = dataInfo == null || shoudlOverwrite ? tickerFromFilename : this.generateTickerName(this.file);
        this.doImportFile(this.file, symbol, this.importInfo);
        this.progressListener.setMessage(L.t((String)"Completed", (Object[])new Object[0]));
        this.progressListener.onProgress(100.0);
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)tickerFromFilename, (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception exception) {
            // empty catch block
        }
        return symbol;
    }

    private void doImportFile(File file, String symbol, MassImportDataInfo importInfo) throws Exception {
        DataManager.addData((String)importInfo.getConnection(), (String)symbol, (String)importInfo.getInstrument(), (int)importInfo.getBarType(), (int)1);
        List<VersatileData> records = this.loadData(file, importInfo);
        this.writeData(symbol, records);
    }

    private void writeData(String symbol, List<VersatileData> records) throws Exception {
        String connection = this.importInfo.getConnection();
        int size = records.size();
        if (size != 0) {
            if (this.canceled) {
                return;
            }
            DataInfo dataInfo = DataManager.getDataInfo((String)connection, (String)symbol);
            DataBinWriterNew writer = null;
            writer = this.importInfo.getTimeframe().equals("TICK") ? DataBinWriterNew.getInstance((int)2, (String)MainApp.getDataPath(), (InstrumentInfo)dataInfo.symbolInfo) : DataBinWriterNew.getInstance((int)1, (String)MainApp.getDataPath(), (InstrumentInfo)dataInfo.symbolInfo);
            String fileName = DataManager.getDataFileName((String)connection, (String)symbol, (String)this.importInfo.getTimeframe(), (String)"No Session");
            String tempFileName = DataManager.getTempFileName((String)fileName);
            writer.setFileName(tempFileName);
            writer.open();
            for (VersatileData versatileData : records) {
                if (this.canceled) break;
                writer.writeData(versatileData);
            }
            long fromTime = records.get((int)0).time;
            long toTime = records.get((int)(size - 1)).time;
            int totalDays = SQTime.getDaysBetween((long)fromTime, (long)toTime) + 1;
            long secondsRecords = totalDays * 86400;
            DataManager.updateData((String)connection, (String)symbol, (long)fromTime, (long)toTime, (int)size, (long)secondsRecords, (int)dataInfo.barTimeType, (String)this.importInfo.getTimeframe(), (String)this.importInfo.getTimezone());
            writer.close();
            DataManager.removeDataFiles((String)connection, (String)symbol);
            new File(tempFileName).renameTo(new File(fileName));
        }
    }

    private String generateTickerName(File file) throws Exception {
        String symbolName = FilenameUtils.removeExtension((String)file.getName());
        while (this.existingSymbols.contains(symbolName)) {
            symbolName = DataManager.generateName((String)symbolName);
        }
        return symbolName;
    }

    private List<VersatileData> loadData(File file, MassImportDataInfo importInfo) throws IOException {
        LinkedList<VersatileData> records = new LinkedList<VersatileData>();
        List<String> lines = Files.readAllLines(file.toPath());
        for (String line : lines) {
            String[] parts;
            if (this.canceled) break;
            if ((line = line.trim()).isEmpty() || "Date".equals((parts = line.split(","))[0])) continue;
            VersatileData dto = new VersatileData();
            dto.time = SQTime.parseToMilis((String)parts[0], (String)importInfo.getDateFormat());
            if (importInfo.getTimeframe().equals("TICK")) {
                dto.ask = Double.valueOf(parts[1]);
                dto.bid = Double.valueOf(parts[2]);
                dto.volume = Double.valueOf(parts[3]);
            } else {
                dto.open = Double.valueOf(parts[1]);
                dto.high = Double.valueOf(parts[2]);
                dto.low = Double.valueOf(parts[3]);
                dto.close = Double.valueOf(parts[4]);
                dto.volume = Double.valueOf(parts[5]);
            }
            records.add(dto);
        }
        return records;
    }
}

