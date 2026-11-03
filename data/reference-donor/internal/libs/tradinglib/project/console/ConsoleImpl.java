/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.imports.AvailableDataFormats
 *  com.strategyquant.datalib.data.imports.CustomDataFormat
 *  com.strategyquant.datalib.data.imports.DataImportEngine
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.L88OaFjjon.Tu5UdlpFO9
 *  com.strategyquant.lib.L88OaFjjon.V571hfnsHw
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.app.impl.IConsoleImpl
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  com.strategyquant.pluginlib.program.Program
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.console;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.imports.AvailableDataFormats;
import com.strategyquant.datalib.data.imports.CustomDataFormat;
import com.strategyquant.datalib.data.imports.DataImportEngine;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.L88OaFjjon.Tu5UdlpFO9;
import com.strategyquant.lib.L88OaFjjon.V571hfnsHw;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.app.impl.IConsoleImpl;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.project.console.CLILogger;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;
import java.util.StringTokenizer;
import java.util.stream.Collectors;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConsoleImpl
implements IConsoleImpl {
    public static final Logger Log = LoggerFactory.getLogger(ConsoleImpl.class);
    protected HashMap<String, String> parsedParams;
    protected String appName;
    protected String exeName;
    private int exitStatus = 0;
    String sqLogo = "  ____   _                _                        ___                        _    __  __\n / ___| | |_  _ __  __ _ | |_  ___   __ _  _   _  / _ \\  _   _   __ _  _ __  | |_  \\ \\/ /\n \\___ \\ | __|| '__|/ _` || __|/ _ \\ / _` || | | || | | || | | | / _` || '_ \\ | __|  \\  / \n  ___) || |_ | |  | (_| || |_|  __/| (_| || |_| || |_| || |_| || (_| || | | || |_   /  \\ \n |____/  \\__||_|   \\__,_| \\__|\\___| \\__, | \\__, | \\__\\_\\ \\__,_| \\__,_||_| |_| \\__| /_/\\_\\\n                                    |___/  |___/                                         ";
    String qdmLogo = "   ___   ____   __  __    \n  / _ \\ |  _ \\ |  \\/  |\n | | | || | | || |\\/| |  \n | |_| || |_| || |  | |   \n  \\__\\_\\|____/ |_|  |_|";

    public ConsoleImpl(String string, String string2) {
        this.appName = string;
        this.exeName = string2;
        MainApp.cli = this;
    }

    public void run(String[] stringArray) throws Exception {
        MainApp.AppLoaded = true;
        if (stringArray.length == 0 || stringArray.length == 1 && (stringArray[0].startsWith("liccheck") || stringArray[0].startsWith("license"))) {
            this.cli();
        } else if (stringArray.length == 1 && stringArray[0].equals("-gui")) {
            this.runCommand(new String[]{"-gui"});
            this.cli();
        } else {
            try {
                this.parsedParams = this.parseParams(stringArray);
                CLILogger.log("--------------------------------------------------");
                CLILogger.log(L.t((String)"Starting %s in command line mode.", (Object[])new Object[]{this.appName}));
                CLILogger.log(L.t((String)"Params: %s", (Object[])new Object[]{this.appArgsToString(stringArray)}));
                this.runCommand(stringArray);
            }
            catch (Exception exception) {
                this.exitStatus = 1;
                Log.error("Error: " + exception.getMessage(), (Throwable)exception);
                if (this.parsedParams != null && this.parsedParams.containsKey("-verbose")) {
                    CLILogger.log("Error: " + SQUtils.stackTraceToString((Throwable)exception));
                } else {
                    CLILogger.log("Error: " + exception.getMessage());
                }
            }
            finally {
                this.waitAndFinish();
            }
        }
    }

    private void cli() {
        new Thread(){

            @Override
            public void run() {
                Log.debug(MainApp.getProductName() + " CLI loaded in " + SQTime.formatDateTime((long)((System.currentTimeMillis() - MainApp.TimeAppStarted) / 1000L)));
                if (MainApp.checkProduct((String)"SQUANT")) {
                    CLILogger.log(ConsoleImpl.this.sqLogo);
                }
                CLILogger.log(L.t((String)"Welcome to %s Command Line Interface", (Object[])new Object[]{ConsoleImpl.this.appName}));
                CLILogger.log(L.t((String)"SQX CLI is now ready. Execute a command or type -h for assistance", (Object[])new Object[0]));
                Scanner scanner = new Scanner(System.in);
                while (scanner.hasNextLine()) {
                    try {
                        String[] stringArray;
                        String string = scanner.nextLine();
                        if (string.trim().isEmpty() || !(stringArray = ConsoleImpl.translateCommandline(string))[0].equalsIgnoreCase("-exit") && MainApp.CLIWebServeActive) continue;
                        ConsoleImpl.this.runCommand(stringArray);
                    }
                    catch (Exception exception) {
                        Log.error("Error: " + exception.getMessage(), (Throwable)exception);
                        if (ConsoleImpl.this.parsedParams != null && ConsoleImpl.this.parsedParams.containsKey("-verbose")) {
                            CLILogger.log("Error: " + SQUtils.stackTraceToString((Throwable)exception));
                            continue;
                        }
                        CLILogger.log("Error: " + exception.getMessage());
                    }
                }
            }
        }.start();
        MainApp.CLIInteractiveMode = true;
    }

    public void runCommand(String[] stringArray) throws Exception {
        this.parsedParams = this.parseParams(stringArray);
        switch (stringArray[0]) {
            case "-run": {
                this.run();
                break;
            }
            case "-symbol": {
                this.symbol();
                break;
            }
            case "-instrument": {
                this.instrument();
                break;
            }
            case "-data": {
                this.data();
                break;
            }
            case "-brokerprofile": {
                this.brokerProfile();
                break;
            }
            case "-license": {
                this.license();
                break;
            }
            case "-a": {
                this.addSymbol();
                break;
            }
            case "-e": {
                this.editSymbol();
                break;
            }
            case "-d": {
                this.deleteSymbol();
                break;
            }
            case "-c": {
                this.clearSymbolData();
                break;
            }
            case "-l": {
                this.listSymbols();
                break;
            }
            case "-ia": {
                this.addInstrument();
                break;
            }
            case "-ie": {
                this.editInstrument();
                break;
            }
            case "-id": {
                this.deleteInstrument();
                break;
            }
            case "-il": {
                this.listInstruments();
                break;
            }
            case "-u": {
                this.update();
                break;
            }
            case "-di": {
                this.dataImport();
                break;
            }
            case "-de": {
                this.dataExport();
                break;
            }
            case "-dc": {
                this.cloneData();
                break;
            }
            case "-tz": {
                this.listTimezones();
                break;
            }
            case "help": {
                this.help();
                break;
            }
            case "-help": {
                this.help();
                break;
            }
            case "-h": {
                this.help();
                break;
            }
            case "-gui": {
                MainApp.CLIWebServeActive = MainApp.initWebServer();
                if (!MainApp.CLIWebServeActive) break;
                Log.info("All other CLI commands are disabled.");
                break;
            }
            case "-deletefile": {
                this.deleteFile();
                break;
            }
            case "-waitfor": {
                this.waitFor();
                break;
            }
            case "-execute": {
                this.execute();
                break;
            }
            case "quit": 
            case "exit": 
            case "-exit": {
                this.exit();
                break;
            }
            default: {
                this.exitStatus = 1;
                CLILogger.log(L.t((String)"Unrecognized command %s. Specify -h for list of available options and commands.", (Object[])new Object[]{stringArray[0]}));
            }
        }
    }

    private Map<String, String[]> createParameterMap() {
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        for (String string : this.parsedParams.keySet()) {
            if (string.equals("action")) continue;
            String string2 = this.parsedParams.get(string);
            hashMap.put(string, new String[]{string2});
        }
        return hashMap;
    }

    private void brokerProfile() throws Exception {
        String string;
        String string2 = string = this.getParam("action");
        Map<String, String[]> map = this.createParameterMap();
        switch (string) {
            case "list": {
                CLILogger.log(L.t((String)"List of available profiles", (Object[])new Object[0]), true);
                break;
            }
            case "importstocks": {
                map.put("brokerId", new String[]{this.getParam("id")});
                map.put("filePath", new String[]{this.getParam("filepath")});
                string2 = "import";
                break;
            }
            case "exportstocks": {
                map.put("brokerId", new String[]{this.getParam("id")});
                map.put("filePath", new String[]{this.getParam("filepath")});
                string2 = "export";
                break;
            }
            case "import": {
                map.put("filePath", new String[]{this.getParam("filepath")});
                string2 = "loadXml";
                break;
            }
            case "export": {
                map.put("ids[]", new String[]{this.getParam("id")});
                map.put("filePath", new String[]{this.getParam("filepath")});
                string2 = "saveXml";
                break;
            }
            case "updateAll": {
                string2 = "updateData";
                List list = BrokerManager.getInstance().getAllBrokers();
                List list2 = list.stream().map(brokerDto -> brokerDto.getId().toString()).collect(Collectors.toList());
                map.put("brokerId", new String[]{String.join((CharSequence)",", String.join((CharSequence)",", list2))});
                break;
            }
            case "update": {
                string2 = "updateData";
                map.put("brokerId", new String[]{this.getParam("id")});
                break;
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string}));
            }
        }
        String string3 = (String)Program.get((String)"Brokers").call(string2, new Object[]{map});
        CLILogger.log(string.equals("list") ? this.parseListBrokers(string3) : this.parseCallResponse(string3));
    }

    private String parseListBrokers(String string) {
        try {
            JSONObject jSONObject = new JSONObject(string);
            if (jSONObject.has("success")) {
                JSONArray jSONArray = (JSONArray)jSONObject.get("rows");
                StringBuilder stringBuilder = new StringBuilder();
                stringBuilder.append("ID\tName\n");
                for (int i = 0; i < jSONArray.length(); ++i) {
                    JSONObject jSONObject2 = (JSONObject)jSONArray.get(i);
                    JSONArray jSONArray2 = (JSONArray)jSONObject2.get("data");
                    JSONObject jSONObject3 = (JSONObject)jSONObject2.get("userdata");
                    stringBuilder.append(jSONObject3.getInt("id") + "\t" + jSONArray2.get(0) + "\n");
                }
                return stringBuilder.toString();
            }
            if (jSONObject.has("error")) {
                return jSONObject.getString("error") + "\n" + "--------------------------------------------------";
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        return "";
    }

    public String runRemoteCommand(String[] stringArray) throws Exception {
        CLILogger.lastCommandOutput = "";
        this.runCommand(stringArray);
        return CLILogger.lastCommandOutput;
    }

    private void execute() throws Exception {
        String string = this.getParam("file");
        File file = new File(string);
        if (!file.exists()) {
            throw new Exception(L.t((String)"Script '%s' doesn't exist.", (Object[])new Object[]{file.getAbsolutePath()}));
        }
        CLILogger.log(String.format("Executing script '%s'", file.getName()));
        Process process = Runtime.getRuntime().exec(string);
        process.waitFor();
        CLILogger.log(L.t((String)"Script done.", (Object[])new Object[0]));
    }

    private void waitFor() throws Exception {
        String string;
        switch (string = this.getParam("action")) {
            case "user": {
                CLILogger.log(L.t((String)"Waiting for user action.", (Object[])new Object[0]));
                CLILogger.log(L.t((String)"Press \"ENTER\" to continue...", (Object[])new Object[0]));
                Scanner scanner = new Scanner(System.in);
                scanner.nextLine();
                CLILogger.log(L.t((String)"Continuing to next command.", (Object[])new Object[0]));
                break;
            }
            case "file": {
                String string2 = this.getParam("file");
                File file = new File(string2);
                if (file.exists()) {
                    L.t((String)"File '%s' exists.", (Object[])new Object[]{file.getAbsolutePath()});
                    CLILogger.log(L.t((String)"Continuing to next command.", (Object[])new Object[0]));
                    break;
                }
                CLILogger.log(L.t((String)"Waiting for file '%s'.", (Object[])new Object[]{file.getAbsolutePath()}));
                while (true) {
                    try {
                        Thread.sleep(1000L);
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                    try {
                        if (!file.exists()) continue;
                        CLILogger.log(L.t((String)"File '%s' exists.", (Object[])new Object[]{file.getName()}));
                        CLILogger.log(L.t((String)"Continuing to next command.", (Object[])new Object[0]));
                        return;
                    }
                    catch (Exception exception) {
                        Log.error("Exc.", (Throwable)exception);
                        continue;
                    }
                    break;
                }
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string}));
            }
        }
    }

    private void deleteFile() throws Exception {
        String string = this.getParam("file");
        File file = new File(string);
        if (!file.exists()) {
            throw new Exception(L.t((String)"File '%s' doesn't exist.", (Object[])new Object[]{file.getAbsolutePath()}));
        }
        if (!file.delete()) {
            throw new Exception(L.t((String)"File '%s' couldn't be deleted.", (Object[])new Object[]{file.getAbsolutePath()}));
        }
        CLILogger.log(L.t((String)"File '%s' successfully deleted.", (Object[])new Object[]{file.getAbsolutePath()}));
    }

    protected void symbol() throws Exception {
        String string;
        switch (string = this.getParam("action")) {
            case "add": {
                this.addSymbol();
                break;
            }
            case "edit": {
                this.editSymbol();
                break;
            }
            case "delete": {
                this.deleteSymbol();
                break;
            }
            case "clear": {
                this.clearSymbolData();
                break;
            }
            case "list": {
                this.listSymbols();
                break;
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string}));
            }
        }
    }

    protected void instrument() throws Exception {
        String string;
        switch (string = this.getParam("action")) {
            case "add": {
                this.addInstrument();
                break;
            }
            case "edit": {
                this.editInstrument();
                break;
            }
            case "delete": {
                this.deleteInstrument();
                break;
            }
            case "list": {
                this.listInstruments();
                break;
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string}));
            }
        }
    }

    protected void data() throws Exception {
        String string;
        switch (string = this.getParam("action")) {
            case "update": {
                this.update();
                break;
            }
            case "import": {
                this.dataImport();
                break;
            }
            case "export": {
                this.dataExport();
                break;
            }
            case "clone": {
                this.cloneData();
                break;
            }
            case "timezones": {
                this.listTimezones();
                break;
            }
            case "exportToMT4": {
                this.exportToMT4();
                break;
            }
            case "exportToMT5": {
                this.exportToMT5();
                break;
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string}));
            }
        }
    }

    protected void license() throws Exception {
        String string;
        switch (string = this.getParam("action")) {
            case "info": {
                this.printLicenseInfo();
                break;
            }
            case "update": {
                try {
                    String string2 = this.getParam("code");
                    CLILogger.log("Verifying license ...");
                    MainApp.rsq3UErJhC((String)string2);
                    CLILogger.log("License was successfully verified.");
                    this.printLicenseInfo();
                    V571hfnsHw v571hfnsHw = MainApp.v571hfnsHw();
                    if (v571hfnsHw.yIifbIrWD3() || v571hfnsHw.w49uJpREZO()) {
                        Tu5UdlpFO9.pzi7BBRxNg((String)v571hfnsHw.eHvc2JguAd());
                        break;
                    }
                    Tu5UdlpFO9.pzi7BBRxNg((String)"");
                }
                catch (Error | Exception throwable) {
                    CLILogger.log("Failed to check license - " + throwable.getMessage());
                    Log.error("Failed to check license. Exc. ", throwable);
                }
                break;
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string}));
            }
        }
    }

    private void printLicenseInfo() {
        String string = this.appName;
        if (string.endsWith("X")) {
            string = string.substring(0, string.length() - 1);
        }
        V571hfnsHw v571hfnsHw = MainApp.v571hfnsHw();
        string = string + MainApp.printAppVersion((String)v571hfnsHw.printEdition(), (boolean)false);
        if (v571hfnsHw.aJg1L21A0t()) {
            string = string + String.format(" for %s", v571hfnsHw.inygRmSMx7() != null ? v571hfnsHw.inygRmSMx7().getName() : "Unknown");
        }
        if (v571hfnsHw.aVwpAOwrF1()) {
            string = string + " - Licensed to: " + v571hfnsHw.oOkoIeUsMG() + " - " + v571hfnsHw.fSECzwVwpK();
        }
        string = string + " " + v571hfnsHw.printType(v571hfnsHw.eHvc2JguAd());
        string = string + ", license " + v571hfnsHw.eHvc2JguAd();
        CLILogger.log(string);
    }

    protected void exit() {
        CLILogger.log(L.t((String)"Bye", (Object[])new Object[0]));
        CLILogger.closeFile();
        MainApp.exitJVM((String)"cmd -exit", (int)this.exitStatus);
    }

    protected void run() throws Exception {
        String string = SQUtils.fileToString((String)this.getParam("file"));
        String[] stringArray = string.split("\n");
        for (int i = 0; i < stringArray.length; ++i) {
            String string2 = stringArray[i];
            if (string2.startsWith("#")) continue;
            CLILogger.log(L.t((String)"Running command: %s", (Object[])new Object[]{string2.trim()}), true);
            this.runCommand(ConsoleImpl.translateCommandline(string2));
        }
    }

    private void listTimezones() throws Exception {
        String string = (String)Program.get((String)"DataManagerData").call("listTimezones", null);
        CLILogger.log(this.parseCallResponse(string));
    }

    protected void help() throws Exception {
        String string = null;
        if (string == null) {
            String string2 = SQStructure.INTERNAL_DIR_PATH + "web/" + MainApp.getProduct() + "/help.txt";
            string = SQUtils.fileToString((String)string2);
            string = string.replaceAll("#ExportAvailableCsvFormats#", this.getExportCsvFormats());
            string = string.replaceAll("#CryptoExchanges#", this.getExchanges());
            string = string.replaceAll("#AvailableTimeframes#", this.getTimeframes());
        }
        CLILogger.log(string);
    }

    protected String getExportCsvFormats() {
        String string = "";
        try {
            String string2 = (String)Program.get((String)"DataManagerData").call("exportToCsvLoadSettings", null);
            JSONObject jSONObject = new JSONObject(string2);
            JSONArray jSONArray = jSONObject.getJSONArray("formats");
            for (int i = 0; i < jSONArray.length(); ++i) {
                string = string + jSONArray.getJSONObject(i).getString("name") + ",";
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        if (string.length() > 0) {
            string = string.substring(0, string.length() - 1);
        }
        return string;
    }

    protected String getTimeframes() {
        String string = "";
        try {
            ArrayList arrayList = TimeframeManager.getPredefinedTimeframes();
            for (int i = 0; i < arrayList.size(); ++i) {
                string = string + (String)arrayList.get(i) + ",";
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        if (string.length() > 0) {
            string = string.substring(0, string.length() - 1);
        }
        return string;
    }

    protected String getExchanges() {
        String string = "";
        try {
            String string2 = (String)Program.get((String)"DataSourceCrypto").call("getExchanges", null);
            JSONObject jSONObject = new JSONObject(string2);
            JSONArray jSONArray = jSONObject.getJSONArray("exchanges");
            for (int i = 0; i < jSONArray.length(); ++i) {
                string = string + jSONArray.getJSONObject(i).getString("value") + ",";
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        if (string.length() > 0) {
            string = string.substring(0, string.length() - 1);
        }
        return string;
    }

    private void cloneData() throws Exception {
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("symbols", new String[]{this.getParam("symbols")});
        hashMap.put("postfix", new String[]{this.getParam("postfix", "_{timeframe}_{cloneTime}")});
        hashMap.put("removeWeekends", new String[]{this.getParam("removeweekends", "false")});
        String string = this.getParam("timezone", null);
        String string2 = this.getParam("hours", null);
        if (string == null && string2 == null) {
            this.getParam("timezone");
        }
        hashMap.put("cloneTimezone", new String[]{string});
        hashMap.put("cloneTimezoneType", new String[]{string != null ? "1" : "0"});
        hashMap.put("cloneTimezoneShift", new String[]{string2});
        String string3 = (String)Program.get((String)"DataManagerData").call("cloneToTimezone", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string3));
    }

    private void dataExport() throws Exception {
        CLILogger.log("Exporting data.", true);
        String string = this.getParam("symbols");
        String string2 = this.getParam("timeframe");
        String string3 = this.getParam("outputdir", SQPaths.exportDirPath);
        String string4 = this.getParam("prefix", "");
        String string5 = this.getParam("format", "MetaTrader4 bar format");
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("symbols", new String[]{string});
        hashMap.put("timeframe", new String[]{string2});
        hashMap.put("directory", new String[]{string3});
        hashMap.put("filePrefix", new String[]{string4});
        hashMap.put("session", new String[]{"No Session"});
        hashMap.put("fileFormat", new String[]{string5});
        if (string5.equalsIgnoreCase("Custom")) {
            hashMap.put("header", new String[]{this.getParam("cHeader", "NA")});
            hashMap.put("format", new String[]{this.getParam("cFormat")});
            hashMap.put("includeHeader", new String[]{this.getParam("cIncludeHeader", "false")});
        }
        if (this.paramsExists("datefrom")) {
            hashMap.put("dateFrom", new String[]{this.getParam("datefrom")});
        }
        if (this.paramsExists("dateto")) {
            hashMap.put("dateTo", new String[]{this.getParam("dateto")});
        }
        String string6 = (String)Program.get((String)"DataManagerData").call("exportToCsv", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string6));
    }

    private void exportToMT4() throws Exception {
        CLILogger.log("Exporting data to MT4.", true);
        String string = this.getParam("symbol");
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("sqSymbol", new String[]{string});
        hashMap.put("timeframe", new String[]{this.getParam("timeframe")});
        hashMap.put("appPath", new String[]{this.getParam("appPath")});
        hashMap.put("dataPath", new String[]{this.getParam("dataPath")});
        hashMap.put("serverName", new String[]{this.getParam("serverName")});
        hashMap.put("mt4Symbol", new String[]{string});
        hashMap.put("mt4SymbolName", new String[]{string});
        hashMap.put("properties", new String[]{"default"});
        if (this.paramsExists("datefrom")) {
            hashMap.put("dateFrom", new String[]{this.getParam("datefrom")});
        }
        if (this.paramsExists("dateto")) {
            hashMap.put("dateTo", new String[]{this.getParam("dateto")});
        }
        String string2 = (String)Program.get((String)"DataManagerData").call("exportToMT4", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string2));
    }

    private void exportToMT5() throws Exception {
        CLILogger.log("Exporting data to MT5.", true);
        String string = this.getParam("timeframe", "Timeframe", new String[]{"TICK", "M1"});
        String string2 = "points";
        String string3 = "1";
        if (this.paramsExists("spreadType")) {
            string2 = this.getParam("spreadType", "Spread", new String[]{"points", "pips", "real"});
        } else {
            CLILogger.log("Using default spreadType: " + string2);
        }
        if (this.paramsExists("spreadValue")) {
            if (string2.equals("points") || string2.equals("pips")) {
                string3 = this.getParam("spreadValue");
            }
        } else if (!string2.equals("real")) {
            CLILogger.log("Using default spreadValue: " + string3);
        }
        String string4 = this.getParam("symbol");
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("symbol", new String[]{string4});
        hashMap.put("timeframe", new String[]{string});
        hashMap.put("spread", new String[]{string2});
        hashMap.put("spreadValue", new String[]{string3});
        hashMap.put("spreadPoints", new String[]{string3});
        hashMap.put("directory", new String[]{this.getParam("outputdir", SQPaths.exportDirPath)});
        hashMap.put("fileName", new String[]{this.getParam("filename", string4)});
        if (this.paramsExists("datefrom")) {
            hashMap.put("dateFrom", new String[]{this.getParam("datefrom")});
        }
        if (this.paramsExists("dateto")) {
            hashMap.put("dateTo", new String[]{this.getParam("dateto")});
        }
        String string5 = (String)Program.get((String)"DataManagerData").call("exportToMT5", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string5));
    }

    private String getParam(String string, String string2, String[] stringArray) throws Exception {
        String string3 = this.getParam(string);
        for (int i = 0; i < stringArray.length; ++i) {
            if (!stringArray[i].equals(string3)) continue;
            return string3;
        }
        throw new Exception(L.t((String)"'%s' must be one of ['%s'].", (Object[])new Object[]{string2, String.join((CharSequence)",", stringArray)}));
    }

    private void dataImport() throws Exception {
        Object object;
        DataInfo dataInfo;
        CLILogger.log(L.t((String)"Importing data.", (Object[])new Object[0]), true);
        String string = this.getParam("filepath");
        String string2 = this.getParam("symbol");
        String string3 = this.getParam("instrument", null);
        String string4 = this.getBarType();
        String string5 = this.getParam("timeframe", "auto");
        String string6 = this.getParam("timezone", "Etc/UCT");
        String string7 = this.getParam("format");
        String string8 = this.getParam("errorhandling", "stop");
        string8 = string8.equalsIgnoreCase("stop") ? "0" : (string8.equalsIgnoreCase("ignore") ? "1" : "0");
        CLILogger.log(L.t((String)"Checking symbol '%s'.", (Object[])new Object[]{string2}));
        if (!DataManager.checkDataExists((String)"History", (String)string2)) {
            CLILogger.log(L.t((String)"Symbol doesn't exist. Creating symbol...", (Object[])new Object[0]));
            dataInfo = new HashMap();
            dataInfo.put("connection", new String[]{"History"});
            dataInfo.put("symbol", new String[]{string2});
            dataInfo.put("instrument", new String[]{string3});
            dataInfo.put("barType", new String[]{string4});
            dataInfo.put("source", new String[]{"1"});
            object = (String)Program.get((String)"DataSourceFiles").call("add", new Object[]{dataInfo});
            CLILogger.log(this.parseCallResponse((String)object));
        } else {
            CLILogger.log(L.t((String)"Symbol exists.", (Object[])new Object[0]));
        }
        dataInfo = DataManager.getDataInfo((String)"History", (String)string2);
        CLILogger.log(L.t((String)"Recognizing file format...", (Object[])new Object[0]));
        object = AvailableDataFormats.getInstance().getAvailableFileFormats();
        CustomDataFormat customDataFormat = null;
        int n = -1;
        if (string7 != null && !string7.trim().isEmpty()) {
            for (int i = 0; i < ((ArrayList)object).size(); ++i) {
                try {
                    if (!((CustomDataFormat)((ArrayList)object).get(i)).getName().equals(string7)) continue;
                    n = i;
                    break;
                }
                catch (Exception exception) {
                    Log.debug("Import history data - cannot apply file format '" + string7 + "'. Reason: " + exception.getMessage(), (Throwable)exception);
                }
            }
        }
        customDataFormat = n != -1 ? DataImportEngine.getFileFormat((String)string, (ArrayList)object, (CustomDataFormat)((CustomDataFormat)((ArrayList)object).get(n))) : DataImportEngine.getFileFormat((String)string, (ArrayList)object, (CustomDataFormat)((CustomDataFormat)((ArrayList)object).get(0)));
        CLILogger.log(L.t((String)"Importing data...", (Object[])new Object[0]));
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("connectionName", new String[]{dataInfo.connection});
        hashMap.put("symbol", new String[]{dataInfo.symbol});
        hashMap.put("timezone", new String[]{string6});
        hashMap.put("fileFormat", new String[]{customDataFormat.getName()});
        hashMap.put("filePath", new String[]{string});
        hashMap.put("dateFormat", new String[]{customDataFormat.getDateFormat()});
        hashMap.put("separator", new String[]{customDataFormat.getSeparator()});
        hashMap.put("skipRows", new String[]{customDataFormat.getSkipRows() + ""});
        hashMap.put("skipColumns", new String[]{customDataFormat.getSkipColumns() + ""});
        hashMap.put("errorHandling", new String[]{string8});
        hashMap.put("timeframe", new String[]{string5});
        hashMap.put("columnTypes", new String[]{customDataFormat.columTypesToString()});
        String string9 = (String)Program.get((String)"DataSourceFiles").call("import", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string9));
    }

    private void update() throws Exception {
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        String string = "updateAll";
        if (this.paramsExists("symbols")) {
            string = "updateSelected";
            hashMap.put("symbols", new String[]{this.getParam("symbols")});
            CLILogger.log(L.t((String)"Updating selected data.", (Object[])new Object[0]), true);
        } else {
            CLILogger.log(L.t((String)"Updating all data.", (Object[])new Object[0]), true);
        }
        String string2 = (String)Program.get((String)"DataManagerData").call(string, new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string2));
    }

    private void listInstruments() throws Exception {
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        if (this.paramsExists("csv")) {
            hashMap.put("csv", new String[]{this.getParam("csv")});
        }
        String string = (String)Program.get((String)"DataManagerInstruments").call("list", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string));
    }

    private void deleteInstrument() throws Exception {
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("instruments", new String[]{this.getParam("instruments")});
        String string = (String)Program.get((String)"DataManagerInstruments").call("removeInstrument", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string));
    }

    private void editInstrument() throws Exception {
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("instrument", new String[]{this.getParam("instrument")});
        if (this.paramsExists("description")) {
            hashMap.put("description", new String[]{this.getParam("description")});
        }
        if (this.paramsExists("pointvalue")) {
            hashMap.put("pointValue", new String[]{this.getParam("pointvalue")});
        }
        if (this.paramsExists("ticksize")) {
            hashMap.put("tickSize", new String[]{this.getParam("ticksize")});
        }
        if (this.paramsExists("tickstep")) {
            hashMap.put("tickStep", new String[]{this.getParam("tickstep")});
        }
        if (this.paramsExists("defaultspread")) {
            hashMap.put("defaultSpread", new String[]{this.getParam("defaultspread")});
        }
        if (this.paramsExists("defaultslippage")) {
            hashMap.put("defaultSlippage", new String[]{this.getParam("defaultslippage")});
        }
        if (this.paramsExists("datatype")) {
            hashMap.put("dataType", new String[]{this.getDataType()});
        }
        if (this.paramsExists("minDistance")) {
            hashMap.put("minDistance", new String[]{this.getParam("minDistance")});
        }
        if (this.paramsExists("orderSizeMultiplier")) {
            hashMap.put("orderSizeMultiplier", new String[]{this.getParam("orderSizeMultiplier")});
        }
        if (this.paramsExists("orderSizeStep")) {
            hashMap.put("orderSizeStep", new String[]{this.getParam("orderSizeStep")});
        }
        String string = (String)Program.get((String)"DataManagerInstruments").call("editInstrument", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string));
    }

    private void addInstrument() throws Exception {
        BrokerDto brokerDto;
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("instrument", new String[]{this.getParam("instrument")});
        hashMap.put("description", new String[]{this.getParam("description", "")});
        hashMap.put("pointValue", new String[]{this.getParam("pointvalue", "100000")});
        hashMap.put("tickSize", new String[]{this.getParam("ticksize", "0.0001")});
        hashMap.put("tickStep", new String[]{this.getParam("tickstep", "0.00001")});
        hashMap.put("defaultSpread", new String[]{this.getParam("defaultspread", "2")});
        hashMap.put("defaultSlippage", new String[]{this.getParam("defaultslippage", "1")});
        hashMap.put("commissions", new String[]{""});
        hashMap.put("dataType", new String[]{this.getDataType()});
        hashMap.put("orderSizeMultiplier", new String[]{this.getParam("orderSizeMultiplier", "1")});
        hashMap.put("orderSizeStep", new String[]{this.getParam("orderSizeStep", "0")});
        hashMap.put("minDistance", new String[]{this.getParam("minDistance", "0")});
        if (this.paramsExists("swap")) {
            hashMap.put("swap", new String[]{this.getParam("swap")});
        }
        String string = this.getParam("broker", "");
        BrokerManager brokerManager = BrokerManager.getInstance();
        BrokerDto brokerDto2 = brokerDto = string.equals("") ? brokerManager.getDefaultBroker() : brokerManager.getBroker(string);
        if (brokerDto == null) {
            CLILogger.log("Broker was not found: " + string);
            return;
        }
        hashMap.put("broker", new String[]{brokerDto.getId().toString()});
        String string2 = (String)Program.get((String)"DataManagerInstruments").call("addInstrument", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string2));
    }

    private void listSymbols() throws Exception {
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        if (this.paramsExists("csv")) {
            hashMap.put("csv", new String[]{this.getParam("csv")});
        }
        String string = (String)Program.get((String)"DataManagerData").call("listData", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string));
    }

    private void clearSymbolData() throws Exception {
        String string = this.getParam("symbols");
        String[] stringArray = string.split(",");
        String string2 = "";
        for (int i = 0; i < stringArray.length; ++i) {
            string2 = i == stringArray.length - 1 ? string2 + "History" : string2 + "History,";
        }
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("symbols", new String[]{string});
        hashMap.put("connections", new String[]{string2});
        String string3 = (String)Program.get((String)"DataManagerData").call("clearData", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string3));
    }

    private void deleteSymbol() throws Exception {
        String string = this.getParam("symbols");
        String[] stringArray = string.split(",");
        String string2 = "";
        for (int i = 0; i < stringArray.length; ++i) {
            string2 = i == stringArray.length - 1 ? string2 + "History" : string2 + "History,";
        }
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("symbols", new String[]{string});
        hashMap.put("connections", new String[]{string2});
        String string3 = (String)Program.get((String)"DataManagerData").call("removeData", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string3));
    }

    private void editSymbol() throws Exception {
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("connection", new String[]{"History"});
        String string = this.getParam("symbol");
        hashMap.put("symbol", new String[]{string});
        hashMap.put("symbolNew", new String[]{this.getParam("name", string)});
        if (this.paramsExists("instrument")) {
            hashMap.put("instrument", new String[]{this.getParam("instrument")});
        }
        if (this.paramsExists("barType")) {
            hashMap.put("barType", new String[]{this.getBarType()});
        }
        String string2 = (String)Program.get((String)"DataManagerData").call("editData", new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string2));
    }

    protected void addSymbol() throws Exception {
        String string = this.getParam("datasource", "dukascopy");
        if (string.equalsIgnoreCase("dukascopy")) {
            BrokerDto brokerDto;
            HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
            hashMap.put("symbols[]", this.getParam("symbols").split(","));
            hashMap.put("postfix", new String[]{this.getParam("postfix", "")});
            hashMap.put("dataType", new String[]{this.getParam("datatype", "M1")});
            String string2 = this.getParam("broker", "");
            BrokerManager brokerManager = BrokerManager.getInstance();
            BrokerDto brokerDto2 = brokerDto = string2.equals("") ? brokerManager.getDefaultBroker() : brokerManager.getBroker(string2);
            if (brokerDto == null) {
                CLILogger.log("Broker was not found: " + string2);
                return;
            }
            hashMap.put("broker", new String[]{brokerDto.getId().toString()});
            CLILogger.log(L.t((String)"Creating symbols...", (Object[])new Object[0]));
            String string3 = (String)Program.get((String)"DataSourceDukascopy").call("addData", new Object[]{hashMap});
            CLILogger.log(this.parseCallResponse(string3));
        } else if (string.equalsIgnoreCase("file")) {
            String[] stringArray = this.getParam("symbols").split(",");
            for (int i = 0; i < stringArray.length; ++i) {
                HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                hashMap.put("connection", new String[]{"History"});
                hashMap.put("symbol", new String[]{stringArray[i]});
                hashMap.put("instrument", new String[]{this.getParam("instrument")});
                hashMap.put("barType", new String[]{this.getBarType()});
                CLILogger.log(L.t((String)"Creating symbol '%s'...", (Object[])new Object[]{stringArray[i]}));
                String string4 = (String)Program.get((String)"DataSourceFiles").call("add", new Object[]{hashMap});
                CLILogger.log(this.parseCallResponse(string4));
            }
        } else if (string.equalsIgnoreCase("darwinex")) {
            BrokerDto brokerDto;
            HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
            hashMap.put("symbols[]", this.getParam("symbols").split(","));
            hashMap.put("broker", new String[]{"-1"});
            hashMap.put("postfix", new String[]{this.getParam("postfix", "")});
            String string5 = this.getParam("broker", "");
            BrokerManager brokerManager = BrokerManager.getInstance();
            BrokerDto brokerDto3 = brokerDto = string5.equals("") ? brokerManager.getDefaultBroker() : brokerManager.getBroker(string5);
            if (brokerDto == null) {
                CLILogger.log("Broker was not found: " + string5);
                return;
            }
            hashMap.put("broker", new String[]{brokerDto.getId().toString()});
            CLILogger.log(L.t((String)"Creating symbols...", (Object[])new Object[0]));
            String string6 = (String)Program.get((String)"DataSourceDarwinex").call("downloadAddData", new Object[]{hashMap});
            CLILogger.log(this.parseCallResponse(string6));
        } else if (string.equalsIgnoreCase("crypto")) {
            HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
            hashMap.put("symbols", new String[]{this.getParam("symbols")});
            hashMap.put("postfix", new String[]{this.getParam("postfix", "")});
            hashMap.put("timeframe", new String[]{this.getParam("timeframe", "M1")});
            hashMap.put("exchange", new String[]{this.getParam("exchange", "Binance")});
            CLILogger.log("Creating symbols...");
            String string7 = (String)Program.get((String)"DataSourceCrypto").call("add", new Object[]{hashMap});
            CLILogger.log(this.parseCallResponse(string7));
        } else if (string.equalsIgnoreCase("yahoo")) {
            HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
            hashMap.put("symbols", new String[]{this.getParam("symbols")});
            hashMap.put("postfix", new String[]{this.getParam("postfix", "")});
            CLILogger.log(L.t((String)"Creating symbols...", (Object[])new Object[0]));
            String string8 = (String)Program.get((String)"DataSourceYahoo").call("add", new Object[]{hashMap});
            CLILogger.log(this.parseCallResponse(string8));
        } else if (string.equalsIgnoreCase("SQEquityData")) {
            HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
            hashMap.put("symbols", new String[]{this.getParam("symbols")});
            hashMap.put("barType", new String[]{this.getBarType()});
            CLILogger.log(L.t((String)"Creating symbols...", (Object[])new Object[0]));
            String string9 = (String)Program.get((String)"DataSourceSQEquityData").call("add", new Object[]{hashMap});
            CLILogger.log(this.parseCallResponse(string9));
        } else if (string.equalsIgnoreCase("mt5api")) {
            HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
            hashMap.put("symbols", new String[]{this.getParam("symbols")});
            hashMap.put("postfix", new String[]{this.getParam("postfix", "")});
            hashMap.put("broker", new String[]{this.getParam("broker", "-1")});
            String string10 = this.getParam("path", "");
            hashMap.put("path", new String[]{string10});
            hashMap.put("dateFrom", new String[]{this.getParam("datefrom")});
            hashMap.put("dateTo", new String[]{this.getParam("dateto")});
            CLILogger.log(L.t((String)"Creating symbols...", (Object[])new Object[0]));
            String string11 = (String)Program.get((String)"DataSourceMt5Api").call("importData", new Object[]{hashMap});
            CLILogger.log(this.parseCallResponse(string11));
        } else {
            throw new Exception(L.t((String)"Unrecognized data source '%s'.", (Object[])new Object[]{string}));
        }
    }

    protected String getDataType() throws Exception {
        String string = this.getParam("datatype", "Forex");
        if (string.equalsIgnoreCase("Stock")) {
            return "1";
        }
        if (string.equalsIgnoreCase("Futures")) {
            return "2";
        }
        if (string.equalsIgnoreCase("Forex")) {
            return "3";
        }
        if (string.equalsIgnoreCase("CFDs")) {
            return "4";
        }
        if (string.equalsIgnoreCase("ETF")) {
            return "5";
        }
        if (string.equalsIgnoreCase("Index")) {
            return "6";
        }
        if (string.equalsIgnoreCase("Crypto")) {
            return "7";
        }
        return "3";
    }

    protected String getBarType() throws Exception {
        String string = this.getParam("bartype", "startofbar");
        if (string.equalsIgnoreCase("startofbar")) {
            return "1";
        }
        if (string.equalsIgnoreCase("endofbar")) {
            return "2";
        }
        return "1";
    }

    protected String appArgsToString(String[] stringArray) {
        String string = "";
        for (int i = 0; i < stringArray.length; ++i) {
            string = string + stringArray[i] + " ";
        }
        return string;
    }

    protected String getParam(String string) throws Exception {
        if (!this.paramsExists(string)) {
            throw new Exception(L.t((String)"Missing parameter '%s'.", (Object[])new Object[]{string}));
        }
        return this.parsedParams.get(string);
    }

    protected String getParam(String string, String string2) throws Exception {
        if (!this.paramsExists(string)) {
            return string2;
        }
        return this.parsedParams.get(string);
    }

    protected boolean paramsExists(String string) {
        return this.parsedParams.containsKey(string);
    }

    public HashMap<String, String> parseParams(String[] stringArray) throws Exception {
        try {
            HashMap<String, String> hashMap = new HashMap<String, String>();
            CLILogger.redirectOutputToFile(null);
            for (int i = 0; i < stringArray.length; ++i) {
                String string = stringArray[i];
                if (string.contains("=")) {
                    String[] stringArray2 = string.split("=");
                    if (stringArray2.length != 2) continue;
                    hashMap.put(stringArray2[0], stringArray2[1]);
                    continue;
                }
                if (string.contains(">") && i + 1 < stringArray.length) {
                    CLILogger.redirectOutputToFile(stringArray[i + 1]);
                    continue;
                }
                hashMap.put(string, null);
            }
            return hashMap;
        }
        catch (Exception exception) {
            CLILogger.log(L.t((String)"Incorrect command line parameters.", (Object[])new Object[0]) + " " + exception.getMessage());
            throw new Exception("Incorrect command line parameters. " + exception.getMessage());
        }
    }

    private void redirectOutputToFile(String string) {
    }

    protected String parseCallResponse(String string) {
        String string2 = string;
        try {
            JSONObject jSONObject = new JSONObject(string);
            if (jSONObject.has("success")) {
                string2 = jSONObject.getString("success");
            } else if (jSONObject.has("error")) {
                string2 = jSONObject.getString("error");
            }
        }
        catch (Exception exception) {
            // empty catch block
        }
        return string2.equals("{}") ? "" : string2 + "\n" + "--------------------------------------------------";
    }

    protected void waitAndFinish() {
        while (true) {
            try {
                Thread.sleep(500L);
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (SQGrid.getGridClient().countAllJobs(null) != 0L) continue;
            SQWebSocketManager.getInstance().sendData();
            CLILogger.closeFile();
            MainApp.exitApp();
        }
    }

    public static String[] translateCommandline(String string) throws Exception {
        if (string == null || string.isEmpty()) {
            return new String[0];
        }
        int n = 0;
        StringTokenizer stringTokenizer = new StringTokenizer(string, "\"' ", true);
        ArrayList<String> arrayList = new ArrayList<String>();
        StringBuilder stringBuilder = new StringBuilder();
        boolean bl = false;
        block4: while (stringTokenizer.hasMoreTokens()) {
            String string2 = stringTokenizer.nextToken();
            switch (n) {
                case 1: {
                    if ("'".equals(string2)) {
                        bl = true;
                        n = 0;
                        continue block4;
                    }
                    stringBuilder.append(string2);
                    continue block4;
                }
                case 2: {
                    if ("\"".equals(string2)) {
                        bl = true;
                        n = 0;
                        continue block4;
                    }
                    stringBuilder.append(string2);
                    continue block4;
                }
            }
            if ("'".equals(string2)) {
                n = 1;
            } else if ("\"".equals(string2)) {
                n = 2;
            } else if (" ".equals(string2)) {
                if (bl || stringBuilder.length() > 0) {
                    arrayList.add(stringBuilder.toString().trim());
                    stringBuilder.setLength(0);
                }
            } else {
                stringBuilder.append(string2);
            }
            bl = false;
        }
        if (bl || stringBuilder.length() > 0) {
            arrayList.add(stringBuilder.toString().trim());
        }
        if (n == 1 || n == 2) {
            throw new Exception("Unbalanced quotes in " + string);
        }
        return arrayList.toArray(new String[arrayList.size()]);
    }
}

