/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.imports.AvailableDataFormats
 *  com.strategyquant.datalib.data.imports.CsvFileReader
 *  com.strategyquant.datalib.data.imports.CustomDataFormat
 *  com.strategyquant.datalib.data.imports.DataColumns
 *  com.strategyquant.datalib.data.imports.DataImportEngine
 *  com.strategyquant.datalib.data.io.ImportDataInfo
 *  com.strategyquant.datalib.data.io.MassImportDataInfo
 *  com.strategyquant.datalib.data.io.MassImportDataInfo$OverwriteStrategy
 *  com.strategyquant.datalib.data.io.columns.DefaultCol
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.time.DateFormats
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.qdm.QDM
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Files;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.imports.AvailableDataFormats;
import com.strategyquant.datalib.data.imports.CsvFileReader;
import com.strategyquant.datalib.data.imports.CustomDataFormat;
import com.strategyquant.datalib.data.imports.DataColumns;
import com.strategyquant.datalib.data.imports.DataImportEngine;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.datalib.data.io.MassImportDataInfo;
import com.strategyquant.datalib.data.io.columns.DefaultCol;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.time.DateFormats;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.plugin.DataSource.impl.Files.job.DataAppImporterJob;
import com.strategyquant.plugin.DataSource.impl.Files.job.DataImporterJob;
import com.strategyquant.plugin.DataSource.impl.Files.job.DataMassImporterMasterJob;
import com.strategyquant.qdm.QDM;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataSourceFilesServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(DataSourceFilesServlet.class);
    private boolean canceled = false;

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "add": {
                return this.onAdd(args);
            }
            case "import": {
                return this.onImportData(args);
            }
            case "importAction": {
                return this.onImportAction(args);
            }
            case "importGetInfo": {
                return this.onImportGetInfo();
            }
            case "importSaveNewDataFormat": {
                return this.onImportSaveNewDataFormat(args);
            }
            case "importDeleteDataFormat": {
                return this.onImportDeleteDataFormat(args);
            }
            case "importUpdateDataFormat": {
                return this.onImportUpdateDataFormat(args);
            }
            case "importGetOverview": {
                return this.onImportGetOverview(args);
            }
            case "appImport": {
                return this.onAppImport(args);
            }
            case "cancelAppImport": {
                return this.onCancelAppImportAction(args);
            }
            case "massImport": {
                return this.onMassImport(args);
            }
            case "cancelMassImport": {
                return this.onCancelMassImportAction(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onAppImport(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String license = null;
        String directory = null;
        try {
            license = this.tryGetParam(args, "license")[0];
            directory = this.tryGetParam(args, "path")[0];
        }
        catch (Exception e) {
            return DataSourceFilesServlet.apiErrorJSON((String)L.t((String)"Cannot import data.", (Object[])new Object[0]), (Throwable)e);
        }
        String ident = "DataAppImportJob";
        DataAppImporterJob job = new DataAppImporterJob(ident, directory, license);
        String errors = job.validate();
        if (errors != null) {
            return DataSourceFilesServlet.apiErrorJSON((String)L.t((String)errors, (Object[])new Object[0]), null);
        }
        SQGrid.getGridClient().executeOnGrid(ident, (GridJob)job);
        response.put("success", (Object)L.t((String)"Importing data.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCancelAppImportAction(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String ident = "DataAppImportJob";
        SQGrid.getGridClient().stop(ident);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onMassImport(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        this.canceled = false;
        MassImportDataInfo info = new MassImportDataInfo();
        info.setDateFormat(this.tryGetParam(args, "dateFormat")[0]);
        info.setPath(this.tryGetParam(args, "path")[0]);
        info.setConnection(this.tryGetParam(args, "connection")[0]);
        info.setBarType(Integer.parseInt(this.tryGetParam(args, "barType")[0]));
        info.setOverwriteStrategy(MassImportDataInfo.OverwriteStrategy.valueOf((String)this.tryGetParam(args, "exists")[0]));
        info.setInstrument(this.tryGetParam(args, "instrument")[0]);
        info.setPostfix(this.tryGetParam(args, "postfix")[0]);
        info.setCreateStockGroup(Boolean.valueOf(this.tryGetParam(args, "createStockGroup")[0]).booleanValue());
        String timezone = this.tryGetParam(args, "timezone")[0];
        info.setTimezone(timezone);
        MainApp.settings().set("timezone", timezone);
        String timeframe = this.tryGetParam(args, "timeframe")[0];
        info.setTimeframe(timeframe);
        String ident = "DataMassImportJob";
        DataMassImporterMasterJob job = new DataMassImporterMasterJob(ident, info);
        if (!job.hasFilesToImport()) {
            return DataSourceFilesServlet.apiErrorJSON((String)L.t((String)"There is nothing to import.", (Object[])new Object[0]), null);
        }
        SQGrid.getGridClient().executeOnGrid(ident, (GridJob)job);
        response.put("success", (Object)L.t((String)"Import symbols.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCancelMassImportAction(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String ident = "DataMassImportJob";
        SQGrid.getGridClient().stop(ident);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onAdd(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String connection = this.tryGetParam(args, "connection")[0];
            String symbol = this.tryGetParam(args, "symbol")[0];
            String instrument = this.tryGetParam(args, "instrument")[0];
            int barType = Integer.parseInt(this.tryGetParam(args, "barType")[0]);
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
            if (dataInfo != null) {
                throw new Exception(L.t((String)"Symbol with name '%s' already exists.", (Object[])new Object[]{symbol}));
            }
            int brokerId = -1;
            if (InstrumentManager.checkInstrumentExists((String)instrument)) {
                InstrumentInfo instrumentInfo = InstrumentManager.getInstrumentInfo((String)instrument);
                brokerId = instrumentInfo.broker;
            }
            DataManager.addData((String)connection, (String)symbol, (String)instrument, (int)barType, (int)1, (int)-1, (int)brokerId);
            this.sendDataUpdate(symbol, "add");
        }
        catch (Exception e) {
            return DataSourceFilesServlet.apiErrorJSON((String)L.t((String)"Cannot add data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportGetInfo() {
        JSONObject response = new JSONObject();
        JSONObject importInfo = new JSONObject();
        JSONArray fileFormats = new JSONArray();
        JSONObject customObj = new JSONObject();
        customObj.put("skipColumns", (Object)"0");
        customObj.put("skipRows", (Object)"0");
        customObj.put("dateFormat", DateFormats.getInstance().getAvailableDateFormats().get(0));
        customObj.put("separator", (Object)",");
        customObj.put("name", (Object)"Custom");
        fileFormats.put((Object)customObj);
        for (CustomDataFormat format : AvailableDataFormats.getInstance().getAvailableFileFormats()) {
            JSONObject formatObj = new JSONObject();
            formatObj.put("columnTypes", (Object)this.listColumnTypes(format.getColumns()));
            formatObj.put("skipColumns", format.getSkipColumns());
            formatObj.put("skipRows", format.getSkipRows());
            formatObj.put("dateFormat", (Object)format.getDateFormat());
            formatObj.put("separator", (Object)format.getSeparator());
            formatObj.put("name", (Object)format.getName());
            formatObj.put("predefined", format.isPredefined());
            fileFormats.put((Object)formatObj);
        }
        importInfo.put("fileFormats", (Object)fileFormats);
        JSONArray dateFormats = new JSONArray();
        Calendar exampleDate = Calendar.getInstance();
        exampleDate.set(2016, 6, 21, 8, 15, 22);
        exampleDate.set(14, 250);
        long exampleTime = exampleDate.getTimeInMillis();
        for (int i = 0; i < DateFormats.getInstance().getAvailableDateFormats().size(); ++i) {
            JSONObject dateObj = new JSONObject();
            String pattern = (String)DateFormats.getInstance().getAvailableDateFormats().get(i);
            dateObj.put("pattern", (Object)pattern);
            dateObj.put("example", pattern.equals("Long (millis from epoch)") || pattern.equals("Long (seconds from epoch)") ? Long.valueOf(exampleTime) : SQUtils.formatDate((long)exampleTime, (String)pattern));
            dateFormats.put((Object)dateObj);
        }
        importInfo.put("dateFormats", (Object)dateFormats);
        response.put("importInfo", (Object)importInfo);
        response.put("success", (Object)L.t((String)"Timezones listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportGetOverview(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String filePath = this.tryGetParam(args, "filePath")[0];
            String custom = this.tryGetParam(args, "customFormat")[0];
            String separator = this.tryGetParam(args, "separator")[0];
            int skipRows = Integer.parseInt(this.tryGetParam(args, "skipRows")[0]);
            int skipCols = Integer.parseInt(this.tryGetParam(args, "skipColumns")[0]);
            boolean customFormat = custom.equals("true");
            boolean recognizeSettings = false;
            String fileFormat = null;
            try {
                fileFormat = this.tryGetParam(args, "fileFormat")[0];
            }
            catch (Exception exception) {
                // empty catch block
            }
            CustomDataFormat format = null;
            ImportDataInfo importInfo = new ImportDataInfo();
            importInfo.filePath = filePath;
            importInfo.rowCount = 10;
            if (customFormat) {
                importInfo.separator = separator;
                importInfo.skipRows = skipRows;
                importInfo.skipCols = skipCols;
            } else {
                try {
                    if (fileFormat != null) {
                        format = AvailableDataFormats.getInstance().findFileFormatByName(fileFormat);
                    }
                    if (format == null) {
                        ArrayList formats = AvailableDataFormats.getInstance().getAvailableFileFormats();
                        format = DataImportEngine.getFileFormat((String)filePath, (ArrayList)formats, (CustomDataFormat)((CustomDataFormat)formats.get(0)));
                    }
                    JSONObject formatObj = new JSONObject();
                    formatObj.put("skipColumns", format.getSkipColumns());
                    formatObj.put("skipRows", format.getSkipRows());
                    formatObj.put("dateFormat", (Object)format.getDateFormat());
                    formatObj.put("separator", (Object)format.getSeparator());
                    formatObj.put("name", (Object)format.getName());
                    formatObj.put("columnTypes", (Object)this.listColumnTypes(format.getColumns()));
                    response.put("format", (Object)formatObj);
                    importInfo.name = format.getName();
                    importInfo.skipRows = format.getSkipRows();
                    importInfo.skipCols = format.getSkipColumns();
                    importInfo.separator = format.getSeparator();
                }
                catch (Exception e) {
                    Log.error("Cannot recognize file format. ", (Throwable)e);
                    importInfo.skipRows = 0;
                    importInfo.skipCols = 0;
                    recognizeSettings = true;
                }
            }
            CsvFileReader reader = new CsvFileReader(importInfo);
            String[][] data = reader.read(Boolean.valueOf(recognizeSettings));
            String firstDate = null;
            JSONArray linesObj = new JSONArray();
            if (data != null && data.length > 0) {
                for (String[] line : data) {
                    JSONArray lineObj = new JSONArray();
                    for (String value : line) {
                        if (firstDate == null) {
                            firstDate = value;
                        }
                        lineObj.put((Object)value);
                    }
                    linesObj.put((Object)(format == null ? lineObj : this.fillMissingValues(format, lineObj)));
                }
            }
            if (recognizeSettings) {
                JSONObject formatObj = new JSONObject();
                formatObj.put("custom", true);
                formatObj.put("separator", (Object)reader.getSeparator());
                formatObj.put("skipRows", importInfo.skipRows);
                String dateFormat = DateFormats.getInstance().recognize(firstDate);
                if (dateFormat != null) {
                    formatObj.put("dateFormat", (Object)dateFormat);
                }
                response.put("format", (Object)formatObj);
            }
            response.put("overviewData", (Object)linesObj);
        }
        catch (Exception e) {
            return DataSourceFilesServlet.apiErrorJSON((String)L.t((String)"Cannot get file overview.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"File overview returned.", (Object[])new Object[0]));
        return response.toString();
    }

    private JSONArray fillMissingValues(CustomDataFormat format, JSONArray lineObj) {
        int i = 1;
        Iterator iterator = format.getColumns().keySet().iterator();
        while (iterator.hasNext()) {
            int key = (Integer)iterator.next();
            if (lineObj.length() < i) {
                lineObj.put((Object)"");
            }
            ++i;
        }
        return lineObj;
    }

    private String onImportData(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String[] cols;
            String connectionName = this.tryGetParam(args, "connectionName")[0];
            String symbol = this.tryGetParam(args, "symbol")[0];
            String timezone = this.tryGetParam(args, "timezone")[0];
            MainApp.settings().set("timezone", timezone);
            ImportDataInfo importInfo = new ImportDataInfo();
            importInfo.name = this.tryGetParam(args, "fileFormat")[0];
            importInfo.filePath = this.tryGetParam(args, "filePath")[0];
            importInfo.dateFormat = this.tryGetParam(args, "dateFormat")[0];
            importInfo.separator = this.tryGetParam(args, "separator")[0];
            importInfo.skipRows = Integer.parseInt(this.tryGetParam(args, "skipRows")[0]);
            importInfo.skipCols = Integer.parseInt(this.tryGetParam(args, "skipColumns")[0]);
            importInfo.errorHandling = Integer.parseInt(this.tryGetParam(args, "errorHandling")[0]);
            importInfo.timezone = timezone;
            String timeframe = this.tryGetParam(args, "timeframe")[0];
            importInfo.timeframe = timeframe.equals("auto") ? null : timeframe;
            CustomDataFormat format = AvailableDataFormats.getInstance().findFileFormatByName(importInfo.name);
            if (format != null) {
                importInfo.timeFormat = format.getTimeFormat();
            }
            ArrayList<DefaultCol> columns = new ArrayList<DefaultCol>();
            for (String col : cols = this.tryGetParam(args, "columnTypes")[0].split(",")) {
                columns.add(DataColumns.getInstance().findColTypeByName(col));
            }
            importInfo.columnTypes = columns;
            QDM.getInstance().activity.increase(5);
            MultiProgressListener listener = DataManagerDataProgress.get().createListener(symbol, "dataSourceFiles/importAction");
            String ident = "DataImportFromFile_" + symbol;
            DataImporterJob job = new DataImporterJob(symbol, ident, (IProgressListener)listener, DataManager.getDataInfo((String)connectionName, (String)symbol), importInfo);
            SQGrid.getGridClient().executeOnGrid(ident, (GridJob)job);
            if (this.getParam(args, "waitForFinish", "false").equals("true")) {
                SQGrid.getGridClient().waitForFinish((Object)this, null, null, ident);
            }
        }
        catch (Exception e) {
            return DataSourceFilesServlet.apiErrorJSON((String)L.t((String)"Cannot import data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Importing data.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportAction(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbol", "action"});
        String symbol = this.tryGetParam(args, "symbol")[0];
        String action = this.tryGetParam(args, "action")[0];
        JSONObject response = new JSONObject();
        String ident = "DataImportFromFile_" + symbol;
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

    private String onImportSaveNewDataFormat(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(args, "name")[0];
            CustomDataFormat newFormat = this.getFileFormat(args);
            if (AvailableDataFormats.getInstance().formatExists(name)) {
                throw new Exception(L.t((String)"Data format with name '%s' already exists. Please choose another name.", (Object[])new Object[]{name}));
            }
            AvailableDataFormats.getInstance().addDataFormat(newFormat);
        }
        catch (Exception e) {
            return DataSourceFilesServlet.apiErrorJSON((String)L.t((String)"Cannot save custom data format.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data format saved", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportDeleteDataFormat(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(args, "name")[0];
            AvailableDataFormats.getInstance().deleteDataFormat(name);
        }
        catch (Exception e) {
            return DataSourceFilesServlet.apiErrorJSON((String)L.t((String)"Cannot delete custom data format.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data format deleted", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportUpdateDataFormat(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            AvailableDataFormats.getInstance().updateDataFormat(this.getFileFormat(args));
        }
        catch (Exception e) {
            return DataSourceFilesServlet.apiErrorJSON((String)L.t((String)"Cannot update custom data format.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data format updated", (Object[])new Object[0]));
        return response.toString();
    }

    private CustomDataFormat getFileFormat(Map<String, String[]> args) throws Exception {
        CustomDataFormat newFormat = new CustomDataFormat();
        newFormat.setName(this.tryGetParam(args, "name")[0]);
        newFormat.setSeparator(this.tryGetParam(args, "separator")[0]);
        newFormat.setSkipColumns(Integer.parseInt(this.tryGetParam(args, "skipColumns")[0]));
        newFormat.setSkipRows(Integer.parseInt(this.tryGetParam(args, "skipRows")[0]));
        newFormat.setDateFormat(this.tryGetParam(args, "dateFormat")[0]);
        newFormat.setPredefined(false);
        HashMap<Integer, DefaultCol> columns = new HashMap<Integer, DefaultCol>();
        String[] columnTypes = this.tryGetParam(args, "columnTypes")[0].split(",");
        for (int a = 0; a < columnTypes.length; ++a) {
            DefaultCol columnType = DataColumns.getInstance().findColTypeByName(columnTypes[a]);
            if (columnType == null) {
                if (columnTypes[a].startsWith("Choose")) {
                    throw new Exception(L.t((String)"Column no. %d not set.", (Object[])new Object[]{a + 1}));
                }
                throw new Exception(L.t((String)"Unknown column '%s'.", (Object[])new Object[]{columnTypes[a]}));
            }
            columns.put(a, columnType);
        }
        newFormat.setColumns(columns);
        return newFormat;
    }

    private JSONArray listColumnTypes(HashMap<Integer, DefaultCol> columns) {
        JSONArray columnTypes = new JSONArray();
        for (int key : columns.keySet()) {
            DefaultCol col = columns.get(key);
            columnTypes.put((Object)col.getName());
        }
        return columnTypes;
    }

    private void sendDataUpdate(String symbols, String action) {
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)symbols, (String)action), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            Log.error("Cannot send websocket data update. ", (Throwable)e);
        }
    }
}

