/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.MassImportDataInfo
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.gridlib.compute.common.ExecuteOptions
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Files.job;

import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.MassImportDataInfo;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.gridlib.compute.common.ExecuteOptions;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.plugin.DataSource.impl.Files.job.DataMassImporterChildrenJob;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import java.io.File;
import java.io.FileFilter;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataMassImporterMasterJob
extends GridJob<Void> {
    public static final Logger Log = LoggerFactory.getLogger(DataMassImporterMasterJob.class);
    private static final int MAX_IMPORT_COUNT_CONCURRENT = 50;
    private static final int BATCH_PROGRESS = 10;
    private MassImportDataInfo importInfo;
    private AtomicInteger finished = new AtomicInteger(0);
    private JSONObject progressJson = new JSONObject();
    private volatile boolean error;
    private int totalFiles;
    private boolean canceled;
    public static final String IMPORT_GROUP = "DataMassImportJobChildrenGroup";
    private static final String CHILD_JOB_PREFIX = "DataMassImportChildJob_";
    private List<String> symbols = new LinkedList<String>();
    private File[] filesForImport;

    public DataMassImporterMasterJob(String jobId, MassImportDataInfo importInfo) {
        super(jobId, 0, null);
        this.importInfo = importInfo;
        this.filesForImport = this.readFiles(importInfo.getPath());
    }

    private synchronized void importFinished(String symbol) {
        this.symbols.add(symbol);
        if (this.finished.incrementAndGet() % 10 == 0) {
            this.updateProgress(L.t((String)"Symbol %s imported", (Object[])new Object[]{symbol}));
        }
    }

    public boolean hasFilesToImport() {
        return this.filesForImport != null && this.filesForImport.length > 0;
    }

    public void updateProgress(String message) {
        Integer percent = SQUtils.round((double)(100.0 * this.finished.doubleValue() / (double)this.totalFiles));
        this.progressJson.put("percent", (Object)percent);
        if (message != null) {
            this.progressJson.put("info", (Object)message);
        }
        DataManagerAddProgressSender.getInstance().sendData(this.progressJson);
    }

    private File[] readFiles(String path) {
        File folder = new File(path);
        if (!folder.exists()) {
            return null;
        }
        File[] filesForImport = folder.listFiles(new FileFilter(){

            @Override
            public boolean accept(File arg0) {
                return arg0.isFile() && arg0.getName().endsWith(".csv");
            }
        });
        return filesForImport;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Void call() throws Exception {
        Set<String> existingSymbols = DataManager.list().stream().map(i -> i.symbol).collect(Collectors.toSet());
        this.canceled = false;
        this.registerListener();
        try {
            this.error = false;
            File[] filesForImport = this.readFiles(this.importInfo.getPath());
            if (!this.hasFilesToImport()) {
                Void void_ = null;
                return void_;
            }
            this.totalFiles = filesForImport.length;
            LinkedList<DataMassImporterChildrenJob> jobs = new LinkedList<DataMassImporterChildrenJob>();
            int index = 0;
            for (File file : filesForImport) {
                jobs.add(new DataMassImporterChildrenJob(CHILD_JOB_PREFIX + file.getName(), file, this.importInfo, existingSymbols));
                ++index;
            }
            ExecuteOptions executeOptions = new ExecuteOptions();
            executeOptions.setMaxRunningCount(50);
            SQGrid.getGridClient().executeOnGrid(IMPORT_GROUP, jobs, executeOptions);
            while (this.finished.get() < this.totalFiles && !this.canceled) {
            }
            String group = null;
            if (this.error) {
                this.progressJson.put("error", (Object)L.t((String)"Some error occured during import. Check the log please.", (Object[])new Object[0]));
            } else if (this.importInfo.isCreateStockGroup()) {
                group = this.createStockGroup();
            }
            BasketOfStocksManager.getInstance().updateGroupsOfSymbols();
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBaskets(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            this.progressJson.put("percent", 100.0);
            String message = group == null ? L.t((String)"Symbols imported: %s", (Object[])new Object[]{index}) : L.t((String)"Symbols imported: %s and created stock group: %s", (Object[])new Object[]{index, group});
            this.progressJson.put("message", (Object)message);
            DataManagerAddProgressSender.getInstance().sendData(this.progressJson);
        }
        finally {
            this.unregisterListener();
        }
        return null;
    }

    private String createStockGroup() throws Exception {
        BasketDto groupDto = new BasketDto();
        groupDto.setCount(this.symbols.size());
        groupDto.setTotal(this.symbols.size());
        groupDto.setName(this.getGroupName());
        BasketOfStocksManager.getInstance().saveGroup(groupDto);
        LinkedList<StockDto> stocks = new LinkedList<StockDto>();
        for (String symbol : this.symbols) {
            StockDto stockDto = new StockDto();
            stockDto.setTicker(symbol);
            stockDto.setDateFrom(Long.valueOf(-1L));
            stockDto.setDateTo(Long.valueOf(-1L));
            stocks.add(stockDto);
        }
        BasketOfStocksManager.getInstance().saveStocks(groupDto.getId().intValue(), stocks);
        SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBaskets(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        MultiProgressListener listener = DataManagerDataProgress.get().createListener(groupDto.getName());
        listener.setMessage(L.t((String)"Stockgroup created.", (Object[])new Object[0]));
        listener.onProgress(100.0);
        DataManagerDataProgress.get().removeListener(groupDto.getName());
        return groupDto.getName();
    }

    private String getGroupName() {
        String folder = new File(this.importInfo.getPath()).getName();
        String group = "[" + folder + "]";
        int index = 0;
        while (BasketOfStocksManager.getInstance().getBasket(group) != null) {
            group = "[" + folder + ++index + "]";
        }
        return group;
    }

    private void unregisterListener() {
        SQGrid.getGridClient().removeMessageListener(IMPORT_GROUP);
    }

    private void registerListener() {
        SQGrid.getGridClient().registerMessageListener(IMPORT_GROUP, new IGridMessageListener(){

            public void messageReceived(GridMessage message) {
                if (DataMassImporterMasterJob.this.canceled) {
                    return;
                }
                if (message.getMessageID() == 1) {
                    String jobID = message.getJobDetails().getJobID();
                    String file = jobID.substring(DataMassImporterMasterJob.CHILD_JOB_PREFIX.length());
                    String symbol = file.substring(0, file.length() - 4);
                    MultiProgressListener listener = DataManagerDataProgress.get().createListener(symbol);
                    if (!message.getJobDetails().isSuccess()) {
                        DataMassImporterMasterJob.this.error = true;
                        listener.setMessage(L.t((String)"Error during import file: %s, error: %s", (Object[])new Object[]{file, message.getJobDetails().getException()}));
                    } else {
                        listener.setMessage(L.t((String)"File imported", (Object[])new Object[0]));
                    }
                    DataMassImporterMasterJob.this.importFinished((String)((Object)message.getData()));
                    listener.onProgress(100.0);
                }
            }
        });
    }

    public void messageReceived(GridMessage message) {
        super.messageReceived(message);
        switch (message.getMessageID()) {
            case 4: {
                this.canceled = true;
                SQGrid.getGridClient().stop(IMPORT_GROUP);
            }
        }
    }
}

