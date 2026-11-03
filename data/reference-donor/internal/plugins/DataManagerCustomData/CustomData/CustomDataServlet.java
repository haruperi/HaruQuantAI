/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.AvailableCustomDataFormats
 *  com.strategyquant.datalib.customData.CustomData
 *  com.strategyquant.datalib.customData.CustomDataBinReader
 *  com.strategyquant.datalib.customData.CustomDataBinWriter
 *  com.strategyquant.datalib.customData.CustomDataCsv
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.datalib.data.imports.CsvFileReader
 *  com.strategyquant.datalib.data.imports.CustomDataFormat
 *  com.strategyquant.datalib.data.imports.DataColumns
 *  com.strategyquant.datalib.data.imports.DataImportEngine
 *  com.strategyquant.datalib.data.io.ImportDataInfo
 *  com.strategyquant.datalib.data.io.columns.CustomValue
 *  com.strategyquant.datalib.data.io.columns.DateCol
 *  com.strategyquant.datalib.data.io.columns.DefaultCol
 *  com.strategyquant.datalib.data.io.columns.TimeCol
 *  com.strategyquant.datalib.data.io.columns.UnusedCol
 *  com.strategyquant.datalib.indicators.SCustomIndicator
 *  com.strategyquant.datalib.indicators.SCustomIndicatorFileParser
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.time.DateFormats
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.qdm.QDM
 *  com.strategyquant.tradinglib.cot.CotData
 *  com.strategyquant.tradinglib.cot.CotManager
 *  com.strategyquant.tradinglib.cot.CotRecord
 *  com.strategyquant.tradinglib.project.console.CLILogger
 *  com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender
 *  com.strategyquant.tradinglib.project.websocket.DataManagerConfirm
 *  com.strategyquant.tradinglib.project.websocket.DataManagerCustomDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.CustomData;

import com.strategyquant.datalib.customData.AvailableCustomDataFormats;
import com.strategyquant.datalib.customData.CustomData;
import com.strategyquant.datalib.customData.CustomDataBinReader;
import com.strategyquant.datalib.customData.CustomDataBinWriter;
import com.strategyquant.datalib.customData.CustomDataCsv;
import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.datalib.data.imports.CsvFileReader;
import com.strategyquant.datalib.data.imports.CustomDataFormat;
import com.strategyquant.datalib.data.imports.DataColumns;
import com.strategyquant.datalib.data.imports.DataImportEngine;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.datalib.data.io.columns.CustomValue;
import com.strategyquant.datalib.data.io.columns.DateCol;
import com.strategyquant.datalib.data.io.columns.DefaultCol;
import com.strategyquant.datalib.data.io.columns.TimeCol;
import com.strategyquant.datalib.data.io.columns.UnusedCol;
import com.strategyquant.datalib.indicators.SCustomIndicator;
import com.strategyquant.datalib.indicators.SCustomIndicatorFileParser;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.time.DateFormats;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.plugin.DataManager.impl.CustomData.job.CustomDataImporterJob;
import com.strategyquant.qdm.QDM;
import com.strategyquant.tradinglib.cot.CotData;
import com.strategyquant.tradinglib.cot.CotManager;
import com.strategyquant.tradinglib.cot.CotRecord;
import com.strategyquant.tradinglib.project.console.CLILogger;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerConfirm;
import com.strategyquant.tradinglib.project.websocket.DataManagerCustomDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CustomDataServlet
extends HttpJSONServlet {
    private static final long serialVersionUID = 1L;
    private static final Logger Log = LoggerFactory.getLogger(CustomDataServlet.class);
    private static final String[] COT_OUTPUTS = new String[]{"cpihedg", "ctihedg", "cpispec", "ctispec", "cpismall"};

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "list": {
                return this.onList(args);
            }
            case "add": {
                return this.onAdd(args);
            }
            case "edit": {
                return this.onEdit(args);
            }
            case "clear": {
                return this.onClear(args);
            }
            case "remove": {
                return this.onRemove(args);
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
            case "importcli": {
                return this.onImportDataCli(args);
            }
            case "recognizeFromFile": {
                return this.onRecognizeFromFile(args);
            }
            case "reviewData": {
                return this.onReviewData(args);
            }
            case "load": {
                return this.onLoad(args);
            }
            case "save": {
                return this.onSave(args);
            }
            case "exportValues": {
                return this.onExportValues(args);
            }
            case "updateCot": {
                return this.onUpdateCot();
            }
        }
        throw new Exception(L.t((String)"Unknown command '%s'.", (Object[])new Object[]{command}));
    }

    private String onRecognizeFromFile(Map<String, String[]> args) throws Exception {
        SCustomIndicator cIndy;
        JSONObject response = new JSONObject();
        String filePath = this.tryGetParam(args, "filePath")[0];
        try {
            File f = new File(filePath);
            if (!f.exists()) {
                throw new Exception(L.t((String)"File doesn't exist.", (Object[])new Object[0]));
            }
            cIndy = SCustomIndicatorFileParser.parse((File)f);
            CustomDataManager.add((SCustomIndicator)cIndy);
            this.sendDataUpdate(cIndy.shortName, "add");
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"Failed to recognize custom indicator from file. Reason: %s", (Object[])new Object[]{e.getMessage()}));
        }
        response.put("success", (Object)L.t((String)"Indicator '%s' added.", (Object[])new Object[]{cIndy.shortName}));
        return response.toString();
    }

    private String onReviewData(Map<String, String[]> parameterMap) throws Exception {
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
        String name = parameterMap.get("name")[0].toString();
        CustomDataInfo dataInfo = CustomDataManager.getDataInfo((String)name);
        if (dataInfo == null) {
            throw new Exception(L.t((String)"Indicator with name '%s' doesn't exist.", (Object[])new Object[]{name}));
        }
        JSONArray rows = new JSONArray();
        CustomDataBinReader reader = new CustomDataBinReader(dataInfo);
        reader.open();
        long i = 0L;
        long loaded = 0L;
        while (reader.hasNextData()) {
            reader.loadData();
            if (i < (long)posStart) {
                ++i;
                continue;
            }
            if (loaded >= (long)count) break;
            CustomData loadedData = reader.loadedData;
            JSONArray rowData = new JSONArray();
            rowData.put((Object)SQTime.toFullDateMinuteString((long)loadedData.time));
            for (int v = 0; v < loadedData.values.length; ++v) {
                rowData.put(loadedData.values[v]);
            }
            JSONObject row = new JSONObject();
            row.put("id", (Object)("r" + ((long)posStart + i)));
            row.put("data", (Object)rowData);
            rows.put((Object)row);
            ++loaded;
        }
        reader.close();
        response.put("total_count", dataInfo.rows);
        response.put("rows", (Object)rows);
        response.put("pos", posStart);
        response.put("success", (Object)L.t((String)"Data listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onList(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            DataToSend dataToSend = WSDataObjects.getCustomData((String)"", (String)"list");
            if (MainApp.runInConsoleWithoutActiveWebserver()) {
                JSONArray data = dataToSend.getDataObject().getJSONArray("data");
                for (int i = 0; i < data.length(); ++i) {
                    JSONObject object = data.getJSONObject(i);
                    CLILogger.log((String)String.format("External indicator %d: %s => %s", i, object.getString("name"), object.toString()));
                }
            } else {
                SQWebSocketManager.addToDataQueue((DataToSend)dataToSend, (String[])new String[]{"SQUANT", "QDM"});
            }
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot get list of indicators.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Indicators listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onAdd(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(args, "name")[0];
            String values = this.tryGetParam(args, "values")[0];
            int dataType = Integer.parseInt(this.tryGetParam(args, "type")[0]);
            if (name.trim().isEmpty()) {
                throw new Exception(L.t((String)"Name cannot be empty", (Object[])new Object[0]));
            }
            CustomDataInfo dataInfo = CustomDataManager.getDataInfo((String)name);
            if (dataInfo != null) {
                throw new Exception(L.t((String)"Custom data with name '%s' already exists.", (Object[])new Object[]{name}));
            }
            CustomDataManager.add((String)name, (String)values, (int)dataType);
            this.sendDataUpdate(name, "add");
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot add indicator.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Indicator added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onEdit(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String oldName = this.tryGetParam(args, "oldName")[0];
        String newName = this.tryGetParam(args, "name")[0];
        String values = this.tryGetParam(args, "values")[0];
        int dataType = Integer.parseInt(this.tryGetParam(args, "type")[0]);
        if (newName.trim().isEmpty()) {
            throw new Exception(L.t((String)"Name cannot be empty", (Object[])new Object[0]));
        }
        if (!oldName.equals(newName)) {
            throw new Exception(L.t((String)"Custom indicator cannot be renamed", (Object[])new Object[0]));
        }
        CustomDataInfo dataInfo = CustomDataManager.getDataInfo((String)oldName);
        if (dataInfo == null) {
            throw new Exception(L.t((String)"Indicator with name '%s' doesn't exist.", (Object[])new Object[]{oldName}));
        }
        CustomDataManager.update((String)oldName, (String)newName, (String)values, (int)dataType);
        this.sendDataUpdate(newName, "update");
        response.put("success", (Object)L.t((String)"Indicator updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onClear(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String[] data = this.tryGetParam(args, "data")[0].split(",");
            for (int a = 0; a < data.length; ++a) {
                CustomDataManager.clear((String)data[a]);
            }
            this.sendDataUpdate(this.tryGetParam(args, "data")[0], "clear");
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot clear indicator data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Indicator data cleared.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemove(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String[] data = this.tryGetParam(args, "data")[0].split(",");
            for (int a = 0; a < data.length; ++a) {
                CustomDataManager.delete((String)data[a]);
            }
            this.sendDataUpdate(this.tryGetParam(args, "data")[0], "remove");
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot remove indicator.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Indicator removed.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onUpdateCot() {
        JSONObject response = new JSONObject();
        ArrayList<String> names = new ArrayList<String>();
        JSONObject progress = new JSONObject();
        try {
            progress.put("percent", 0);
            progress.put("info", (Object)L.t((String)"Downloading COT data", (Object[])new Object[0]));
            DataManagerAddProgressSender.getInstance().sendData(progress);
            List cotDataList = CotManager.getInstance().sync();
            if (cotDataList == null) {
                throw new Exception(L.t((String)"Cannot download COT data.", (Object[])new Object[0]));
            }
            try {
                File csvOutputDir = new File(SQPaths.customDataDirPath + "/Tradestation");
                int csvCount = CotManager.getInstance().exportIndividualCsvs(cotDataList, csvOutputDir);
                Log.info("COT CSV export: {} files written to {}", (Object)csvCount, (Object)csvOutputDir.getAbsolutePath());
            }
            catch (Exception e) {
                Log.error("COT CSV export failed (continuing with indicator creation)", (Throwable)e);
            }
            long total = cotDataList.size();
            long index = 0L;
            for (CotData cotData : cotDataList) {
                String name = CustomDataServlet.importCot(cotData);
                names.add(name);
                Integer percent = SQUtils.round((double)(100.0 * (double)index / (double)total));
                progress.put("percent", (Object)percent);
                progress.put("info", (Object)L.t((String)"Adding '%s'", (Object[])new Object[]{name}));
                DataManagerAddProgressSender.getInstance().sendData(progress);
                ++index;
            }
            this.sendDataUpdate(String.join((CharSequence)",", names), "add");
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getCotList(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            String string = CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot update COT indicators.", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            progress.put("percent", 100);
            DataManagerAddProgressSender.getInstance().sendData(progress);
        }
        response.put("success", (Object)L.t((String)"COT indicators (%d) updated.", (Object[])new Object[]{names.size()}));
        return response.toString();
    }

    public static String importCot(CotData cotData) throws Exception {
        String name = CotManager.getInstance().getDataName(cotData.getName());
        if (CustomDataManager.checkDataExists((String)name)) {
            CustomDataManager.delete((String)name);
        }
        String values = CustomDataServlet.createCotValuesObject(cotData.getName());
        CustomDataManager.add((String)name, (String)values, (int)2);
        CustomDataServlet.writeCotData(name, cotData);
        return name;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static void writeCotData(String name, CotData cotData) throws Exception {
        CustomDataInfo dataInfo = CustomDataManager.getDataInfo((String)name);
        if (dataInfo == null) {
            throw new Exception(L.t((String)"Indicator with name '%s' doesn't exist.", (Object[])new Object[]{name}));
        }
        ArrayList records = new ArrayList(cotData.getRecords());
        Collections.sort(records, new Comparator<CotRecord>(){

            @Override
            public int compare(CotRecord record1, CotRecord record2) {
                return record1.getDate().compareTo(record2.getDate());
            }
        });
        CustomDataBinWriter writer = new CustomDataBinWriter();
        writer.setFileName(CustomDataManager.getDataFileName((String)name));
        writer.open();
        CustomData data = new CustomData(dataInfo.values);
        long dateFrom = 0L;
        long dateTo = 0L;
        int rows = 0;
        try {
            for (CotRecord record : records) {
                long time;
                data.time = time = record.getDate().getTime();
                CustomDataServlet.fillCotValues(data.values, record);
                writer.writeData(data);
                if (rows == 0) {
                    dateFrom = time;
                }
                dateTo = time;
                ++rows;
            }
        }
        finally {
            writer.close();
        }
        CustomDataManager.updateData((String)name, (long)dateFrom, (long)dateTo, (int)rows, (String)"Weekly");
    }

    private static void fillCotValues(double[] values, CotRecord record) {
        values[0] = CustomDataServlet.notNaN(record.getCpihedg());
        values[1] = CustomDataServlet.notNaN(record.getCtihedg());
        values[2] = CustomDataServlet.notNaN(record.getCpispec());
        values[3] = CustomDataServlet.notNaN(record.getCtispec());
        values[4] = CustomDataServlet.notNaN(record.getCpismall());
    }

    private static double notNaN(double value) {
        return Double.isNaN(value) ? 0.0 : value;
    }

    public static String createCotValuesObject(String cotKey) {
        JSONArray values = new JSONArray();
        for (int i = 0; i < COT_OUTPUTS.length; ++i) {
            String outputName = COT_OUTPUTS[i];
            JSONObject output = new JSONObject();
            output.put("name", (Object)outputName);
            output.put("mt4", (Object)String.format("iCustom(NULL, 0, \"SqCOT\", \"%s\", %d, %d, #Shift#)", cotKey, i, i));
            output.put("mt5", (Object)String.format("iCustom(NULL, 0, \"SqCOT\", \"%s\", %d)", cotKey, i));
            output.put("el", (Object)CustomDataManager.cotELCode((String)cotKey, (int)i));
            values.put((Object)output);
        }
        return values.toString();
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
        for (CustomDataFormat format : AvailableCustomDataFormats.getInstance().getAvailableFileFormats()) {
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
        response.put("success", (Object)"ok");
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
                        format = AvailableCustomDataFormats.getInstance().findFileFormatByName(fileFormat);
                    }
                    if (format == null) {
                        ArrayList formats = AvailableCustomDataFormats.getInstance().getAvailableFileFormats();
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
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot get file overview.", (Object[])new Object[0]), (Throwable)e);
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
            String data = this.tryGetParam(args, "data")[0];
            ImportDataInfo importInfo = new ImportDataInfo();
            importInfo.name = this.tryGetParam(args, "fileFormat")[0];
            importInfo.filePath = this.tryGetParam(args, "filePath")[0];
            importInfo.dateFormat = this.tryGetParam(args, "dateFormat")[0];
            importInfo.separator = this.tryGetParam(args, "separator")[0];
            importInfo.skipRows = Integer.parseInt(this.tryGetParam(args, "skipRows")[0]);
            importInfo.skipCols = Integer.parseInt(this.tryGetParam(args, "skipColumns")[0]);
            importInfo.errorHandling = Integer.parseInt(this.tryGetParam(args, "errorHandling")[0]);
            CustomDataFormat format = AvailableCustomDataFormats.getInstance().findFileFormatByName(importInfo.name);
            if (format != null) {
                importInfo.timeFormat = format.getTimeFormat();
            }
            ArrayList<DefaultCol> columns = new ArrayList<DefaultCol>();
            for (String col : cols = this.tryGetParam(args, "columnTypes")[0].split(",")) {
                columns.add(DataColumns.getInstance().findColTypeByName(col));
            }
            importInfo.columnTypes = columns;
            QDM.getInstance().activity.increase(5);
            MultiProgressListener listener = DataManagerCustomDataProgress.get().createListener(data, "customdata/importAction");
            String ident = "CustomDataImport_" + data;
            CustomDataImporterJob job = new CustomDataImporterJob(ident, (IProgressListener)listener, CustomDataManager.getDataInfo((String)data), importInfo);
            SQGrid.getGridClient().executeOnGrid(ident, (GridJob)job);
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot import data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Importing indicator data.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportAction(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"data", "action"});
        String data = this.tryGetParam(args, "data")[0];
        String action = this.tryGetParam(args, "action")[0];
        JSONObject response = new JSONObject();
        String ident = "CustomDataImport_" + data;
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
            if (AvailableCustomDataFormats.getInstance().formatExists(name)) {
                throw new Exception(L.t((String)"Data format with name '%s' already exists. Please choose another name.", (Object[])new Object[]{name}));
            }
            AvailableCustomDataFormats.getInstance().addDataFormat(newFormat);
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot save indicator data format.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data format saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportDeleteDataFormat(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(args, "name")[0];
            AvailableCustomDataFormats.getInstance().deleteDataFormat(name);
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot delete indicator data format.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data format deleted.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportUpdateDataFormat(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            AvailableCustomDataFormats.getInstance().updateDataFormat(this.getFileFormat(args));
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot update indicator data format.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data format updated.", (Object[])new Object[0]));
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

    private void sendDataUpdate(String names, String action) {
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getCustomData((String)names, (String)action), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            Log.error("Cannot send websocket data update. ", (Throwable)e);
        }
    }

    private String onLoad(Map<String, String[]> args) {
        try {
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            ArrayList<String> names = new ArrayList<String>();
            Element elIndicators = XMLUtil.fileToXmlElement((File)file);
            if (!elIndicators.getName().equals("ExternalIndicators")) {
                throw new Exception(L.t((String)"No Indicators found to import.", (Object[])new Object[0]));
            }
            for (Element elIndicator : elIndicators.getChildren("IndicatorDataInfo")) {
                CustomDataInfo dataInfoLoaded = new CustomDataInfo();
                dataInfoLoaded.setFromXML(elIndicator);
                if (!CustomDataManager.checkDataExists((String)dataInfoLoaded.name)) {
                    CustomDataManager.add((CustomDataInfo)dataInfoLoaded);
                    names.add(dataInfoLoaded.name);
                    continue;
                }
                DataManagerConfirm.get().awaitConfirmation(L.t((String)"Overwrite confirm", (Object[])new Object[0]), L.t((String)"Indicator '%s' already exists, do you want to overwrite it with the imported one?", (Object[])new Object[]{dataInfoLoaded.name}));
                String action = DataManagerConfirm.get().getConfirmedAction();
                if (action.equals("skip")) continue;
                if (action.equals("cancel")) break;
                if (!action.equals("overwrite")) continue;
                CustomDataManager.clear((String)dataInfoLoaded.name);
                CustomDataManager.update((CustomDataInfo)dataInfoLoaded);
                names.add(dataInfoLoaded.name);
            }
            this.sendDataUpdate(String.join((CharSequence)",", names), "add");
            response.put("success", (Object)L.t((String)"Indicators (%d) loaded.", (Object[])new Object[]{names.size()}));
            return response.toString();
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot load indicators.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onSave(Map<String, String[]> args) {
        try {
            String[] names;
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            Element elIndicators = new Element("ExternalIndicators");
            for (String name : names = this.tryGetParam(args, "data")[0].split(",")) {
                CustomDataInfo dataInfo = CustomDataManager.getDataInfo((String)name);
                elIndicators.addContent((Content)dataInfo.getXML());
            }
            XMLUtil.xmlToFile((Element)elIndicators, (File)file);
            response.put("success", (Object)L.t((String)"Indicators saved.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot save indicators.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onExportValues(Map<String, String[]> args) {
        try {
            String name = this.tryGetParam(args, "name")[0];
            String filePath = this.tryGetParam(args, "filePath")[0];
            CustomDataInfo dataInfo = CustomDataManager.getDataInfo((String)name);
            if (dataInfo == null) {
                throw new Exception(L.t((String)"Indicator with name '%s' doesn't exist.", (Object[])new Object[]{name}));
            }
            int rows = CustomDataCsv.write((CustomDataInfo)dataInfo, (File)new File(filePath));
            JSONObject response = new JSONObject();
            response.put("success", (Object)L.t((String)"%s - %s rows exported to '%s'", (Object[])new Object[]{name, rows + "", new File(filePath).getAbsolutePath()}));
            response.put("rows", rows);
            return response.toString();
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot export indicator values.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onImportDataCli(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(args, "name")[0];
            CustomDataInfo dataInfo = CustomDataManager.getDataInfo((String)name);
            if (dataInfo == null) {
                throw new Exception(L.t((String)"External indicator with name '%s' doesn't exist.", (Object[])new Object[]{name}));
            }
            ImportDataInfo importInfo = new ImportDataInfo();
            importInfo.name = "";
            importInfo.filePath = this.tryGetParam(args, "file")[0];
            importInfo.dateFormat = "dd/MM/yyyy";
            importInfo.timeFormat = "HH:mm:ss";
            importInfo.separator = ",";
            importInfo.skipRows = 0;
            importInfo.skipCols = 0;
            importInfo.errorHandling = 0;
            ArrayList<Object> columns = new ArrayList<Object>();
            columns.add(new DateCol());
            columns.add(new TimeCol());
            columns.add(new UnusedCol());
            columns.add(new UnusedCol());
            columns.add(new UnusedCol());
            columns.add(new UnusedCol());
            columns.add(new UnusedCol());
            for (int i = 0; i < dataInfo.values; ++i) {
                columns.add(new CustomValue(i));
            }
            importInfo.columnTypes = columns;
            MultiProgressListener listener = DataManagerCustomDataProgress.get().createListener(name, "customdata/importAction");
            String ident = "CustomDataImport_" + name;
            CustomDataImporterJob job = new CustomDataImporterJob(ident, (IProgressListener)listener, CustomDataManager.getDataInfo((String)name), importInfo);
            SQGrid.getGridClient().executeOnGrid(ident, (GridJob)job);
        }
        catch (Exception e) {
            return CustomDataServlet.apiErrorJSON((String)L.t((String)"Cannot import data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Importing external indicator data.", (Object[])new Object[0]));
        return response.toString();
    }
}

