/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.consts.DataTypes
 *  com.strategyquant.datalib.data.BatchProgressController
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew
 *  com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew
 *  com.strategyquant.datalib.historyData.TickerFilterDto
 *  com.strategyquant.datalib.historyData.dto.TickerDto
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.datalib.metatrader4.MT4Utils
 *  com.strategyquant.datalib.metatrader4.MT4Utils$MetaTraderLocation
 *  com.strategyquant.datalib.metatrader4.Mt4Properties
 *  com.strategyquant.datalib.metatrader4.Mt4SymbolProperties
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.datalib.timezone.Timezone
 *  com.strategyquant.datalib.timezone.Timezones
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.historyData.DataSources
 *  com.strategyquant.lib.historyData.HistoryDataChecker
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.lib.utils.JsonCreator
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.data.download.DownloadDispatcher
 *  com.strategyquant.tradinglib.historyData.HistoryDataManager
 *  com.strategyquant.tradinglib.historyData.SpecialSymbolsManager
 *  com.strategyquant.tradinglib.project.ProjectResources
 *  com.strategyquant.tradinglib.project.console.CLILogger
 *  com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender
 *  com.strategyquant.tradinglib.project.websocket.DataManagerConfirm
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataManagerSaveProgreessSender
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.tradinglib.quality.QualityChecker
 *  com.strategyquant.tradinglib.stockchart.PreviewCaption
 *  com.strategyquant.tradinglib.stockchart.StockChartData
 *  com.strategyquant.tradinglib.stockchart.StockData
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.apache.http.util.LangUtils
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.Data;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.consts.DataTypes;
import com.strategyquant.datalib.data.BatchProgressController;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.datalib.historyData.TickerFilterDto;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.datalib.metatrader4.MT4Utils;
import com.strategyquant.datalib.metatrader4.Mt4Properties;
import com.strategyquant.datalib.metatrader4.Mt4SymbolProperties;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.datalib.timezone.Timezone;
import com.strategyquant.datalib.timezone.Timezones;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.historyData.DataSources;
import com.strategyquant.lib.historyData.HistoryDataChecker;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.CsvExportJob;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.format.Format;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.format.Formats;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.Items;
import com.strategyquant.plugin.DataManager.impl.Data.job.CloneToTimezoneJob;
import com.strategyquant.plugin.DataManager.impl.Data.job.MT4ExportJob;
import com.strategyquant.plugin.DataManager.impl.Data.job.MT5ExportJob;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.data.download.DownloadDispatcher;
import com.strategyquant.tradinglib.historyData.HistoryDataManager;
import com.strategyquant.tradinglib.historyData.SpecialSymbolsManager;
import com.strategyquant.tradinglib.project.ProjectResources;
import com.strategyquant.tradinglib.project.console.CLILogger;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerConfirm;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerSaveProgreessSender;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.quality.QualityChecker;
import com.strategyquant.tradinglib.stockchart.PreviewCaption;
import com.strategyquant.tradinglib.stockchart.StockChartData;
import com.strategyquant.tradinglib.stockchart.StockData;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import java.util.stream.Collectors;
import org.apache.http.util.LangUtils;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataServlet
extends HttpJSONServlet {
    private static final long serialVersionUID = 1L;
    private static final Logger Log = LoggerFactory.getLogger(DataServlet.class);
    private static final String MT4_EXPORT_JOB_ID = "MT4_Export_data_job";
    private static final String MT5_EXPORT = "MT5_Export";
    private static final int BATCH_LIMIT = 5;
    private volatile boolean canceled = false;

    private void checkLimitedSymbol(String symbol) {
        if (DataManager.isLimited((String)symbol)) {
            throw new IllegalArgumentException("Operation can't be done on limited symbols");
        }
    }

    private void checkLimitedSymbols(String[] symbols) {
        for (String symbol : symbols) {
            this.checkLimitedSymbol(symbol);
        }
    }

    private int getLimitedCount(String[] symbols) {
        int count = 0;
        for (String symbol : symbols) {
            if (!DataManager.isLimited((String)symbol)) continue;
            ++count;
        }
        return count;
    }

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        this.canceled = false;
        switch (command) {
            case "listData": {
                return this.onListData(args);
            }
            case "listDataJson": {
                return this.onListDataJson(args);
            }
            case "editData": {
                return this.onEditData(args);
            }
            case "cancelDataOperation": {
                return this.onCancelDataOperation(args);
            }
            case "clearData": {
                return this.onClearData(args);
            }
            case "removeData": {
                return this.onRemoveData(args);
            }
            case "showData": {
                return this.onShowData(args);
            }
            case "saveDataChanges": {
                return this.onSaveDataChanges(args);
            }
            case "getSymbolData": {
                return this.onGetSymbolData(args);
            }
            case "addTimeframe": {
                return this.onAddTimeframe(args);
            }
            case "reviewData": {
                return this.onReviewData(args);
            }
            case "getIndexForDate": {
                return this.onGetIndexForDate(args);
            }
            case "reviewChart": {
                return this.onReviewChart(args);
            }
            case "cloneToTimezone": {
                return this.onCloneToTimezone(args);
            }
            case "cloneToTimezoneAction": {
                return this.onCloneToTimezoneAction(args);
            }
            case "exportTick": {
                return this.onExport(true, args);
            }
            case "exportM1": {
                return this.onExport(false, args);
            }
            case "exportCDN": {
                return this.onExportCDN();
            }
            case "exportToCsv": {
                return this.onExportToCsv(args);
            }
            case "exportToCsvAction": {
                return this.onExportToCsvAction(args);
            }
            case "exportToCsvLoadSettings": {
                return this.onExportToCsvLoadSettings();
            }
            case "exportToCsvSaveFileFormat": {
                return this.onExportToCsvSaveFileFormat(args);
            }
            case "exportToCsvSaveAsFileFormat": {
                return this.onExportToCsvSaveAsFileFormat(args);
            }
            case "exportToCsvDeleteFileFormat": {
                return this.onExportToCsvDeleteFileFormat(args);
            }
            case "exportToMT4": {
                return this.onExportToMT4(args);
            }
            case "exportToMT4Action": {
                return this.onExportToMT4Action(args);
            }
            case "exportToMT4GetDataFolder": {
                return this.onExportToMT4GetDataFolder(args);
            }
            case "exportToMT4GetServerNames": {
                return this.onExportToMT4GetServerNames(args);
            }
            case "exportToMT4LoadProperties": {
                return this.onExportToMT4LoadProperties(args);
            }
            case "exportToMT5": {
                return this.onExportToMT5(args);
            }
            case "exportToMT5Action": {
                return this.onExportToMT5Action(args);
            }
            case "checkQualitySummary": {
                return this.onCheckQualitySummary(args);
            }
            case "checkQualityDetails": {
                return this.onCheckQualityDetails(args);
            }
            case "updateAll": {
                return this.onUpdateAll();
            }
            case "updateSelected": {
                return this.onUpdateSelected(args);
            }
            case "stopAll": {
                return this.onStopAll();
            }
            case "pauseAll": {
                return this.onPauseAll();
            }
            case "resumeAll": {
                return this.onResumeAll();
            }
            case "listTimezones": {
                return this.onListTimezones(args);
            }
            case "load": {
                return this.onLoad(args);
            }
            case "save": {
                return this.onSave(args);
            }
            case "confirm": {
                return this.onConfirm(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onCancelDataOperation(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        this.canceled = true;
        response.put("success", (Object)L.t((String)"Operation canceled.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onResumeAll() {
        DownloadDispatcher.get().resumeAll();
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Resuming download...", (Object[])new Object[0]));
        return response.toString();
    }

    private String onPauseAll() {
        DownloadDispatcher.get().pauseAll();
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Pausing download...", (Object[])new Object[0]));
        return response.toString();
    }

    private String onStopAll() {
        DownloadDispatcher.get().stopAll();
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Stopping download...", (Object[])new Object[0]));
        return response.toString();
    }

    private String onListTimezones(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        CLILogger.log((String)"Timezone,Timezone name");
        for (Timezone timezone : Timezones.getTimezones()) {
            CLILogger.log((String)(timezone.printShortName() + "," + timezone.getId()));
        }
        response.put("success", (Object)L.t((String)"Timezones listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private static String exportIdent(String jobPrefix, String symbol, boolean unique) {
        String ident = jobPrefix + "_" + symbol;
        return unique ? ident + "_" + System.nanoTime() : ident;
    }

    private String onExportToCsv(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            Format format;
            String[] symbols = this.tryGetParam(args, "symbols")[0].split(",");
            this.checkLimitedSymbols(symbols);
            String timeframe = this.tryGetParam(args, "timeframe")[0];
            String directory = this.tryGetParam(args, "directory")[0];
            String filePrefix = this.tryGetParam(args, "filePrefix")[0];
            String session = this.tryGetParam(args, "session")[0];
            String fileFormat = this.tryGetParam(args, "fileFormat")[0];
            boolean uniqueIdent = Boolean.parseBoolean(this.getParam(args, "uniqueIdent", "false"));
            String targetTimezone = this.getParam(args, "targetTimezone", "");
            if ("".equals(targetTimezone)) {
                targetTimezone = null;
            }
            if (fileFormat.equals("Custom")) {
                String header = this.tryGetParam(args, "header")[0];
                String items = this.tryGetParam(args, "format")[0];
                boolean includeHeader = Boolean.parseBoolean(args.get("includeHeader")[0]);
                format = Formats.parseCustomFormat(fileFormat, header, items, includeHeader);
            } else {
                format = Formats.get().findByName(fileFormat);
                if (format == null) {
                    throw new Exception(L.t((String)"Cannot find format with name '%s'", (Object[])new Object[]{fileFormat}));
                }
                if (args.containsKey("includeHeader")) {
                    format = format.withIncludeHeader(Boolean.parseBoolean(args.get("includeHeader")[0]));
                }
            }
            long fromDate = Long.MIN_VALUE;
            long toDate = Long.MIN_VALUE;
            String dateType = this.getParam(args, "dateType", "custom");
            if (!dateType.equals("allTime")) {
                try {
                    if (args.containsKey("dateFrom")) {
                        fromDate = SQTime.parseToMilis((String)this.tryGetParam(args, "dateFrom")[0], (String)"yyyy.MM.dd");
                    }
                }
                catch (Exception e) {
                    if (MainApp.runInConsoleWithoutActiveWebserver()) {
                        CLILogger.log((String)L.t((String)("Cannot parse date from - " + e.getMessage()), (Object[])new Object[0]));
                    }
                    throw new Exception(L.t((String)("Cannot parse date from - " + e.getMessage()), (Object[])new Object[0]));
                }
                try {
                    if (args.containsKey("dateTo")) {
                        toDate = SQTime.parseToMilis((String)this.tryGetParam(args, "dateTo")[0], (String)"yyyy.MM.dd");
                    }
                }
                catch (Exception e) {
                    if (MainApp.runInConsoleWithoutActiveWebserver()) {
                        CLILogger.log((String)L.t((String)("Cannot parse date to - " + e.getMessage()), (Object[])new Object[0]));
                    }
                    throw new Exception(L.t((String)("Cannot parse date to - " + e.getMessage()), (Object[])new Object[0]));
                }
            }
            for (int a = 0; a < symbols.length; ++a) {
                String symbol = symbols[a];
                DataInfo info = DataManager.getDataInfo((String)"History", (String)symbol);
                if (info == null) {
                    throw new IllegalArgumentException("Symbol " + symbol + " not found.");
                }
                HistoryDataChecker.checkDataExport((int)info.source);
                if (info.rows == 0) continue;
                if (fromDate == Long.MIN_VALUE || dateType.equals("allTime")) {
                    fromDate = info.dateFrom;
                }
                if (toDate == Long.MIN_VALUE || dateType.equals("allTime")) {
                    toDate = info.dateTo;
                }
                MultiProgressListener listener = DataManagerDataProgress.get().createListener(symbol, "data/exportToCsvAction");
                String ident = DataServlet.exportIdent("CsvExport", symbol, uniqueIdent);
                String filePath = String.format("%s/%s%s-%s-%s.csv", directory, filePrefix, symbol, timeframe, session);
                CsvExportJob job = new CsvExportJob(ident, (IProgressListener)listener, info.connection, symbol, timeframe, session, filePath, fromDate, toDate, format, targetTimezone);
                SQGrid.getGridClient().executeOnGrid(ident, (GridJob)job);
            }
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot export data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Exporting data.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onExportToCsvAction(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbol", "action"});
        String symbol = this.tryGetParam(args, "symbol")[0];
        String action = this.tryGetParam(args, "action")[0];
        JSONObject response = new JSONObject();
        String ident = "CsvExport_" + symbol;
        switch (action) {
            case "stop": {
                SQGrid.getGridClient().stop(ident);
                break;
            }
            case "pause": {
                SQGrid.getGridClient().pause(ident);
                break;
            }
            case "continue": {
                SQGrid.getGridClient().restart(ident);
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onExportToCsvLoadSettings() throws Exception {
        JSONObject response = new JSONObject();
        response.put("items", (Object)Items.get().toJson());
        response.put("formats", (Object)Formats.get().toJson());
        response.put("canonical", (Object)new JSONObject().put("bar", (Object)"Generic bar format (comma delimited)").put("barDateFormat", (Object)"yyyyMMdd").put("tick", (Object)"Generic tick format (comma delimited)").put("tickDateFormat", (Object)"yyyyMMdd HH:mm:ss.SSS"));
        response.put("success", (Object)L.t((String)"Settings loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onExportToCsvSaveFileFormat(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String fileFormat = this.tryGetParam(args, "fileFormat")[0];
        String header = this.tryGetParam(args, "header")[0];
        String items = this.tryGetParam(args, "format")[0];
        boolean includeHeader = Boolean.parseBoolean(args.get("includeHeader")[0]);
        try {
            Formats.get().updateFormat(fileFormat, header, items, includeHeader);
            response.put("formats", (Object)Formats.get().toJson());
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot update file format.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Format saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onExportToCsvSaveAsFileFormat(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String fileFormat = this.tryGetParam(args, "newFormatName")[0];
        String header = this.tryGetParam(args, "header")[0];
        String items = this.tryGetParam(args, "format")[0];
        boolean includeHeader = Boolean.parseBoolean(args.get("includeHeader")[0]);
        try {
            Format format = Formats.get().findByName(fileFormat);
            if (format != null) {
                throw new Exception(L.t((String)"Format with name '%s' already exists. Please choose another name.", (Object[])new Object[]{fileFormat}));
            }
            Formats.get().addFormat(fileFormat, header, items, includeHeader);
            response.put("formats", (Object)Formats.get().toJson());
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot save file format.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Format saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onExportToCsvDeleteFileFormat(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String fileFormat = this.tryGetParam(args, "fileFormat")[0];
        try {
            Formats.get().deleteFormat(fileFormat);
            response.put("formats", (Object)Formats.get().toJson());
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot delete file format.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Format deleted.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCheckQualityDetails(Map<String, String[]> parameterMap) throws NumberFormatException, Exception {
        int count;
        int posStart;
        String symbol = parameterMap.get("symbol")[0].toString();
        int totalErrors = Integer.parseInt(this.tryGetParam(parameterMap, "totalErrors")[0]);
        String timeframe = parameterMap.get("timeframe")[0].toString();
        String session = parameterMap.get("session")[0].toString();
        try {
            posStart = Integer.parseInt(parameterMap.get("posStart")[0]);
        }
        catch (Exception ex) {
            posStart = 0;
        }
        try {
            count = Integer.parseInt(parameterMap.get("count")[0]);
        }
        catch (Exception ex) {
            count = 20;
        }
        QualityChecker checker = new QualityChecker();
        String rows = checker.getDetails(timeframe, symbol, session, posStart, posStart + count);
        JsonCreator json = new JsonCreator();
        json.beginObject();
        json.putRaw("rows", (Object)rows, true);
        json.put("pos", (Object)posStart, true);
        json.put("total_count", (Object)totalErrors, true);
        json.put("success", (Object)"ok", false);
        json.endObject(false);
        return json.toJson();
    }

    private String onCheckQualitySummary(Map<String, String[]> parameterMap) throws Exception {
        String symbol = parameterMap.get("symbol")[0].toString();
        String timeframe = parameterMap.get("timeframe")[0].toString();
        String session = parameterMap.get("session")[0].toString();
        QualityChecker checker = new QualityChecker();
        String summary = checker.getSummary(timeframe, symbol, session);
        JsonCreator json = new JsonCreator();
        json.beginObject();
        json.putRaw("problems", (Object)summary, true);
        json.put("success", (Object)"ok", false);
        json.endObject(false);
        return json.toJson();
    }

    private String onExportToMT4GetDataFolder(Map<String, String[]> parameterMap) throws Exception {
        String appPath = parameterMap.get("appPath")[0].toString();
        JSONObject response = new JSONObject();
        MT4Utils.MetaTraderLocation mtLocation = MT4Utils.getDataFolder((String)appPath);
        if (mtLocation == null) {
            File rootFolder = MT4Utils.getDataFolderFile();
            response.put("error", (Object)L.t((String)"Cannot find MT4 data folder in default location '%s'.", (Object[])new Object[]{rootFolder.getAbsolutePath()}));
        } else {
            response.put("dataPath", (Object)mtLocation.getDataFolder());
            response.put("serverNames", (Object)new JSONArray((Object)mtLocation.getServerNames()));
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onExportToMT4GetServerNames(Map<String, String[]> parameterMap) throws Exception {
        String dataFolderPath = parameterMap.get("dataFolderPath")[0].toString();
        JSONObject response = new JSONObject();
        try {
            response.put("serverNames", (Object)new JSONArray((Object)MT4Utils.getServerNames((String)dataFolderPath)));
        }
        catch (Exception e) {
            response.put("error", (Object)L.t((String)"Data folder doesn't contain MT4 history files.", (Object[])new Object[0]));
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onExportToMT4LoadProperties(Map<String, String[]> parameterMap) throws Exception {
        Mt4Properties properties;
        String filePath = parameterMap.get("filePath")[0].toString();
        JSONObject response = new JSONObject();
        if (filePath.equals("default")) {
            properties = new Mt4Properties();
            try {
                String appPath = MainApp.settings().get("mt4ExportAppPath", "");
                response.put("appPath", (Object)appPath);
                String serverName = MainApp.settings().get("mt4ExportServerName", "");
                if (!appPath.isEmpty()) {
                    MT4Utils.MetaTraderLocation mtLocation = MT4Utils.getDataFolder((String)appPath);
                    response.put("dataPath", (Object)mtLocation.getDataFolder());
                    response.put("serverNames", (Object)new JSONArray((Object)mtLocation.getServerNames()));
                    if (serverName.equals("") && mtLocation.getServerNames().length > 0) {
                        serverName = mtLocation.getServerNames()[0];
                    }
                }
                response.put("serverName", (Object)serverName);
            }
            catch (Exception e) {
                Log.error("ExportToMT4 - Error while loading last settings.", (Throwable)e);
            }
        } else {
            properties = new Mt4Properties(filePath);
        }
        response.put("symbols", (Object)properties.toJSON());
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onExportToMT4(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"sqSymbol", "mt4Symbol", "serverName", "appPath", "dataPath", "properties"});
        String sqSymbol = parameterMap.get("sqSymbol")[0].toString();
        String mt4Symbol = parameterMap.get("mt4Symbol")[0].toString();
        String encoding = parameterMap.get("encoding")[0].toString();
        String serverName = parameterMap.get("serverName")[0].toString();
        String appPath = parameterMap.get("appPath")[0].toString();
        String dataPath = parameterMap.get("dataPath")[0].toString();
        String properties = parameterMap.get("properties")[0].toString();
        String timeframe = parameterMap.get("timeframe")[0].toString();
        String exportMode = parameterMap.get("exportMode")[0].toString();
        boolean uniqueIdent = Boolean.parseBoolean(this.getParam(parameterMap, "uniqueIdent", "false"));
        String targetTimezone = this.getParam(parameterMap, "targetTimezone", "");
        if ("".equals(targetTimezone)) {
            targetTimezone = null;
        }
        if (properties.equals("default")) {
            Mt4Properties mt4Pproperties = new Mt4Properties();
            properties = mt4Pproperties.findBySymbol(mt4Symbol);
        }
        MainApp.settings().set("mt4ExportAppPath", appPath);
        MainApp.settings().set("mt4ExportServerName", serverName);
        long fromDate = Long.MIN_VALUE;
        long toDate = Long.MIN_VALUE;
        try {
            if (parameterMap.containsKey("dateFrom")) {
                fromDate = SQTime.parseToMilis((String)this.tryGetParam(parameterMap, "dateFrom")[0], (String)"yyyy.MM.dd");
            }
        }
        catch (Exception e) {
            if (MainApp.runInConsoleWithoutActiveWebserver()) {
                CLILogger.log((String)L.t((String)("Cannot parse date from - " + e.getMessage()), (Object[])new Object[0]));
            }
            throw new Exception(L.t((String)("Cannot parse date from - " + e.getMessage()), (Object[])new Object[0]));
        }
        try {
            if (parameterMap.containsKey("dateTo")) {
                toDate = SQTime.parseToMilis((String)this.tryGetParam(parameterMap, "dateTo")[0], (String)"yyyy.MM.dd");
            }
        }
        catch (Exception e) {
            if (MainApp.runInConsoleWithoutActiveWebserver()) {
                CLILogger.log((String)L.t((String)("Cannot parse date to - " + e.getMessage()), (Object[])new Object[0]));
            }
            throw new Exception(L.t((String)("Cannot parse date to - " + e.getMessage()), (Object[])new Object[0]));
        }
        MultiProgressListener listener = DataManagerDataProgress.get().createListener(sqSymbol, "data/exportToMT4Action");
        Mt4SymbolProperties symbolProperties = new Mt4SymbolProperties();
        try {
            symbolProperties.parse(properties);
        }
        catch (Exception e) {
            Log.error("Invalid MT4 data specification file. Exc.", (Throwable)e);
            throw new Exception(L.t((String)"Invalid MT4 data specification file.", (Object[])new Object[0]));
        }
        DataInfo info = DataManager.getDataInfo((String)"History", (String)sqSymbol);
        if (info == null) {
            throw new Exception(L.t((String)"Symbol %s doesn't exist.", (Object[])new Object[]{sqSymbol}));
        }
        if (fromDate == Long.MIN_VALUE) {
            fromDate = info.dateFrom;
        }
        if (toDate == Long.MIN_VALUE) {
            toDate = info.dateTo;
        }
        String jobId = DataServlet.exportIdent(MT4_EXPORT_JOB_ID, sqSymbol, uniqueIdent);
        MT4ExportJob job = new MT4ExportJob(jobId, sqSymbol, mt4Symbol, encoding, fromDate, toDate, dataPath, serverName, symbolProperties, timeframe, exportMode, targetTimezone, (IProgressListener)listener);
        ArrayList<MT4ExportJob> jobs = new ArrayList<MT4ExportJob>(1);
        jobs.add(job);
        GridClient gridClient = SQGrid.getGridClient();
        gridClient.executeOnGrid(jobId, jobs);
        JSONObject response = new JSONObject();
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onExportToMT4Action(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbol", "action"});
        String symbol = this.tryGetParam(args, "symbol")[0];
        String action = this.tryGetParam(args, "action")[0];
        JSONObject response = new JSONObject();
        GridClient gridClient = SQGrid.getGridClient();
        String groupId = "MT4_Export_data_job_" + symbol;
        switch (action) {
            case "stop": {
                gridClient.stop(groupId);
                break;
            }
            case "pause": {
                gridClient.pause(groupId);
                break;
            }
            case "continue": {
                gridClient.restart(groupId);
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onExportToMT5(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            String symbol = this.tryGetParam(args, "symbol")[0];
            String connection = this.getParam(args, "connection", "History");
            String timeframe = this.tryGetParam(args, "timeframe")[0];
            boolean uniqueIdent = Boolean.parseBoolean(this.getParam(args, "uniqueIdent", "false"));
            String spreadType = this.tryGetParam(args, "spread")[0];
            double spreadPips = Double.parseDouble(this.tryGetParam(args, "spreadValue")[0]);
            double spreadPoints = Double.parseDouble(this.tryGetParam(args, "spreadPoints")[0]);
            String directory = this.tryGetParam(args, "directory")[0];
            String fileName = this.tryGetParam(args, "fileName")[0];
            String targetTimezone = this.getParam(args, "targetTimezone", "");
            if ("".equals(targetTimezone)) {
                targetTimezone = null;
            }
            String filePath = directory + "/" + fileName + ".csv";
            long fromDate = Long.MIN_VALUE;
            long toDate = Long.MIN_VALUE;
            try {
                if (args.containsKey("dateFrom")) {
                    fromDate = SQTime.parseToMilis((String)this.tryGetParam(args, "dateFrom")[0], (String)"yyyy.MM.dd");
                }
            }
            catch (Exception e) {
                if (MainApp.runInConsoleWithoutActiveWebserver()) {
                    CLILogger.log((String)L.t((String)("Cannot parse date from - " + e.getMessage()), (Object[])new Object[0]));
                }
                throw new Exception(L.t((String)("Cannot parse date from - " + e.getMessage()), (Object[])new Object[0]));
            }
            try {
                if (args.containsKey("dateTo")) {
                    toDate = SQTime.parseToMilis((String)this.tryGetParam(args, "dateTo")[0], (String)"yyyy.MM.dd");
                }
            }
            catch (Exception e) {
                if (MainApp.runInConsoleWithoutActiveWebserver()) {
                    CLILogger.log((String)L.t((String)("Cannot parse date to - " + e.getMessage()), (Object[])new Object[0]));
                }
                throw new Exception(L.t((String)("Cannot parse date to - " + e.getMessage()), (Object[])new Object[0]));
            }
            DataInfo info = DataManager.getDataInfo((String)"History", (String)symbol);
            if (info == null) {
                throw new Exception(L.t((String)"Symbol %s doesn't exist.", (Object[])new Object[]{symbol}));
            }
            if (info.rows == 0) {
                throw new Exception(L.t((String)"Symbol %s doesn't contain any data.", (Object[])new Object[]{symbol}));
            }
            if (fromDate == Long.MIN_VALUE) {
                fromDate = info.dateFrom;
            }
            if (toDate == Long.MIN_VALUE) {
                toDate = info.dateTo;
            }
            MultiProgressListener listener = DataManagerDataProgress.get().createListener(symbol, "data/exportToMT5Action");
            String ident = DataServlet.exportIdent(MT5_EXPORT, symbol, uniqueIdent);
            MT5ExportJob job = new MT5ExportJob(ident, (IProgressListener)listener, connection, symbol, timeframe, spreadType, spreadPoints, spreadPips, filePath, fromDate, toDate, targetTimezone);
            SQGrid.getGridClient().executeOnGrid(ident, (GridJob)job);
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot export data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Exporting data.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onExportToMT5Action(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbol", "action"});
        String symbol = this.tryGetParam(args, "symbol")[0];
        String action = this.tryGetParam(args, "action")[0];
        JSONObject response = new JSONObject();
        String ident = "MT5_Export_" + symbol;
        switch (action) {
            case "stop": {
                SQGrid.getGridClient().stop(ident);
                break;
            }
            case "pause": {
                SQGrid.getGridClient().pause(ident);
                break;
            }
            case "continue": {
                SQGrid.getGridClient().restart(ident);
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onListData(Map<String, String[]> parameterMap) {
        JSONObject response;
        block17: {
            response = new JSONObject();
            try {
                DataToSend dataToSend = WSDataObjects.getData((String)"", (String)"list");
                if (MainApp.runInConsoleWithoutActiveWebserver()) {
                    PrintWriter csv;
                    block16: {
                        csv = null;
                        try {
                            csv = new PrintWriter(this.tryGetParam(parameterMap, "csv")[0]);
                        }
                        catch (Exception e) {
                            if (!parameterMap.containsKey("csv")) break block16;
                            Log.error("Cannot open file. Reason: ", (Throwable)e);
                        }
                    }
                    String header = "Symbol,Instrument,Timeframe,Timezone,Date from,Date to,Total days,Total records,Source,Data type";
                    if (csv == null) {
                        CLILogger.log((String)header);
                    } else {
                        csv.println(header);
                    }
                    JSONArray data = dataToSend.getDataObject().getJSONArray("data");
                    for (int i = 0; i < data.length(); ++i) {
                        JSONObject object = data.getJSONObject(i);
                        String dateFrom = "";
                        try {
                            if (object.getLong("dateFrom") > 0L) {
                                dateFrom = SQTime.toUIDateString((long)object.getLong("dateFrom"));
                            }
                        }
                        catch (Exception exception) {
                            // empty catch block
                        }
                        String dateTo = "";
                        try {
                            if (object.getLong("dateTo") > 0L) {
                                dateTo = SQTime.toUIDateString((long)object.getLong("dateTo"));
                            }
                        }
                        catch (Exception exception) {
                            // empty catch block
                        }
                        String source = DataSources.toString((int)object.getInt("source"));
                        String dataType = DataTypes.toString((int)object.getInt("dataType"));
                        String line = object.getString("symbol") + "," + object.getString("instrument") + "," + (object.has("timeframe") ? object.getString("timeframe") : "") + "," + (object.has("timezone") ? "\"" + object.getString("timezone") + "\"" : "") + "," + dateFrom + "," + dateTo + "," + object.getLong("totalDays") + "," + object.getLong("rows") + "," + source + "," + dataType;
                        if (csv == null) {
                            CLILogger.log((String)line);
                            continue;
                        }
                        csv.println(line);
                    }
                    if (csv != null) {
                        csv.flush();
                        csv.close();
                    }
                    break block17;
                }
                SQWebSocketManager.addToDataQueue((DataToSend)dataToSend, (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            }
            catch (Exception e) {
                return DataServlet.apiErrorJSON((String)L.t((String)"Cannot get list of data.", (Object[])new Object[0]), (Throwable)e);
            }
        }
        response.put("success", (Object)L.t((String)"Data listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onListDataJson(Map<String, String[]> args) {
        try {
            boolean compact;
            JSONObject data = WSDataObjects.getData((String)"", (String)"list").getDataObject();
            boolean bl = compact = args.containsKey("compact") && "1".equals(args.get("compact")[0]);
            if (compact) {
                JSONArray full = data.optJSONArray("data");
                JSONArray slim = new JSONArray();
                for (int i = 0; full != null && i < full.length(); ++i) {
                    JSONObject row = full.optJSONObject(i);
                    if (row == null) continue;
                    slim.put((Object)new JSONObject().put("symbol", (Object)row.optString("symbol")).put("instrument", (Object)row.optString("instrument")).put("timeframe", (Object)row.optString("timeframe")).put("dateFrom", row.optLong("dateFrom", 0L)).put("dateTo", row.optLong("dateTo", 0L)).put("rows", row.optLong("rows", 0L)).put("readyToUse", row.optBoolean("readyToUse", false)));
                }
                data = new JSONObject().put("data", (Object)slim);
            }
            data.put("success", (Object)L.t((String)"Data listed.", (Object[])new Object[0]));
            return data.toString();
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot get list of data.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onEditData(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String connection = this.tryGetParam(args, "connection")[0];
            String symbol = this.tryGetParam(args, "symbol")[0];
            String swap = args.containsKey("swap") ? this.tryGetParam(args, "swap")[0] : null;
            this.checkLimitedSymbol(symbol);
            String toSymbol = this.tryGetParam(args, "symbolNew")[0];
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
            if (dataInfo == null) {
                throw new Exception("No data info found for symbol '" + symbol + "'.");
            }
            String instrument = dataInfo.instrument;
            int barType = dataInfo.barTimeType;
            int newBrokerId = dataInfo.brokerId;
            try {
                instrument = this.tryGetParam(args, "instrument")[0];
                InstrumentInfo newInstrument = InstrumentManager.getInstrumentInfo((String)instrument);
                newBrokerId = newInstrument.broker;
            }
            catch (Exception newInstrument) {
                // empty catch block
            }
            try {
                barType = Integer.parseInt(this.tryGetParam(args, "barType")[0]);
            }
            catch (Exception newInstrument) {
                // empty catch block
            }
            if (dataInfo.brokerId != newBrokerId && dataInfo.rows != 0) {
                boolean someTimezoneIsSet;
                BrokerDto originalBroker = BrokerManager.getInstance().getBroker(Integer.valueOf(dataInfo.brokerId));
                BrokerDto newBroker = BrokerManager.getInstance().getBroker(Integer.valueOf(newBrokerId));
                boolean bl = someTimezoneIsSet = originalBroker.getMtTimezone() != null || newBroker.getMtTimezone() != null;
                if (someTimezoneIsSet && !LangUtils.equals((Object)originalBroker.getMtTimezone(), (Object)newBroker.getMtTimezone())) {
                    return DataServlet.apiErrorJSONNoLog((String)L.t((String)"Cannot update the instrument because the broker of this instrument uses a different timezone. To avoid data corruption, please clear this symbols data first and then try again", (Object[])new Object[0]), null);
                }
            }
            DataManager.updateData((String)connection, (String)symbol, (long)dataInfo.dateFrom, (long)dataInfo.dateTo, (int)dataInfo.rows, (long)dataInfo.secondsRecords, (int)barType, (String)dataInfo.timeframe, null);
            if (!instrument.equals(dataInfo.instrument)) {
                DataManager.updateInstrument((String)connection, (String)symbol, (String)instrument);
            }
            if (dataInfo.brokerId != newBrokerId) {
                DataManager.updateBroker((String)connection, (String)symbol, (int)newBrokerId);
            }
            if (swap != null && !swap.equals(dataInfo.symbolInfo.swap)) {
                DataManager.updateInstrumentSwap((String)connection, (String)symbol, (String)instrument, (String)swap);
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            }
            if (SpecialSymbolsManager.isSpecial((String)symbol)) {
                throw new Exception(L.t((String)"Modification of this symbol is not allowed.", (Object[])new Object[0]));
            }
            if (!symbol.equals(toSymbol)) {
                boolean equityOrFutures;
                if (SpecialSymbolsManager.isSpecial((String)toSymbol)) {
                    throw new Exception(L.t((String)"This symbol name '%s' couldn't be used.", (Object[])new Object[]{toSymbol}));
                }
                boolean daily = dataInfo.timeframe != null && dataInfo.timeframe.equals("D1");
                boolean bl = equityOrFutures = dataInfo.source == 5 || dataInfo.source == 6;
                if (equityOrFutures && daily && !toSymbol.endsWith(".D")) {
                    throw new Exception(L.t((String)"Cannot to rename symbol '%s' to '%s'. Reason: Daily futures and equities must end to .D postfix", (Object[])new Object[]{symbol, toSymbol}));
                }
                dataInfo = DataManager.getDataInfo((String)"History", (String)toSymbol);
                if (dataInfo != null) {
                    throw new Exception("Symbol with name '" + symbol + "' already exists.");
                }
                try {
                    DataManager.renameData((String)connection, (String)symbol, (String)toSymbol);
                }
                catch (Exception e) {
                    Log.error(String.format("Cannot rename symbol '%s' to '%s'. Reason:", symbol, toSymbol), (Throwable)e);
                    throw new Exception(L.t((String)"Cannot to rename symbol '%s' to '%s'. Reason: %s", (Object[])new Object[]{symbol, toSymbol, e.getMessage()}));
                }
                symbol = symbol + "##" + toSymbol;
            }
            this.sendDataUpdate(symbol, "rename");
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onClearData(Map<String, String[]> args) {
        boolean success;
        String message;
        JSONObject response = new JSONObject();
        boolean async = false;
        try {
            final String[] connections = this.tryGetParam(args, "connections")[0].split(",");
            final String rawSymbols = this.tryGetParam(args, "symbols")[0];
            final String[] symbols = rawSymbols.split(",");
            int limitedCount = this.getLimitedCount(symbols);
            if (limitedCount == 0) {
                message = "Data cleared";
                success = true;
            } else if (limitedCount == symbols.length) {
                message = "Data was not cleared - limited symbols can't be cleared";
                success = false;
            } else {
                message = "Data cleared, but not all. Limited data can't be cleared";
                success = true;
            }
            if (symbols.length >= 5) {
                new Thread(this){
                    final /* synthetic */ DataServlet this$0;
                    {
                        this.this$0 = this$0;
                    }

                    @Override
                    public void run() {
                        JSONObject progress = new JSONObject();
                        for (int a = 0; a < connections.length; ++a) {
                            DataManager.clearDataInBatch((String)connections[a], (String)symbols[a]);
                            if (a % 5 == 0) {
                                Integer percent = SQUtils.round((double)(100.0 * (double)a / (double)connections.length));
                                progress.put("percent", (Object)percent);
                                progress.put("info", (Object)L.t((String)"Cleared symbol '%s'", (Object[])new Object[]{symbols[a]}));
                                DataManagerAddProgressSender.getInstance().sendData(progress);
                            }
                            if (this.this$0.canceled) break;
                        }
                        DataManager.flushUpdatedData();
                        progress.put("percent", 100.0);
                        progress.put("info", (Object)L.t((String)"Cleared symbols", (Object[])new Object[0]));
                        if (success) {
                            progress.put("message", (Object)L.t((String)message, (Object[])new Object[0]));
                        } else {
                            progress.put("error", (Object)L.t((String)message, (Object[])new Object[0]));
                        }
                        DataManagerAddProgressSender.getInstance().sendData(progress);
                        try {
                            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)rawSymbols, (String)"update"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                        }
                        catch (Exception e) {
                            Log.error("Error while sending message to ui", (Throwable)e);
                        }
                        this.this$0.updateStockGroups(symbols);
                    }
                }.start();
            } else {
                for (int a = 0; a < connections.length; ++a) {
                    DataManager.clearDataInBatch((String)connections[a], (String)symbols[a]);
                }
                DataManager.flushUpdatedData();
                this.updateStockGroups(symbols);
                this.sendDataUpdate(this.tryGetParam(args, "symbols")[0], "clear");
            }
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot clear data.", (Object[])new Object[0]), (Throwable)e);
        }
        if (async) {
            response.put("success", (Object)L.t((String)"Clearing data started. Please wait...", (Object[])new Object[0]));
        } else if (success) {
            response.put("success", (Object)message);
        } else {
            response.put("error", (Object)message);
        }
        return response.toString();
    }

    private void updateStockGroups(String[] symbols) {
        if (BasketOfStocksManager.getInstance() == null) {
            return;
        }
        new Thread(new Runnable(){

            @Override
            public void run() {
                Set changedGroups = BasketOfStocksManager.getInstance().updateGroupsOfSymbols();
                if (!changedGroups.isEmpty()) {
                    try {
                        String affectedSymbols = String.join((CharSequence)",", changedGroups);
                        SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)affectedSymbols, (String)"update"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                        SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBaskets(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                    }
                    catch (Exception e) {
                        Log.error("", (Throwable)e);
                    }
                }
            }
        }).start();
    }

    private String onRemoveData(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        boolean async = false;
        try {
            final String[] connections = this.tryGetParam(args, "connections")[0].split(",");
            final String rawSymbols = this.tryGetParam(args, "symbols")[0];
            final String[] symbols = rawSymbols.split(",");
            final JSONObject progress = new JSONObject();
            if (symbols.length >= 5) {
                async = true;
                new Thread(new Runnable(){
                    final /* synthetic */ DataServlet this$0;
                    {
                        this.this$0 = this$0;
                    }

                    @Override
                    public void run() {
                        try {
                            DataManager.deleteDataInBatch((String[])connections, (String[])symbols, (BatchProgressController)new BatchProgressController(){
                                final /* synthetic */ 3 this$1;
                                {
                                    this.this$1 = this$1;
                                }

                                public void updateProgress(int count, int total, String name) throws Exception {
                                    if (count % 5 == 0) {
                                        Integer percent = SQUtils.round((double)(100.0 * (double)count / (double)total));
                                        progress.put("percent", (Object)percent);
                                        progress.put("info", (Object)L.t((String)"Removed symbol '%s'", (Object[])new Object[]{name}));
                                        DataManagerAddProgressSender.getInstance().sendData(progress);
                                    }
                                }

                                public boolean isCancel() {
                                    return this.this$1.this$0.canceled;
                                }

                                public void finished() {
                                    this.this$1.this$0.sendDataUpdate(rawSymbols, "remove");
                                    this.this$1.this$0.updateStockGroups(symbols);
                                    progress.put("percent", 100.0);
                                    progress.put("info", (Object)L.t((String)"Removed symbols", (Object[])new Object[0]));
                                    progress.put("message", (Object)L.t((String)"Data removed", (Object[])new Object[0]));
                                    DataManagerAddProgressSender.getInstance().sendData(progress);
                                }
                            });
                        }
                        catch (ClassNotFoundException e) {
                            Log.error("Error while removing data", (Throwable)e);
                        }
                    }
                }).start();
            } else {
                DataManager.deleteDataInBatch((String[])connections, (String[])symbols, null);
                this.updateStockGroups(symbols);
                this.sendDataUpdate(this.tryGetParam(args, "symbols")[0], "remove");
            }
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot remove data.", (Object[])new Object[0]), (Throwable)e);
        }
        if (async) {
            response.put("success", (Object)L.t((String)"Removing data started. Please wait...", (Object[])new Object[0]));
        } else {
            response.put("success", (Object)L.t((String)"Data removed", (Object[])new Object[0]));
        }
        return response.toString();
    }

    private String onShowData(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String connection = this.tryGetParam(args, "connection")[0];
            String symbol = this.tryGetParam(args, "symbol")[0];
            boolean show = Boolean.valueOf(this.tryGetParam(args, "show")[0]);
            DataManager.showData((String)connection, (String)symbol, (boolean)show);
            this.sendDataUpdate(symbol, "show");
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot change data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data changed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetSymbolData(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        JSONArray data = new JSONArray();
        try {
            String symbol = this.tryGetParam(args, "symbol")[0];
            String dateFrom = this.tryGetParam(args, "dateFrom")[0];
            String dateTo = this.tryGetParam(args, "dateTo")[0];
            String session = this.tryGetParam(args, "session")[0];
            double spread = 2.5;
            if (SessionManager.getSession((String)session) == null) {
                Log.info("Session '{}' doesn't exist, using NoSession.", (Object)session);
                session = "No Session";
            }
            if (!symbol.equals("not set")) {
                long dateFromValue = 0L;
                long dateToValue = 0L;
                if (!dateFrom.equals("not set")) {
                    try {
                        dateFromValue = SQTime.parseToMilis((String)dateFrom, (String)"yyyy.MM.dd");
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                }
                if (!dateTo.equals("not set")) {
                    try {
                        dateToValue = SQTime.parseToMilis((String)dateTo, (String)"yyyy.MM.dd");
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                }
                ChartDef chart = new ChartDef("History", symbol, "D1", dateFromValue, dateToValue, spread, session);
                IDataLoader loader = DataManager.getDataLoader((ChartDef)chart, (int)1, null);
                loader.open();
                double lastATRValue = -1.0;
                double prevClose = 0.0;
                int CurrentBar = 0;
                int ATRPeriod = 14;
                while (loader.hasNextTick()) {
                    JSONArray array = new JSONArray();
                    VersatileData vd = new VersatileData();
                    loader.getNextTick(vd);
                    array.put((Object)SQTime.toUIDateString((long)vd.time));
                    array.put(vd.close);
                    double tr = vd.high - vd.low;
                    if (lastATRValue < 0.0) {
                        lastATRValue = tr;
                        prevClose = vd.close;
                    } else {
                        tr = Math.max(Math.abs(vd.low - prevClose), Math.max(tr, Math.abs(vd.high - prevClose)));
                        lastATRValue = ((double)(Math.min(CurrentBar + 1, 14) - 1) * lastATRValue + tr) / (double)Math.min(CurrentBar + 1, 14);
                        prevClose = vd.close;
                    }
                    ++CurrentBar;
                    array.put(lastATRValue);
                    data.put((Object)array);
                }
                loader.close();
            }
            response.put("data", (Object)data);
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot get symbol data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Symbol data loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onAddTimeframe(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String timeframe = this.tryGetParam(args, "timeframe")[0];
            TimeframeManager.addTimeframe((String)timeframe);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getTimeframes(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot add timeframe.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Timeframe added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSaveDataChanges(Map<String, String[]> parameterMap) {
        try {
            HashSet datesForDeleteSet;
            final String symbol = parameterMap.get("symbol")[0].toString();
            final String timeframe = parameterMap.get("timeframe")[0].toString();
            final String session = parameterMap.get("session")[0].toString();
            String[] forDelete = this.getParam(parameterMap, "deleted[]");
            final HashMap<Long, String[]> changed = new HashMap<Long, String[]>();
            final boolean tick = timeframe.equals("TICK");
            String format = tick ? "yyyy.MM.dd HH:mm:ss.SSS" : "yyyy.MM.dd HH:mm:ss";
            List changedRows = parameterMap.keySet().stream().filter(i -> i.startsWith("changed[")).collect(Collectors.toList());
            for (String changedRowKey : changedRows) {
                String[] changedRow = this.getParam(parameterMap, changedRowKey);
                changed.put(SQTime.parseToMilis((String)changedRow[0], (String)format), changedRow);
            }
            Set<Object> set = datesForDeleteSet = forDelete != null ? Arrays.stream(forDelete).map(i -> SQTime.parseToMilis((String)i, (String)format)).collect(Collectors.toSet()) : new HashSet();
            if (datesForDeleteSet.isEmpty() && changedRows.isEmpty()) {
                return DataServlet.apiErrorJSON((String)L.t((String)"No changes was performed.", (Object[])new Object[0]), null);
            }
            new Thread(new Runnable(){
                final /* synthetic */ DataServlet this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void run() {
                    try {
                        DataInfo info = DataManager.getDataInfo((String)"History", (String)symbol);
                        int dateType = timeframe.equals("TICK") ? 2 : 1;
                        DataBinReaderNew reader = DataBinReaderNew.getInstance((int)dateType, (InstrumentInfo)info.symbolInfo);
                        String path = DataManager.getDataFileName((String)"History", (String)symbol, (String)timeframe, (String)session);
                        File sourceFile = new File(path);
                        String sourceFileName = sourceFile.getAbsolutePath();
                        reader.setFileName(sourceFileName);
                        reader.openFile();
                        boolean crypted = reader.isCrypted();
                        DataBinWriterNew writer = crypted ? DataBinWriterNew.getCryptedInstance((int)dateType, (String)MainApp.getDataPath(), (InstrumentInfo)info.symbolInfo) : DataBinWriterNew.getInstance((int)dateType, (String)MainApp.getDataPath(), (InstrumentInfo)info.symbolInfo);
                        String tempFileName = sourceFile.getAbsoluteFile() + ".temp";
                        writer.setFileName(tempFileName);
                        writer.open();
                        VersatileData data = new VersatileData();
                        long min = -1L;
                        long max = -1L;
                        long savedRows = 0L;
                        int count = 0;
                        JSONObject progress = new JSONObject();
                        while (reader.dataRemaining()) {
                            reader.readData();
                            data = reader.tickData;
                            long iDate = data.time;
                            if (count % 200 == 0) {
                                Integer percent = SQUtils.round((double)(100.0 * (double)count / (double)info.rows));
                                progress.put("percent", (Object)percent);
                                progress.put("info", (Object)L.t((String)"Saving data %s", (Object[])new Object[]{SQTime.toString((long)iDate)}));
                                DataManagerSaveProgreessSender.getInstance().sendData(progress);
                            }
                            ++count;
                            if (datesForDeleteSet.contains(iDate)) continue;
                            String[] iChanges = (String[])changed.get(iDate);
                            if (iChanges != null) {
                                if (tick) {
                                    data.ask = Double.valueOf(iChanges[1]);
                                    data.bid = Double.valueOf(iChanges[2]);
                                    data.volume = Double.valueOf(iChanges[3]);
                                } else {
                                    data.open = Double.valueOf(iChanges[1]);
                                    data.high = Double.valueOf(iChanges[2]);
                                    data.low = Double.valueOf(iChanges[3]);
                                    data.close = Double.valueOf(iChanges[4]);
                                    data.volume = Double.valueOf(iChanges[5]);
                                }
                            }
                            writer.writeData(data);
                            if (min == -1L) {
                                min = iDate;
                            }
                            max = iDate;
                            ++savedRows;
                        }
                        reader.closeFile();
                        writer.close();
                        sourceFile.delete();
                        new File(tempFileName).renameTo(sourceFile);
                        DataManager.updateData((String)"History", (String)info.symbol, (long)min, (long)max, (int)((int)savedRows), (long)info.secondsRecords, (int)1, (String)info.timeframe, (String)"Etc/UCT");
                        progress.put("percent", 100.0);
                        progress.put("info", (Object)L.t((String)"Data saved", (Object[])new Object[0]));
                        DataManagerSaveProgreessSender.getInstance().sendData(progress);
                    }
                    catch (Exception e) {
                        Log.error("Error while updating. ", (Throwable)e);
                    }
                }
            }).start();
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot load chart.", (Object[])new Object[0]), (Throwable)e);
        }
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Data saving.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetIndexForDate(Map<String, String[]> parameterMap) throws Exception {
        String symbol = parameterMap.get("symbol")[0].toString();
        String timeframe = parameterMap.get("timeframe")[0].toString();
        String session = parameterMap.get("session")[0].toString();
        long date = SQTime.parseDateToMilis((String)parameterMap.get("date")[0].toString());
        DataInfo info = DataManager.getDataInfo((String)"History", (String)symbol);
        DataBinReaderNew reader = this.getDataReader(symbol, timeframe, session);
        int i = this.seekReader(reader, info, date);
        reader.seek(i);
        VersatileData data = new VersatileData();
        while (reader.dataRemaining()) {
            reader.readData();
            data = reader.tickData;
            long iDate = data.time;
            if (iDate >= date) break;
            ++i;
        }
        reader.closeFile();
        JSONObject result = new JSONObject();
        result.put("success", (Object)"Index listed.");
        result.put("index", i);
        return result.toString();
    }

    private int seekReader(DataBinReaderNew reader, DataInfo info, long date) throws Exception {
        int tries;
        long total = reader.getTotalRecords();
        if (total == 0L) {
            total = info.rows;
        }
        long timeDelta = info.dateTo - info.dateFrom;
        double steps = timeDelta / total;
        long secFromStart = date - info.dateFrom;
        int start = (int)((double)secFromStart / steps);
        for (tries = 0; tries < 5; ++tries) {
            reader.seek(start);
            reader.readData();
            long currentDate = reader.tickData.time;
            if (currentDate < date) break;
            start -= start / 10;
        }
        return tries == 5 || start < 0 ? 0 : start;
    }

    private DataBinReaderNew getDataReader(String symbol, String timeframe, String session) throws Exception {
        DataInfo info = DataManager.getDataInfo((String)"History", (String)symbol);
        boolean tickData = timeframe.equals("TICK");
        DataBinReaderNew reader = null;
        reader = tickData ? DataBinReaderNew.getInstance((int)2, (InstrumentInfo)info.symbolInfo) : DataBinReaderNew.getInstance((int)1, (InstrumentInfo)info.symbolInfo);
        String path = DataManager.getDataFileName((String)"History", (String)symbol, (String)timeframe, (String)session);
        File file = new File(path);
        reader.setFileName(file.getAbsolutePath());
        reader.openFile();
        return reader;
    }

    private String onReviewData(Map<String, String[]> parameterMap) throws Exception {
        JSONArray rows;
        int count;
        int posStart;
        JSONObject response = new JSONObject();
        try {
            posStart = Integer.parseInt(parameterMap.get("posStart")[0]);
        }
        catch (Exception ex) {
            posStart = 0;
        }
        try {
            count = Integer.parseInt(parameterMap.get("count")[0]);
        }
        catch (Exception ex) {
            count = 100;
        }
        String symbol = parameterMap.get("symbol")[0].toString();
        String timeframe = parameterMap.get("timeframe")[0].toString();
        String session = parameterMap.get("session")[0].toString();
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
        if (dataInfo == null) {
            throw new Exception("No data info found for symbol '" + symbol + "'.");
        }
        boolean tickData = timeframe.equals("TICK");
        long total = 0L;
        if (tickData) {
            rows = this.listTickData(symbol, timeframe, session, posStart, count, dataInfo);
            total = dataInfo.rows;
        } else {
            ChartDef chart = new ChartDef("History", symbol, timeframe, 0L, SQTime.toLong((int)2100, (int)1, (int)1), 2.5, session);
            IDataLoader loader = DataManager.getDataLoader((ChartDef)chart, (int)1, null);
            loader.open();
            total = loader.getTotalRecords();
            rows = this.listOHLCData(posStart, count, loader, dataInfo);
        }
        response.put("total_count", total);
        response.put("rows", (Object)rows);
        response.put("pos", posStart);
        response.put("success", (Object)L.t((String)"Data listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onExport(boolean tick, Map<String, String[]> parameterMap) throws Exception {
        String symbol = parameterMap.get("symbol")[0].toString();
        String targetFolder = parameterMap.get("path")[0].toString();
        this.checkLimitedSymbol(symbol);
        long fromDate = 0L;
        long toDate = 0L;
        try {
            fromDate = SQTime.parseToMilis((String)this.tryGetParam(parameterMap, "dateFrom")[0], (String)"yyyy.MM.dd");
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            toDate = SQTime.parseToMilis((String)this.tryGetParam(parameterMap, "dateTo")[0], (String)"yyyy.MM.dd");
        }
        catch (Exception exception) {
            // empty catch block
        }
        DataInfo info = DataManager.getDataInfo((String)"History", (String)symbol);
        if (info == null) {
            throw new Exception(L.t((String)"Symbol %s doesn't exist.", (Object[])new Object[]{symbol}));
        }
        if (tick) {
            DataManager.exportTick((String)symbol, (long)fromDate, (long)toDate, (String)targetFolder);
        } else {
            DataManager.exportM1((String)symbol, (long)fromDate, (long)toDate, (String)targetFolder);
        }
        return "{}";
    }

    private String onExportCDN() throws Exception {
        Thread t = new Thread(){

            @Override
            public void run() {
                String[] symbols = new String[]{"AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY", "XAGUSD", "XAUUSD"};
                try {
                    int i;
                    for (i = 0; i < symbols.length; ++i) {
                        DataManager.exportTick((String)symbols[i], (long)0L, (long)0L, (String)"C:/SQ4-cdndata/data/tick");
                    }
                    for (i = 0; i < symbols.length; ++i) {
                        DataManager.exportM1((String)(symbols[i] + "_M1"), (long)0L, (long)0L, (String)"C:/SQ4-cdndata/data/m1");
                    }
                }
                catch (Exception e) {
                    Log.error("Error while export CDN data. Exc.", (Throwable)e);
                }
            }
        };
        t.start();
        return "{}";
    }

    private String onReviewChart(Map<String, String[]> parameterMap) throws Exception {
        JsonCreator json = new JsonCreator();
        json.beginObject();
        long indexFrom = 0L;
        long indexTo = 0L;
        try {
            indexFrom = Long.parseLong(this.tryGetParam(parameterMap, "indexFrom")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            indexTo = Long.parseLong(this.tryGetParam(parameterMap, "indexTo")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        boolean loadPreview = true;
        try {
            loadPreview = Boolean.parseBoolean(this.tryGetParam(parameterMap, "loadPreview")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        String symbol = parameterMap.get("symbol")[0].toString();
        String timeframe = parameterMap.get("timeframe")[0].toString();
        String session = parameterMap.get("session")[0].toString();
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
        if (dataInfo == null) {
            throw new Exception("No data info found for symbol '" + symbol + "'.");
        }
        ChartDef chart = new ChartDef("History", symbol, timeframe, 0L, SQTime.toLong((int)2100, (int)1, (int)1), 2.5, session);
        IDataLoader loader = DataManager.getDataLoader((ChartDef)chart, (int)1, null);
        loader.open();
        long total = loader.getTotalRecords();
        if (indexFrom < 0L) {
            indexFrom = 0L;
        }
        if (indexTo < 0L) {
            indexTo = indexFrom + 100L;
        }
        if (indexTo >= total) {
            indexTo = total - 1L;
        }
        if (indexFrom >= indexTo && (indexFrom = indexTo - 100L) < 0L) {
            indexFrom = 0L;
        }
        try {
            StockData stockData = new StockData();
            stockData.setCount(total);
            if (loadPreview) {
                this.fillPreview(stockData, total, loader);
            }
            stockData.setAreaFrom(indexFrom);
            stockData.setAreaTo(indexTo);
            loader.seek((int)indexFrom);
            this.fillStockData(stockData, loader, dataInfo);
            stockData.getChartData()[0].setTitle(symbol + "/" + timeframe);
            json.putRaw("chart", (Object)stockData.toJSON(), false);
            try {
                json.separator();
                json.put("requestId", (Object)this.tryGetParam(parameterMap, "requestId")[0], false);
            }
            catch (Exception exception) {}
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot load chart.", (Object[])new Object[0]), (Throwable)e);
        }
        loader.close();
        json.put("success", (Object)"Chart data loaded", false);
        json.endObject(false);
        return json.toJson();
    }

    private String onCloneToTimezone(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String[] symbols = this.tryGetParam(parameterMap, "symbols")[0].split(",");
        String postfix = parameterMap.get("postfix")[0].toString();
        int toTimezoneType = Integer.parseInt(this.tryGetParam(parameterMap, "cloneTimezoneType")[0]);
        this.checkLimitedSymbols(symbols);
        boolean removeWeekends = Boolean.parseBoolean(this.tryGetParam(parameterMap, "removeWeekends")[0]);
        int shiftHours = 0;
        for (int i = 0; i < symbols.length; ++i) {
            String toTimezone;
            String symbol = symbols[i];
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
            if (toTimezoneType == 1) {
                shiftHours = 0;
                toTimezone = parameterMap.get("cloneTimezone")[0].toString();
            } else {
                shiftHours = Integer.parseInt(this.tryGetParam(parameterMap, "cloneTimezoneShift")[0]);
                toTimezone = dataInfo.timezone;
                if (toTimezone == null) {
                    toTimezone = "Etc/UCT";
                }
            }
            if (dataInfo.sourceDataId != 0) {
                if (!MainApp.runInConsoleWithoutActiveWebserver()) continue;
                CLILogger.log((String)L.t((String)"Symbol '%s' - cloned data cannot be cloned again.", (Object[])new Object[]{symbol}));
                continue;
            }
            if (dataInfo.rows == 0 && dataInfo.source == 1) {
                if (!MainApp.runInConsoleWithoutActiveWebserver()) continue;
                CLILogger.log((String)L.t((String)"Symbol '%s' has no data to clone (unknown timezone).", (Object[])new Object[]{symbol}));
                continue;
            }
            String toSymbol = this.addPostfixToSymbolName(symbol, postfix, toTimezone, shiftHours, dataInfo);
            while (DataManager.checkDataExists((String)"History", (String)toSymbol)) {
                toSymbol = DataManager.generateName((String)toSymbol);
            }
            if (i == 0) {
                MainApp.settings().set("CloneTimezone", shiftHours == 0 ? toTimezone : shiftHours + "");
                MainApp.settings().set("CloneRemoveWeekends", removeWeekends + "");
            }
            MultiProgressListener listener = DataManagerDataProgress.get().createListener(symbol, "data/cloneToTimezoneAction");
            TickerDto ticker = null;
            if (dataInfo.source == 6) {
                ticker = HistoryDataManager.get().getFutureTicker(dataInfo.uSymbol);
            } else if (dataInfo.source == 5) {
                ticker = HistoryDataManager.get().getStockTicker(dataInfo.uSymbol);
            }
            CloneToTimezoneJob job = new CloneToTimezoneJob("CloneToTimezoneJob_" + symbol, symbol, toSymbol, toTimezone, shiftHours, removeWeekends, ticker, listener);
            SQGrid.getGridClient().executeOnGrid("CloneToTimezoneJob_" + symbol, (GridJob)job);
        }
        response.put("success", (Object)L.t((String)"Data cloned.", (Object[])new Object[0]));
        return response.toString();
    }

    private String addPostfixToSymbolName(String symbol, String postfix, String toTimezone, int shiftHours, DataInfo dataInfo) {
        String text;
        String result = symbol + postfix;
        result = result.replaceAll("\\{timeframe\\}", dataInfo.timeframe);
        if (shiftHours == 0) {
            text = Timezone.print((String)toTimezone, (int)dataInfo.source, (boolean)true);
            text = text.replace(",", "").replaceAll("\\s+", "_");
        } else {
            text = shiftHours < 0 ? shiftHours + "" : "+" + shiftHours;
        }
        result = result.replaceAll("\\{cloneTime\\}", text);
        result = result.replaceAll("-", "Minus");
        result = result.replaceAll("\\+", "Plus");
        result = result.replace("&", "");
        return result;
    }

    private String onCloneToTimezoneAction(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbol", "action"});
        String symbol = this.tryGetParam(args, "symbol")[0];
        String action = this.tryGetParam(args, "action")[0];
        JSONObject response = new JSONObject();
        String jobIdent = "CloneToTimezoneJob_" + symbol;
        switch (action) {
            case "stop": {
                SQGrid.getGridClient().stop(jobIdent);
                break;
            }
            case "pause": {
                SQGrid.getGridClient().pause(jobIdent);
                break;
            }
            case "continue": {
                SQGrid.getGridClient().restart(jobIdent);
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private void fillPreview(StockData stockData, long total, IDataLoader loader) throws Exception {
        double step;
        int size;
        int previewSize = 1000;
        if (total < (long)previewSize) {
            size = (int)total;
            step = 1.0;
        } else {
            step = (double)total / (double)previewSize;
            size = previewSize;
        }
        LinkedList<PreviewCaption> previewCaptions = new LinkedList<PreviewCaption>();
        float[] previewYVals = new float[size];
        double index = 0.0;
        Integer lastYear = null;
        VersatileData data = new VersatileData();
        for (int counter = 0; index < (double)total && counter < size; index += step, ++counter) {
            loader.seek((int)index);
            loader.hasNextTick();
            loader.getNextTick(data);
            previewYVals[counter] = (float)((double)Math.round(data.close * 10000.0) / 10000.0);
            int year = SQTime.getFullYear((long)data.time);
            if (lastYear != null && year == lastYear) continue;
            PreviewCaption pc = new PreviewCaption(counter, String.valueOf(year));
            previewCaptions.add(pc);
            lastYear = year;
        }
        stockData.setPreviewYVals(previewYVals);
        stockData.setPreviewCaptions(previewCaptions.toArray(new PreviewCaption[0]));
    }

    private void fillStockData(StockData stockData, IDataLoader loader, DataInfo dataInfo) throws Exception {
        long total = stockData.getAreaTo() - stockData.getAreaFrom();
        int index = 0;
        StockChartData data = new StockChartData();
        data.setPrecision(dataInfo.symbolInfo.decimals);
        stockData.setChartData(new StockChartData[1]);
        stockData.getChartData()[0] = data;
        VersatileData versatileData = new VersatileData();
        data.setClose(new LinkedList());
        data.setLow(new LinkedList());
        data.setHigh(new LinkedList());
        data.setOpen(new LinkedList());
        LinkedList<Long> xVals = new LinkedList<Long>();
        while (loader.hasNextTick()) {
            loader.getNextTick(versatileData);
            xVals.add(versatileData.time);
            data.getClose().add(versatileData.close);
            data.getOpen().add(versatileData.open);
            data.getHigh().add(versatileData.high);
            data.getLow().add(versatileData.low);
            if ((long)index++ != total) continue;
        }
        long[] xValsArray = new long[xVals.size()];
        int i = 0;
        for (Long xVal : xVals) {
            xValsArray[i++] = xVal;
        }
        data.setxVals(xValsArray);
    }

    private JSONArray listTickData(String symbol, String timeframe, String session, int posStart, int count, DataInfo dataInfo) throws Exception {
        JSONArray rows = new JSONArray();
        DataInfo info = DataManager.getDataInfo((String)"History", (String)symbol);
        DataBinReaderNew reader = DataBinReaderNew.getInstance((int)2, (InstrumentInfo)info.symbolInfo);
        String path = DataManager.getDataFileName((String)"History", (String)symbol, (String)timeframe, (String)session);
        File file = new File(path);
        reader.setFileName(file.getAbsolutePath());
        reader.openFile();
        reader.seek(posStart);
        VersatileData data = new VersatileData();
        for (long i = 0L; reader.dataRemaining() && i < (long)count; ++i) {
            reader.readData();
            data = reader.tickData;
            JSONArray rowData = new JSONArray();
            rowData.put((Object)SQTime.toFullDateTimeString((long)data.time));
            rowData.put((Object)SQUtils.d2String((double)data.ask, (int)dataInfo.symbolInfo.decimals));
            rowData.put((Object)SQUtils.d2String((double)data.bid, (int)dataInfo.symbolInfo.decimals));
            rowData.put(data.volume > 1.0 ? SQUtils.round((double)data.volume) : 1);
            JSONObject row = new JSONObject();
            row.put("id", (Object)("r" + ((long)posStart + i)));
            row.put("data", (Object)rowData);
            rows.put((Object)row);
        }
        reader.closeFile();
        return rows;
    }

    private JSONArray listOHLCData(int posStart, int count, IDataLoader loader, DataInfo dataInfo) throws Exception {
        JSONArray rows = new JSONArray();
        loader.seek(posStart);
        for (long i = 0L; loader.hasNextTick() && i < (long)count; ++i) {
            VersatileData data = new VersatileData();
            loader.getNextTick(data);
            JSONArray rowData = new JSONArray();
            rowData.put((Object)SQTime.toFullDateMinuteString((long)data.time));
            rowData.put((Object)SQUtils.d2String((double)data.open, (int)dataInfo.symbolInfo.decimals));
            rowData.put((Object)SQUtils.d2String((double)data.high, (int)dataInfo.symbolInfo.decimals));
            rowData.put((Object)SQUtils.d2String((double)data.low, (int)dataInfo.symbolInfo.decimals));
            rowData.put((Object)SQUtils.d2String((double)data.close, (int)dataInfo.symbolInfo.decimals));
            rowData.put(data.volume > 1.0 ? SQUtils.roundLong((double)data.volume) : 1L);
            JSONObject row = new JSONObject();
            row.put("id", (Object)("r" + ((long)posStart + i)));
            row.put("data", (Object)rowData);
            rows.put((Object)row);
        }
        loader.close();
        return rows;
    }

    private void sendDataUpdate(String symbol, String actionPerformed) {
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)symbol, (String)actionPerformed), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            Log.error("Cannot send websocket data update. ", (Throwable)e);
        }
    }

    private TickerFilterDto getFilterForHistoryTickers(List<String> symbols) {
        TickerFilterDto filter = new TickerFilterDto();
        filter.setSearchInTicker(true);
        filter.setExactMatch(true);
        filter.setNames(symbols.toArray(new String[0]));
        return filter;
    }

    private String onUpdateAll() {
        try {
            JSONObject response = new JSONObject();
            ArrayList<DataInfo> data = DataManager.listSafe();
            data = new ArrayList<DataInfo>(data.stream().filter(d -> d.source != 8).toList());
            Collections.shuffle(data);
            this.performUpdate(data);
            response.put("success", (Object)L.t((String)"Updates started.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private void performUpdate(List<DataInfo> data) throws Exception {
        LinkedList<String> futuresSymbols = new LinkedList<String>();
        LinkedList<String> equitiesSymbols = new LinkedList<String>();
        for (DataInfo dataInfo : data) {
            if (dataInfo.source == 5 && dataInfo.uSymbol != null) {
                equitiesSymbols.add(dataInfo.uSymbol);
            }
            if (dataInfo.source != 6 || dataInfo.uSymbol == null) continue;
            futuresSymbols.add(dataInfo.uSymbol);
        }
        LinkedList<TickerDto> futuresTickers = futuresSymbols.isEmpty() ? new LinkedList<TickerDto>() : HistoryDataManager.get().getFuturesTickers(this.getFilterForHistoryTickers(futuresSymbols));
        LinkedList<TickerDto> equitiesTickers = equitiesSymbols.isEmpty() ? new LinkedList<TickerDto>() : HistoryDataManager.get().getStockTickers(this.getFilterForHistoryTickers(equitiesSymbols));
        Map<String, TickerDto> futuresMap = this.toMap(futuresTickers);
        Map<String, TickerDto> equityMap = this.toMap(equitiesTickers);
        HashMap<String, String[]> map = new HashMap<String, String[]>();
        String[] symbols = new String[1];
        map.put("symbols", symbols);
        for (DataInfo dataInfo : data) {
            if (DataManager.isLimited((String)dataInfo.symbol)) continue;
            symbols[0] = dataInfo.symbol;
            if (dataInfo.source == 5) {
                DownloadDispatcher.get().updateHistoryData(dataInfo, equityMap.get(dataInfo.uSymbol));
                continue;
            }
            if (dataInfo.source == 6) {
                DownloadDispatcher.get().updateHistoryData(dataInfo, futuresMap.get(dataInfo.uSymbol));
                continue;
            }
            if (dataInfo.source == 2) {
                try {
                    Program.get((String)"DataSourceDukascopy").call("updateSelected", new Object[]{map});
                }
                catch (Exception exception) {}
                continue;
            }
            if (dataInfo.source == 7) {
                try {
                    Program.get((String)"DataSourceCrypto").call("updateSelected", new Object[]{map});
                }
                catch (Exception exception) {}
                continue;
            }
            if (dataInfo.source == 4) {
                try {
                    Program.get((String)"DataSourceDarwinex").call("updateSelected", new Object[]{map});
                }
                catch (Exception exception) {}
                continue;
            }
            if (dataInfo.source == 3) {
                try {
                    Program.get((String)"DataSourceYahoo").call("updateSelected", new Object[]{map});
                }
                catch (Exception exception) {}
                continue;
            }
            if (dataInfo.source != 8) continue;
            try {
                Program.get((String)"DataSourceMt5Api").call("updateSelected", new Object[]{map});
            }
            catch (Exception exception) {}
        }
    }

    private Map<String, TickerDto> toMap(List<TickerDto> tickers) {
        HashMap<String, TickerDto> map = new HashMap<String, TickerDto>();
        for (TickerDto dto : tickers) {
            map.put(dto.getTicker(), dto);
        }
        return map;
    }

    private String onUpdateSelected(Map<String, String[]> args) {
        try {
            JSONObject response = new JSONObject();
            String[] symbols = this.tryGetParamValue(args, "symbols").split(",");
            LinkedList<DataInfo> infos = new LinkedList<DataInfo>();
            for (String symbol : symbols) {
                DataInfo di = DataManager.getDataInfo((String)"History", (String)symbol);
                if (di == null) {
                    Log.error(String.format("Symbol with name '%s' doesn't exist.", symbol));
                    continue;
                }
                infos.add(di);
            }
            this.performUpdate(infos);
            response.put("success", (Object)L.t((String)"Updates started.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onLoad(Map<String, String[]> args) {
        try {
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            ArrayList<String> names = new ArrayList<String>();
            Element elData = XMLUtil.fileToXmlElement((File)file);
            if (!elData.getName().equals("Data")) {
                throw new Exception("No Data found to import.");
            }
            ArrayList<Object> data = new ArrayList<Object>();
            ArrayList<DataInfo> dataClone = new ArrayList<DataInfo>();
            for (Object elDataInfo : elData.getChildren("DataInfo")) {
                DataInfo diLoaded = new DataInfo();
                diLoaded.setFromXML((Element)elDataInfo);
                if (diLoaded.sourceDataId > 0) {
                    dataClone.add(diLoaded);
                    continue;
                }
                data.add(diLoaded);
            }
            data.addAll(dataClone);
            HashMap<Integer, Integer> brokerIdMap = new HashMap<Integer, Integer>();
            for (Element elBrokerInfo : elData.getChildren("Broker")) {
                BrokerDto brokerDto = ProjectResources.loadBrokerElement((Element)elBrokerInfo);
                Integer originalBrokerId = brokerDto.getId();
                BrokerDto existingBroker = BrokerManager.getInstance().getBroker(brokerDto.getName());
                if (existingBroker != null) {
                    brokerIdMap.put(originalBrokerId, existingBroker.getId());
                    continue;
                }
                brokerDto.setId(null);
                BrokerManager.getInstance().saveBroker(brokerDto);
                brokerIdMap.put(originalBrokerId, brokerDto.getId());
            }
            boolean overwriteAll = false;
            for (DataInfo dataInfo : data) {
                Object brokerId;
                int sourceDataId = -1;
                DataInfo di = DataManager.getDataInfo((String)"History", (String)dataInfo.symbol);
                if (di == null) {
                    Integer instrumentBrokerId = (Integer)brokerIdMap.get(dataInfo.symbolInfo.broker);
                    dataInfo.symbolInfo.broker = instrumentBrokerId == null ? -1 : instrumentBrokerId;
                    ProjectResources.checkInstrumentExists((InstrumentInfo)dataInfo.symbolInfo);
                    brokerId = (Integer)brokerIdMap.get(dataInfo.brokerId);
                    DataManager.addData((String)"History", (String)dataInfo.symbol, (String)dataInfo.instrument, (int)dataInfo.barTimeType, (int)dataInfo.source, (String)dataInfo.uSymbol, (String)dataInfo.uSymbolName, (int)-1, (int)(brokerId == null ? -1 : (Integer)brokerId));
                    names.add(dataInfo.symbol);
                    if (dataInfo.sourceDataId > 0) {
                        for (DataInfo dataInfo2 : data) {
                            DataInfo di2;
                            if (dataInfo2.id != dataInfo.sourceDataId || (di2 = DataManager.getDataInfo((String)"History", (String)dataInfo2.symbol)) == null) continue;
                            sourceDataId = di2.id;
                            break;
                        }
                    }
                    DataManager.updateData((String)"History", (String)dataInfo.symbol, (long)0L, (long)0L, (int)0, (long)0L, (int)dataInfo.barTimeType, (String)dataInfo.timeframe, (String)dataInfo.timezone, (int)sourceDataId, (boolean)dataInfo.removeWeekends);
                    continue;
                }
                String action = "";
                if (!overwriteAll) {
                    DataManagerConfirm.get().awaitConfirmation(L.t((String)"Overwrite confirm", (Object[])new Object[0]), L.t((String)"Symbol '%s' already exists, do you want to overwrite it with the imported one?", (Object[])new Object[]{di.symbol}));
                    action = DataManagerConfirm.get().getConfirmedAction();
                }
                if (action.equals("skip")) continue;
                if (action.equals("cancel")) break;
                if (!action.equals("overwrite") && !action.equals("overwrite_all") && !overwriteAll) continue;
                if (action.equals("overwrite_all")) {
                    overwriteAll = true;
                }
                DataManager.clearData((String)"History", (String)dataInfo.symbol);
                if (dataInfo.sourceDataId > 0) {
                    for (DataInfo dataInfo3 : data) {
                        DataInfo dataInfo4;
                        if (dataInfo3.id != dataInfo.sourceDataId || (dataInfo4 = DataManager.getDataInfo((String)"History", (String)dataInfo3.symbol)) == null) continue;
                        sourceDataId = dataInfo4.id;
                        break;
                    }
                }
                DataManager.updateData((String)"History", (String)dataInfo.symbol, (long)0L, (long)0L, (int)0, (long)0L, (int)dataInfo.barTimeType, (String)dataInfo.timeframe, (String)dataInfo.timezone, (int)sourceDataId, (boolean)dataInfo.removeWeekends);
                brokerId = (Integer)brokerIdMap.get(dataInfo.brokerId);
                DataManager.updateBroker((String)"History", (String)dataInfo.symbol, (int)(brokerId == null ? -1 : (Integer)brokerId));
                names.add(dataInfo.symbol);
            }
            this.sendDataUpdate(String.join((CharSequence)",", names), "add");
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            response.put("success", (Object)L.t((String)"Data (%d) loaded.", (Object[])new Object[]{names.size()}));
            return response.toString();
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot load data.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onSave(Map<String, String[]> args) {
        try {
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            Element elData = new Element("Data");
            String[] symbols = this.tryGetParamValue(args, "symbols").split(",");
            TreeSet<Integer> usedBrokerIds = new TreeSet<Integer>();
            for (String symbol : symbols) {
                DataInfo di = DataManager.getDataInfo((String)"History", (String)symbol);
                if (di == null) {
                    Log.error(String.format("Symbol with name '%s' doesn't exist.", symbol));
                    continue;
                }
                elData.addContent((Content)di.getXML());
                usedBrokerIds.add(di.brokerId);
                usedBrokerIds.add(di.symbolInfo.broker);
            }
            for (Integer brokerId : usedBrokerIds) {
                if (brokerId == -1) continue;
                BrokerDto broker = BrokerManager.getInstance().getBroker(brokerId);
                elData.addContent((Content)ProjectResources.createBrokerElement((BrokerDto)broker));
            }
            XMLUtil.xmlToFile((Element)elData, (File)file);
            response.put("success", (Object)L.t((String)"Data saved.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Cannot save data.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onConfirm(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String action = args.get("action")[0];
            DataManagerConfirm.get().setConfirmedAction(action);
        }
        catch (Exception ex) {
            return DataServlet.apiErrorJSON((String)L.t((String)"Confirmation failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Action confirmed.", (Object[])new Object[0]));
        return response.toString();
    }
}

