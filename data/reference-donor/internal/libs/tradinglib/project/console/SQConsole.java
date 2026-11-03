/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.customData.CustomDataTypes
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.app.impl.MainAppStandardImpl
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  io.modelcontextprotocol.json.McpJsonDefaults
 *  io.modelcontextprotocol.server.McpServer
 *  io.modelcontextprotocol.server.transport.StdioServerTransportProvider
 *  io.modelcontextprotocol.spec.McpSchema$ServerCapabilities
 *  io.modelcontextprotocol.spec.McpServerTransportProvider
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.project.console;

import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.customData.CustomDataTypes;
import com.strategyquant.lib.L;
import com.strategyquant.lib.app.impl.MainAppStandardImpl;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.project.console.CLILogger;
import com.strategyquant.tradinglib.project.console.ConsoleImpl;
import com.strategyquant.tradinglib.project.mcp.MCPTools;
import com.strategyquant.tradinglib.strategy.SourceCode;
import io.modelcontextprotocol.json.McpJsonDefaults;
import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.spec.McpSchema;
import io.modelcontextprotocol.spec.McpServerTransportProvider;
import java.io.File;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.PipedInputStream;
import java.io.PipedOutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.json.JSONArray;
import org.json.JSONObject;

public class SQConsole
extends ConsoleImpl {
    private List<String> initSyncList = new ArrayList<String>();

    public SQConsole(MainAppStandardImpl mainAppStandardImpl) {
        super("StrategyQuant X", "sqcli");
    }

    public SQConsole(String string, String string2) {
        super(string, string2);
    }

    @Override
    public void runCommand(String[] stringArray) throws Exception {
        this.parsedParams = this.parseParams(stringArray);
        switch (stringArray[0]) {
            case "-project": {
                this.project();
                break;
            }
            case "-databank": {
                this.databank();
                break;
            }
            case "-tools": {
                this.tools();
                break;
            }
            case "-stockgroup": {
                this.stockgroups();
                break;
            }
            case "-stockgroups": {
                this.stockgroups();
                break;
            }
            case "-sourcecode": {
                this.sourcecode();
                break;
            }
            case "-extindicators": {
                this.extIndicators();
                break;
            }
            case "-mcp": {
                this.runMcpStdioServer();
                break;
            }
            case "quit": 
            case "exit": 
            case "-exit": {
                this.exit();
                break;
            }
            default: {
                super.runCommand(stringArray);
            }
        }
    }

    @Override
    public void exit() {
        try {
            CLILogger.log(L.t((String)"Synchronizing databanks to files", (Object[])new Object[0]), true);
            String string = (String)Program.get((String)"Project").call("synchronizeAllDatabanks", null);
            CLILogger.log(this.parseCallResponse(string));
        }
        catch (Exception exception) {
            CLILogger.log(L.t((String)"Cannot synchronize databanks. Reason: %s", (Object[])new Object[]{exception.getMessage()}));
        }
        super.exit();
    }

    private void stockgroups() throws Exception {
        String string;
        String string2 = string = this.getParam("action");
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        switch (string) {
            case "list": {
                CLILogger.log(L.t((String)"List of available groups", (Object[])new Object[0]), true);
                break;
            }
            case "importstocks": {
                hashMap.put("basketId", new String[]{this.getParam("id")});
                hashMap.put("filePath", new String[]{this.getParam("filepath")});
                string2 = "import";
                break;
            }
            case "exportstocks": {
                hashMap.put("basketId", new String[]{this.getParam("id")});
                hashMap.put("filePath", new String[]{this.getParam("filepath")});
                string2 = "export";
                break;
            }
            case "import": {
                hashMap.put("filePath", new String[]{this.getParam("filepath")});
                string2 = "loadXml";
                break;
            }
            case "export": {
                hashMap.put("ids[]", new String[]{this.getParam("id")});
                hashMap.put("filePath", new String[]{this.getParam("filepath")});
                string2 = "saveXml";
                break;
            }
            case "updateAll": {
                string2 = "updateData";
                BasketOfStocksManager.getInstance().sync(null);
                List list = BasketOfStocksManager.getInstance().getGroups();
                List list2 = list.stream().filter(basketDto -> !basketDto.getName().equalsIgnoreCase("[[S&P 100 limited]]")).map(basketDto -> basketDto.getId().toString()).collect(Collectors.toList());
                hashMap.put("basketId", new String[]{String.join((CharSequence)",", list2)});
                break;
            }
            case "update": {
                string2 = "updateData";
                hashMap.put("basketId", new String[]{this.getParam("id")});
                break;
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string}));
            }
        }
        String string3 = (String)Program.get((String)"GroupOfStocks").call(string2, new Object[]{hashMap});
        CLILogger.log(string.equals("list") ? this.parseListGroups(string3) : this.parseCallResponse(string3));
    }

    private String parseListGroups(String string) {
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

    private void tools() throws Exception {
        String string = this.getParam("action");
        String string2 = this.getParam("file");
        String string3 = this.getParam("output", null);
        String string4 = this.getParam("usecomma", "false");
        String string5 = this.getParam("data", "all");
        switch (string) {
            case "orderstocsv": {
                CLILogger.log(L.t((String)"Extracting strategy orders to csv", (Object[])new Object[0]), true);
                this.saveOrders(string2, string3, "csv", string4, string5);
                break;
            }
            case "orderstoxlsx": {
                CLILogger.log(L.t((String)"Extracting strategy orders to xlsx", (Object[])new Object[0]), true);
                this.saveOrders(string2, string3, "xlsx", string4, string5);
                break;
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string}));
            }
        }
    }

    private void saveOrders(String string, String string2, String string3, String string4, String string5) throws Exception {
        block15: {
            IProgram iProgram;
            IProgram iProgram2;
            File file;
            File file2;
            HashMap<String, String[]> hashMap;
            block14: {
                File[] fileArray;
                hashMap = new HashMap<String, String[]>();
                hashMap.put("useComma", new String[]{string4});
                hashMap.put("data", new String[]{string5});
                file2 = new File(string);
                if (!file2.exists()) {
                    throw new Exception(L.t((String)"File '%s' doesn't exist.", (Object[])new Object[]{file2.getAbsolutePath()}));
                }
                file = string2 != null ? new File(string2) : null;
                iProgram2 = Program.get((String)"Loader");
                iProgram = Program.get((String)"SaverStrategyTrades");
                if (!file2.isDirectory()) break block14;
                if (file != null) {
                    if (!file.exists()) {
                        file.mkdirs();
                    }
                    if (!file.isDirectory()) {
                        throw new Exception(L.t((String)"Output file '%s' is not a directory.", (Object[])new Object[]{file.getAbsolutePath()}));
                    }
                }
                if ((fileArray = file2.listFiles()) == null) break block15;
                for (File file3 : fileArray) {
                    ResultsGroup resultsGroup = (ResultsGroup)iProgram2.call("loadFile", new Object[]{file3.getAbsolutePath()});
                    String string6 = resultsGroup.getName() + "." + string3;
                    string6 = file != null ? file.getAbsolutePath() + "/" + string6 : (file2.getParentFile() != null ? file2.getParentFile().getAbsolutePath() + "/" + string6 : file2.getAbsolutePath() + "/" + string6);
                    try {
                        iProgram.call("save", new Object[]{resultsGroup, string6, hashMap});
                        CLILogger.log(L.t((String)"%s - orders exported to '%s'", (Object[])new Object[]{resultsGroup.getName(), new File(string6).getAbsolutePath()}));
                    }
                    catch (Exception exception) {
                        CLILogger.log(L.t((String)"Cannot export orders of strategy  '%s'", (Object[])new Object[]{file2.getAbsolutePath()}));
                    }
                }
                break block15;
            }
            if (file != null && !file.exists() && file.getParentFile() != null) {
                file.getParentFile().mkdirs();
            }
            ResultsGroup resultsGroup = (ResultsGroup)iProgram2.call("loadFile", new Object[]{file2.getAbsolutePath()});
            String string7 = resultsGroup.getName() + "." + string3;
            if (file != null) {
                string7 = file.getAbsolutePath();
            } else if (file2.getParentFile() != null) {
                string7 = file2.getParentFile().getAbsolutePath() + "/" + string7;
            }
            if (!string7.endsWith("." + string3)) {
                string7 = string7 + "." + string3;
            }
            try {
                iProgram.call("save", new Object[]{resultsGroup, string7, hashMap});
                CLILogger.log(L.t((String)"%s - orders exported to '%s'", (Object[])new Object[]{resultsGroup.getName(), new File(string7).getAbsolutePath()}));
            }
            catch (Exception exception) {
                CLILogger.log(L.t((String)"Cannot export orders of strategy  '%s'", (Object[])new Object[]{file2.getAbsolutePath()}));
            }
        }
    }

    protected void project() throws Exception {
        String string;
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        String string2 = this.getParam("action");
        String string3 = null;
        if (!string2.equals("list")) {
            string3 = this.getParam("name");
            hashMap.put("projectName", new String[]{string3});
        }
        String string4 = "Project";
        switch (string2) {
            case "list": {
                CLILogger.log(L.t((String)"List of available projects", (Object[])new Object[0]), true);
                string = "list";
                break;
            }
            case "start": {
                CLILogger.log(L.t((String)"Starting project '%s'", (Object[])new Object[]{this.getParam("name")}), true);
                string = "start";
                this.syncDatabanks(hashMap);
                break;
            }
            case "startOnlyTask": {
                try {
                    Integer.valueOf(this.getParam("task"));
                }
                catch (Exception exception) {
                    throw new Exception(L.t((String)"Task must be a number.", (Object[])new Object[0]));
                }
                hashMap.put("action", new String[]{"runTask"});
                hashMap.put("taskName", new String[]{this.getParam("task")});
                CLILogger.log(L.t((String)"Starting project '%s' task %s only", (Object[])new Object[]{this.getParam("name"), this.getParam("task")}), true);
                string = "start";
                this.syncDatabanks(hashMap);
                break;
            }
            case "startFromTask": {
                try {
                    Integer.valueOf(this.getParam("task"));
                }
                catch (Exception exception) {
                    throw new Exception(L.t((String)"Task must be a number.", (Object[])new Object[0]));
                }
                hashMap.put("action", new String[]{"runFrom"});
                hashMap.put("taskName", new String[]{this.getParam("task")});
                CLILogger.log(L.t((String)"Starting project '%s' from task %s", (Object[])new Object[]{this.getParam("name"), this.getParam("task")}), true);
                string = "start";
                this.syncDatabanks(hashMap);
                break;
            }
            case "stop": {
                CLILogger.log(L.t((String)"Stopping project %s", (Object[])new Object[]{this.getParam("name")}), true);
                string = "stop";
                break;
            }
            case "pause": {
                CLILogger.log(L.t((String)"Pausing project %s", (Object[])new Object[]{this.getParam("name")}), true);
                string = "pause";
                break;
            }
            case "resume": {
                CLILogger.log(L.t((String)"Resuming project %s", (Object[])new Object[]{this.getParam("name")}), true);
                string = "resume";
                break;
            }
            case "remove": {
                CLILogger.log(L.t((String)"Removing project %s", (Object[])new Object[]{this.getParam("name")}), true);
                string4 = "TaskManager";
                string = "removeProject";
                break;
            }
            case "status": {
                CLILogger.log(L.t((String)"Status of project %s", (Object[])new Object[]{this.getParam("name")}), true);
                string = "status";
                this.syncDatabanks(hashMap);
                break;
            }
            case "loadconfig": {
                hashMap.put("file", new String[]{this.getParam("file")});
                CLILogger.log(L.t((String)"Loading config of project %s", (Object[])new Object[]{string3}), true);
                string4 = "Project";
                string = "loadConfig";
                if (string3.equalsIgnoreCase("Builder")) {
                    hashMap.put("projectName", new String[]{"Builder"});
                    break;
                }
                if (string3.equalsIgnoreCase("Retester")) {
                    hashMap.put("projectName", new String[]{"Retester"});
                    break;
                }
                if (string3.equalsIgnoreCase("Optimizer")) {
                    hashMap.put("projectName", new String[]{"Optimizer"});
                    break;
                }
                string4 = "TaskManager";
                string = "openProject";
                hashMap.put("loadAsIs", new String[]{"true"});
                break;
            }
            case "saveconfig": {
                hashMap.put("file", new String[]{this.getParam("file")});
                CLILogger.log(L.t((String)"Saving config of project %s", (Object[])new Object[]{string3}), true);
                string4 = "Project";
                string = "saveConfig";
                if (string3.equalsIgnoreCase("Builder")) {
                    hashMap.put("projectName", new String[]{"Builder"});
                    break;
                }
                if (string3.equalsIgnoreCase("Retester")) {
                    hashMap.put("projectName", new String[]{"Retester"});
                    break;
                }
                if (string3.equalsIgnoreCase("Optimizer")) {
                    hashMap.put("projectName", new String[]{"Optimizer"});
                    break;
                }
                string4 = "TaskManager";
                string = "saveProject";
                break;
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string2}));
            }
        }
        String string5 = (String)Program.get((String)string4).call(string, new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string5));
    }

    protected void databank() throws Exception {
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("projectName", new String[]{this.getParam("project")});
        String string = this.getParam("action");
        if (!string.equals("list")) {
            hashMap.put("databankName", new String[]{this.getParam("name")});
        }
        String string2 = "Project";
        String string3 = null;
        String string4 = null;
        switch (string) {
            case "list": {
                CLILogger.log(L.t((String)"List of available databanks", (Object[])new Object[0]), true);
                string3 = "databankList";
                this.syncDatabanks(hashMap);
                break;
            }
            case "count": {
                CLILogger.log(L.t((String)"Number of strategies", (Object[])new Object[0]), true);
                string3 = "databankCount";
                this.syncDatabanks(hashMap);
                break;
            }
            case "load": {
                CLILogger.log(L.t((String)"Loading reports", (Object[])new Object[0]), true);
                hashMap.put("folder", new String[]{this.getParam("folder")});
                hashMap.put("strategies", new String[]{this.getParam("strategies", "all")});
                string3 = "loadFilesToDatabank";
                break;
            }
            case "save": {
                CLILogger.log(L.t((String)"Saving reports", (Object[])new Object[0]), true);
                hashMap.put("folder", new String[]{this.getParam("folder")});
                hashMap.put("strategies", new String[]{this.getParam("strategies", "all")});
                string3 = "saveReports";
                break;
            }
            case "delete": {
                CLILogger.log(L.t((String)"Deleting selected reports", (Object[])new Object[0]), true);
                hashMap.put("strategies", new String[]{this.getParam("strategies")});
                string3 = "removeReports";
                break;
            }
            case "clear": {
                CLILogger.log(L.t((String)"Clearing databank", (Object[])new Object[0]), true);
                string3 = "removeAllReports";
                this.syncDatabanks(hashMap);
                break;
            }
            case "copy": {
                CLILogger.log(L.t((String)"Copying reports", (Object[])new Object[0]), true);
                string4 = (String)Program.get((String)"Project").call("copyStrategies", new Object[]{hashMap});
                CLILogger.log(this.parseCallResponse(string4));
                hashMap.put("projectName", new String[]{this.getParam("destproject")});
                hashMap.put("databankName", new String[]{this.getParam("destdatabank")});
                string3 = "pasteStrategies";
                break;
            }
            case "move": {
                CLILogger.log(L.t((String)"Moving reports", (Object[])new Object[0]), true);
                string4 = (String)Program.get((String)"Project").call("cutStrategies", new Object[]{hashMap});
                CLILogger.log(this.parseCallResponse(string4));
                hashMap.put("projectName", new String[]{this.getParam("destproject")});
                hashMap.put("databankName", new String[]{this.getParam("destdatabank")});
                string3 = "pasteStrategies";
                break;
            }
            case "synctofiles": {
                CLILogger.log(L.t((String)"Syncing datatabank to files", (Object[])new Object[0]), true);
                string3 = "synchronizeDatabank";
                break;
            }
            case "syncfromfiles": {
                CLILogger.log(L.t((String)"Syncing databank from files", (Object[])new Object[0]), true);
                string3 = "syncfromfiles";
                break;
            }
            case "create": {
                CLILogger.log(L.t((String)"Creating datatabank", (Object[])new Object[0]), true);
                string3 = "createDatabank";
                String string5 = this.getParam("position", null);
                if (string5 == null) break;
                hashMap.put("position", new String[]{string5});
                break;
            }
            case "remove": {
                CLILogger.log(L.t((String)"Removing datatabank", (Object[])new Object[0]), true);
                string3 = "removeDatabank";
                break;
            }
            case "export": {
                CLILogger.log(L.t((String)"Exporting databank contents", (Object[])new Object[0]), true);
                hashMap.put("path", new String[]{this.getParam("file")});
                hashMap.put("view", new String[]{this.getParam("view", "Default - Main data")});
                string2 = "ResultsDatabankActions";
                string3 = "exportDatabankToCSV";
                break;
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string}));
            }
        }
        string4 = (String)Program.get((String)string2).call(string3, new Object[]{hashMap});
        CLILogger.log(this.parseCallResponse(string4));
    }

    @Override
    protected void addSymbol() throws Exception {
        String string = this.getParam("datasource", "dukascopy");
        if (string.equalsIgnoreCase("sqequity")) {
            if (!this.getParam("confirm").equalsIgnoreCase("yes")) {
                throw new Exception(L.t((String)"Please read and agree to StrategyQuant Data Usage Conditions", (Object[])new Object[0]));
            }
            HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
            hashMap.put("symbols", new String[]{this.getParam("symbols")});
            hashMap.put("postfix", new String[]{this.getParam("postfix", "")});
            hashMap.put("barType", new String[]{this.getBarType()});
            String string2 = (String)Program.get((String)"DataSourceSQEquityData").call("add", new Object[]{hashMap});
            CLILogger.log(this.parseCallResponse(string2));
        } else if (string.equalsIgnoreCase("sqfutures")) {
            if (!this.getParam("confirm").equalsIgnoreCase("yes")) {
                throw new Exception(L.t((String)"Please read and agree to StrategyQuant Data Usage Conditions", (Object[])new Object[0]));
            }
            HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
            hashMap.put("symbols", new String[]{this.getParam("symbols")});
            hashMap.put("postfix", new String[]{this.getParam("postfix", "")});
            hashMap.put("barType", new String[]{this.getBarType()});
            String string3 = (String)Program.get((String)"DataSourceSQFuturesData").call("add", new Object[]{hashMap});
            CLILogger.log(this.parseCallResponse(string3));
        } else {
            super.addSymbol();
        }
    }

    private void syncDatabanks(Map<String, String[]> map) throws Exception {
        if (!map.containsKey("projectName")) {
            return;
        }
        String string = map.get("projectName")[0];
        if (this.initSyncList.contains(string)) {
            return;
        }
        this.initSyncList.add(string);
        CLILogger.log(L.t((String)"Syncing databank(s) from files", (Object[])new Object[0]));
        String string2 = (String)Program.get((String)"Project").call("synchronizeDatabanks", new Object[]{map});
        CLILogger.log(this.parseCallResponse(string2));
    }

    private void sourcecode() throws Exception {
        String string;
        switch (string = this.getParam("action")) {
            case "generate": {
                String string2 = this.getParam("engine");
                String string3 = this.getParam("s");
                String string4 = this.getParam("o");
                SourceCode sourceCode = new SourceCode();
                sourceCode.generate(string2, string3, string4);
                break;
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string}));
            }
        }
    }

    private void runMcpStdioServer() {
        try {
            int n;
            CLILogger.log(L.t((String)"Starting MCP stdio server...", (Object[])new Object[0]), true);
            PipedOutputStream pipedOutputStream = new PipedOutputStream();
            PipedInputStream pipedInputStream = new PipedInputStream(pipedOutputStream, 65536);
            StdioServerTransportProvider stdioServerTransportProvider = new StdioServerTransportProvider(McpJsonDefaults.getMapper(), (InputStream)pipedInputStream, (OutputStream)System.out);
            McpServer.sync((McpServerTransportProvider)stdioServerTransportProvider).serverInfo("StrategyQuant X", "1.0.0").capabilities(McpSchema.ServerCapabilities.builder().tools(Boolean.valueOf(false)).build()).tools(MCPTools.createSpecs()).build();
            byte[] byArray = new byte[4096];
            while ((n = System.in.read(byArray)) != -1) {
                pipedOutputStream.write(byArray, 0, n);
                pipedOutputStream.flush();
            }
        }
        catch (Exception exception) {
            CLILogger.log(L.t((String)"MCP server error: %s", (Object[])new Object[]{exception.getMessage()}));
        }
    }

    private void extIndicators() throws Exception {
        String string;
        switch (string = this.getParam("action")) {
            case "list": {
                CLILogger.log(L.t((String)"List of external indicators", (Object[])new Object[0]), true);
                String string2 = (String)Program.get((String)"DataManagerCustomData").call("list", null);
                CLILogger.log(this.parseCallResponse(string2));
                break;
            }
            case "add": {
                CLILogger.log(L.t((String)"Add external indicator", (Object[])new Object[0]), true);
                String string3 = this.getParam("values");
                String[] stringArray = string3.split(",");
                if (stringArray.length == 0) {
                    throw new Exception(L.t((String)"At least one value must be set.", (Object[])new Object[0]));
                }
                JSONArray jSONArray = new JSONArray();
                for (String string4 : stringArray) {
                    JSONObject jSONObject = new JSONObject();
                    jSONObject.put("name", (Object)string4);
                    jSONObject.put("mt4", (Object)"");
                    jSONObject.put("mt5", (Object)"");
                    jSONObject.put("el", (Object)"");
                    jSONArray.put((Object)jSONObject);
                }
                byte by = Byte.parseByte(this.getParam("type"));
                if (!CustomDataTypes.availableDataTypes().contains(by)) {
                    throw new Exception(L.t((String)"Unrecognized data type %s.", (Object[])new Object[]{by}));
                }
                HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                hashMap.put("name", new String[]{this.getParam("name")});
                hashMap.put("values", new String[]{jSONArray.toString()});
                hashMap.put("type", new String[]{by + ""});
                String string5 = (String)Program.get((String)"DataManagerCustomData").call("add", new Object[]{hashMap});
                CLILogger.log(this.parseCallResponse(string5));
                break;
            }
            case "import": {
                CLILogger.log(L.t((String)"Import data from file", (Object[])new Object[0]), true);
                String string6 = this.getParam("name");
                String string7 = this.getParam("file");
                HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                hashMap.put("name", new String[]{string6});
                hashMap.put("file", new String[]{string7});
                String string8 = (String)Program.get((String)"DataManagerCustomData").call("importcli", new Object[]{hashMap});
                CLILogger.log(this.parseCallResponse(string8));
                break;
            }
            case "load": {
                CLILogger.log(L.t((String)"Load indicator from file.", (Object[])new Object[0]), true);
                String string9 = this.getParam("filepath");
                HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                hashMap.put("filePath", new String[]{string9});
                String string10 = (String)Program.get((String)"DataManagerCustomData").call("load", new Object[]{hashMap});
                CLILogger.log(this.parseCallResponse(string10));
                break;
            }
            case "save": {
                CLILogger.log(L.t((String)"Save indicator to file.", (Object[])new Object[0]), true);
                String string11 = this.getParam("filepath");
                String string12 = this.getParam("name");
                HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                hashMap.put("filePath", new String[]{string11});
                hashMap.put("data", new String[]{string12});
                String string13 = (String)Program.get((String)"DataManagerCustomData").call("save", new Object[]{hashMap});
                CLILogger.log(this.parseCallResponse(string13));
                break;
            }
            default: {
                throw new Exception(L.t((String)"Unrecognized action %s.", (Object[])new Object[]{string}));
            }
        }
    }
}

