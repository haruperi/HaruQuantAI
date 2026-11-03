/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.DownloadSemaphore
 *  com.strategyquant.datalib.data.StockGroupUpdateErrorManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.pluginlib.program.ProgramDoesntExistException
 *  com.strategyquant.tradinglib.project.websocket.DataManagerConfirm
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.tradinglib.project.websocket.WebSocketNotification
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.Basket;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.DownloadSemaphore;
import com.strategyquant.datalib.data.StockGroupUpdateErrorManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.pluginlib.program.ProgramDoesntExistException;
import com.strategyquant.tradinglib.project.websocket.DataManagerConfirm;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.project.websocket.WebSocketNotification;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BasketServlet
extends HttpJSONServlet {
    private static final long serialVersionUID = 1L;
    private static final Logger Log = LoggerFactory.getLogger(BasketServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "list": {
                return this.onListBasket(args);
            }
            case "save": {
                return this.onSaveBasket(args);
            }
            case "delete": {
                return this.onDeleteBasket(args);
            }
            case "import": {
                return this.onImportStocks(args);
            }
            case "listStocks": {
                return this.onListStocks(args);
            }
            case "editStocks": {
                return this.onEditStocks(args);
            }
            case "updateData": {
                return this.onUpdateData(args);
            }
            case "export": {
                return this.onExportStocks(args);
            }
            case "loadXml": {
                return this.onLoad(args);
            }
            case "saveXml": {
                return this.onSave(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onLoad(Map<String, String[]> args) {
        try {
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            Element elGroups = XMLUtil.fileToXmlElement((File)file);
            if (!elGroups.getName().equals("Groups")) {
                throw new Exception(L.t((String)"No Groups found to import.", (Object[])new Object[0]));
            }
            LinkedList<String> names = new LinkedList<String>();
            for (Element elGroup : elGroups.getChildren("Group")) {
                BasketDto groupLoaded = new BasketDto();
                String name = elGroup.getAttributeValue("name");
                if (name.startsWith("[[")) {
                    name = name.substring(1, name.length() - 1);
                }
                groupLoaded.setName(name);
                groupLoaded.setDesc(elGroup.getChildText("Desc"));
                ArrayList<StockDto> stocks = new ArrayList<StockDto>();
                Element stocksEl = elGroup.getChild("Stocks");
                List stockElements = stocksEl.getChildren("Stock");
                for (Element stockEl : stockElements) {
                    StockDto dto = new StockDto();
                    dto.setTicker(stockEl.getAttributeValue("name"));
                    try {
                        dto.setDateFrom(Long.valueOf(stockEl.getAttributeValue("from")));
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                    try {
                        dto.setDateTo(Long.valueOf(stockEl.getAttributeValue("to")));
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                    stocks.add(dto);
                }
                groupLoaded.setCount(stocks.size());
                BasketDto existingBasket = BasketOfStocksManager.getInstance().getBasket(name);
                if (existingBasket == null || MainApp.runInConsole()) {
                    if (existingBasket != null) {
                        groupLoaded.setId(existingBasket.getId());
                    }
                    BasketOfStocksManager.getInstance().saveGroup(groupLoaded);
                    BasketOfStocksManager.getInstance().saveStocks(groupLoaded.getId().intValue(), stocks);
                    names.add(groupLoaded.getName());
                    continue;
                }
                DataManagerConfirm.get().awaitConfirmation(L.t((String)"Overwrite confirm", (Object[])new Object[0]), L.t((String)"Group '%s' already exists, do you want to overwrite it with the imported one?", (Object[])new Object[]{name}));
                String action = DataManagerConfirm.get().getConfirmedAction();
                if (action.equals("skip")) continue;
                if (action.equals("cancel")) break;
                if (!action.equals("overwrite") && !action.equals("overwrite_all")) continue;
                groupLoaded.setId(existingBasket.getId());
                BasketOfStocksManager.getInstance().saveGroup(groupLoaded);
                BasketOfStocksManager.getInstance().saveStocks(groupLoaded.getId().intValue(), stocks);
                names.add(groupLoaded.getName());
            }
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBaskets(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            response.put("success", (Object)L.t((String)"Stockgroups (%d) loaded.", (Object[])new Object[]{names.size()}));
            return response.toString();
        }
        catch (Exception e) {
            return BasketServlet.apiErrorJSON((String)L.t((String)"Cannot load stockgroups.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onSave(Map<String, String[]> args) {
        try {
            String[] ids;
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            Element elSessions = new Element("Groups");
            for (String id : ids = this.tryGetParam(args, "ids[]")) {
                BasketDto group = BasketOfStocksManager.getInstance().getBasket(Integer.valueOf(id));
                List stocks = BasketOfStocksManager.getInstance().getStocks(group.getId().intValue());
                elSessions.addContent((Content)this.toXML(group, stocks));
            }
            XMLUtil.xmlToFile((Element)elSessions, (File)file);
            response.put("success", (Object)L.t((String)"Groups saved.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return BasketServlet.apiErrorJSON((String)L.t((String)"Cannot save groups.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private Element toXML(BasketDto basket, List<StockDto> stocks) {
        Element elBroker = new Element("Group");
        elBroker.setAttribute("name", basket.getName());
        Element descEl = new Element("Desc");
        descEl.setText(basket.getDesc());
        elBroker.addContent((Content)descEl);
        Element elStocks = new Element("Stocks");
        elBroker.addContent((Content)elStocks);
        for (StockDto stock : stocks) {
            Element elStockElement = new Element("Stock");
            elStockElement.setAttribute("name", stock.getTicker());
            elStockElement.setAttribute("from", stock.getDateFrom() == null ? "" : stock.getDateFrom().toString());
            elStockElement.setAttribute("to", stock.getDateTo() == null ? "" : stock.getDateTo().toString());
            elStocks.addContent((Content)elStockElement);
        }
        return elBroker;
    }

    private String onEditGroup(Map<String, String[]> args) {
        return null;
    }

    private String onExportStocks(Map<String, String[]> args) throws Exception {
        String filePath = this.tryGetParam(args, "filePath")[0];
        Integer basketId = Integer.valueOf(this.tryGetParam(args, "basketId")[0]);
        try {
            BasketDto dto = BasketOfStocksManager.getInstance().getBasket(basketId);
            if (dto == null) {
                return BasketServlet.apiErrorJSON((String)L.t((String)"Group doesn't exist.", (Object[])new Object[0]), null);
            }
            List stocks = BasketOfStocksManager.getInstance().getStocks(basketId.intValue());
            this.writeStocksToCsv(filePath, stocks);
            return this.getSuccessResult("Stocks were exported");
        }
        catch (Exception e) {
            return BasketServlet.apiErrorJSON((String)L.t((String)"Cannot import stocks.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private void writeStocksToCsv(String filePath, List<StockDto> stocks) throws IOException {
        StringBuilder sb = new StringBuilder();
        for (StockDto stockDto : stocks) {
            sb.append(stockDto.getTicker() + ";" + SQTime.formatDate((long)stockDto.getDateFrom()));
            if (stockDto.getDateTo() != null) {
                sb.append(";" + SQTime.formatDate((long)stockDto.getDateTo()));
            }
            sb.append("\n");
        }
        Files.writeString(new File(filePath).toPath(), (CharSequence)sb.toString(), StandardOpenOption.CREATE);
    }

    private String onImportStocks(Map<String, String[]> args) throws Exception {
        String filePath = this.tryGetParam(args, "filePath")[0];
        Integer basketId = Integer.valueOf(this.tryGetParam(args, "basketId")[0]);
        String prefix = this.getParam(args, "prefix", "");
        try {
            BasketDto dto = BasketOfStocksManager.getInstance().getBasket(basketId);
            if (dto == null) {
                return BasketServlet.apiErrorJSON((String)L.t((String)"Group doesn't exist.", (Object[])new Object[0]), null);
            }
            if (dto.isSystem()) {
                return BasketServlet.apiErrorJSON((String)L.t((String)"This group can't be modified.", (Object[])new Object[0]), null);
            }
            String lines = Files.readString(new File(filePath).toPath());
            BasketOfStocksManager.getInstance().importFromCsv(lines, basketId, null, prefix);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBaskets(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            return this.getSuccessResult(L.t((String)"Stocks were imported", (Object[])new Object[0]));
        }
        catch (Exception e) {
            return BasketServlet.apiErrorJSON((String)L.t((String)"Cannot import stocks from file '%s'.", (Object[])new Object[]{filePath}), (Throwable)e);
        }
    }

    private String onDeleteBasket(Map<String, String[]> args) throws Exception {
        String[] baskets;
        for (String strBasketId : baskets = this.tryGetParam(args, "baskets")[0].split("\\,")) {
            int id = Integer.valueOf(strBasketId);
            BasketDto group = BasketOfStocksManager.getInstance().deleteGroup(id);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)group.getName(), (String)"remove"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBaskets(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        return this.getSuccessResult(L.t((String)"Group deleted", (Object[])new Object[0]));
    }

    private String getSuccessResult(String message) {
        JSONObject response = new JSONObject();
        response.put("success", (Object)message);
        return response.toString();
    }

    private String onSaveBasket(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(args, "name")[0];
            String desc = this.tryGetParam(args, "desc")[0];
            String idStr = this.tryGetParam(args, "id")[0];
            Integer id = null;
            try {
                id = Integer.valueOf(idStr);
            }
            catch (Exception exception) {
                // empty catch block
            }
            BasketDto dto = new BasketDto();
            dto.setId(id);
            dto.setName(name);
            dto.setDesc(desc);
            BasketOfStocksManager.getInstance().saveGroup(dto);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBaskets(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            if (id == null) {
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)"", (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            }
            response.put("success", (Object)L.t((String)"Group added.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return BasketServlet.apiErrorJSON((String)L.t((String)"Cannot save group.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onListBasket(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        JSONArray rows = new JSONArray();
        HashMap<String, DataInfo> symbolsMap = new HashMap<String, DataInfo>();
        DataManager.get();
        ArrayList symbols = DataManager.list();
        HashSet<String> existingNames = new HashSet<String>();
        for (DataInfo dataInfo : symbols) {
            existingNames.add(dataInfo.symbol);
            symbolsMap.put(dataInfo.symbol, dataInfo);
        }
        List baskets = BasketOfStocksManager.getInstance().getGroups();
        for (int i = 0; i < baskets.size(); ++i) {
            BasketDto info = (BasketDto)baskets.get(i);
            JSONObject userdata = new JSONObject();
            userdata.put("id", (Object)info.getId());
            userdata.put("system", info.isSystem());
            JSONObject row = new JSONObject();
            row.put("userdata", (Object)userdata);
            JSONArray data = new JSONArray();
            data.put((Object)info.getName());
            data.put((Object)(info.getCount() + " / " + info.getTotal()));
            data.put((Object)info.getDesc());
            data.put(BasketOfStocksManager.getNumberOfSymbolsInGroup(existingNames, (BasketDto)info));
            int downloaded = BasketOfStocksManager.getDownloaded(symbolsMap, (Integer)info.getId());
            data.put((Object)(downloaded + " / " + info.getTotal()));
            if (info.getTotal() > 0 && BasketOfStocksManager.isReadyForUse((int)downloaded, (int)info.getTotal())) {
                data.put((Object)"Yes");
            } else {
                String tooltip = "Stock group is not ready for use, not all its symbols are downloaded";
                List missingSymbols = BasketOfStocksManager.getMissingSymbols(symbolsMap, (Integer)info.getId());
                if (!missingSymbols.isEmpty()) {
                    int maxShown = 20;
                    List shown = missingSymbols.size() > maxShown ? missingSymbols.subList(0, maxShown) : missingSymbols;
                    tooltip = tooltip + ". Missing symbols: " + String.join((CharSequence)", ", shown);
                    if (missingSymbols.size() > maxShown) {
                        tooltip = tooltip + " and " + (missingSymbols.size() - maxShown) + " more";
                    }
                }
                data.put((Object)("No, <a onmousedown=\"sqGridSendEvent(event, 'updateSpecificGroup')\">Update data</a> <i title=\"" + tooltip + "\" class=\"fa fa-question-circle-o\" aria-hidden=\"true\"></i>"));
            }
            DataInfo aliasInfo = DataManager.getDataInfo((String)"History", (String)info.getName());
            if (aliasInfo == null) {
                data.put((Object)"-");
                data.put((Object)"-");
            } else {
                data.put((Object)(aliasInfo.dateFrom == 0L ? "" : SQTime.toDateString((long)aliasInfo.dateFrom)));
                data.put((Object)(aliasInfo.dateTo == 0L ? "" : SQTime.toDateString((long)aliasInfo.dateTo)));
            }
            row.put("data", (Object)data);
            rows.put((Object)row);
        }
        response.put("rows", (Object)rows);
        response.put("success", (Object)L.t((String)"Groups listed", (Object[])new Object[0]));
        return response.toString();
    }

    private String onEditStocks(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        Integer basketId = Integer.valueOf(this.tryGetParam(args, "id")[0]);
        String stocks = this.tryGetParam(args, "stocks")[0];
        List stocksDtos = BasketOfStocksManager.getInstance().updateStocksFromStr(stocks, basketId, "");
        SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBaskets(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        response.put("success", (Object)L.t((String)"Stocks saved", (Object[])new Object[0]));
        return response.toString();
    }

    private String onListStocks(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        Integer basketId = Integer.valueOf(this.tryGetParam(args, "basketId")[0]);
        BasketDto dto = BasketOfStocksManager.getInstance().getBasket(basketId);
        if (dto == null) {
            return BasketServlet.apiErrorJSON((String)L.t((String)"Group doesn't exist.", (Object[])new Object[0]), null);
        }
        List stocks = BasketOfStocksManager.getInstance().getStocks(basketId.intValue());
        StringBuilder stocksStr = new StringBuilder();
        for (int i = 0; i < stocks.size(); ++i) {
            StockDto info = (StockDto)stocks.get(i);
            stocksStr.append(info.getTicker());
            if (info.getDateFrom() != null && info.getDateFrom() != -1L) {
                stocksStr.append(";");
                stocksStr.append(SQTime.toDateString((long)info.getDateFrom()));
            }
            if (info.getDateTo() != null && info.getDateTo() != -1L) {
                stocksStr.append(";");
                stocksStr.append(SQTime.toDateString((long)info.getDateTo()));
            }
            stocksStr.append("\n");
        }
        response.put("stocks", (Object)stocksStr);
        response.put("success", (Object)L.t((String)"Stocks listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUpdateData(Map<String, String[]> parameterMap) throws Exception {
        if (!DownloadSemaphore.getInstance().startDownloadData(5)) {
            return BasketServlet.apiErrorJSON((String)L.t((String)"Please wait couple of seconds and try again.", (Object[])new Object[0]), null);
        }
        try {
            StockGroupUpdateErrorManager.getInstance().start();
            String[] groupIdsStr = this.tryGetParamValue(parameterMap, "basketId").split(",");
            final LinkedList<StockDto> stocks = new LinkedList<StockDto>();
            HashSet<String> stockSet = new HashSet<String>();
            for (String idStr : groupIdsStr) {
                Integer basketId = Integer.valueOf(idStr);
                BasketDto dto = BasketOfStocksManager.getInstance().getBasket(basketId);
                if (dto == null) {
                    DownloadSemaphore.getInstance().downloadFinished();
                    return BasketServlet.apiErrorJSON((String)L.t((String)"Group doesn't exist.", (Object[])new Object[0]), null);
                }
                if (dto.getName().equalsIgnoreCase("[[S&P 100 limited]]")) {
                    DownloadSemaphore.getInstance().downloadFinished();
                    return BasketServlet.apiErrorJSON((String)L.t((String)"Group S&P 100 limited cannot be updated, it is only in clean installation.", (Object[])new Object[0]), null);
                }
                List iStocks = BasketOfStocksManager.getInstance().getStocks(basketId.intValue());
                for (StockDto stockDto : iStocks) {
                    if (stockSet.contains(stockDto.getTicker())) continue;
                    stocks.add(stockDto);
                    stockSet.add(stockDto.getTicker());
                }
            }
            if (stocks.isEmpty()) {
                DownloadSemaphore.getInstance().downloadFinished();
                return this.getSuccessResult(L.t((String)"Nothing to update. Group is without any stocks.", (Object[])new Object[0]));
            }
            if (MainApp.runInConsoleWithoutActiveWebserver()) {
                this._onUpdateData(stocks);
            } else {
                new Thread(new Runnable(){
                    final /* synthetic */ BasketServlet this$0;
                    {
                        this.this$0 = this$0;
                    }

                    @Override
                    public void run() {
                        try {
                            this.this$0._onUpdateData(stocks);
                        }
                        catch (Exception e) {
                            Log.error("Error while updating data", (Throwable)e);
                        }
                    }
                }).start();
            }
        }
        catch (Exception e) {
            DownloadSemaphore.getInstance().downloadFinished();
            throw e;
        }
        return this.getSuccessResult(L.t((String)"Starting updating data. Please wait...", (Object[])new Object[0]));
    }

    private void _onUpdateData(List<StockDto> stocks) throws ProgramDoesntExistException, Exception {
        try {
            HashMap<String, String[]> args = new HashMap<String, String[]>();
            ArrayList<String> allSymbols = new ArrayList<String>();
            ArrayList<String> missingSymbols = new ArrayList<String>();
            WebSocketNotification.sendSuccess((String)L.t((String)"Loading stock informations. ", (Object[])new Object[0]), (String[])new String[]{"QDM"});
            Log.info("Checking stocks in groups");
            for (int i = 0; i < stocks.size(); ++i) {
                boolean symbolExists;
                StockDto stock = stocks.get(i);
                String symbol = stock.getTicker();
                DataInfo di = DataManager.getDataInfo((String)"History", (String)symbol);
                boolean bl = symbolExists = di != null && (di.source == 6 || di.source == 5);
                if (!symbolExists) {
                    missingSymbols.add(symbol);
                }
                allSymbols.add(symbol);
            }
            WebSocketNotification.sendSuccess((String)L.t((String)"Loading stock informations finished. Creating symbols for group...", (Object[])new Object[0]), (String[])new String[]{"QDM", "SQUANT"});
            args.put("symbols", new String[]{String.join((CharSequence)",", missingSymbols)});
            args.put("postfix", new String[]{""});
            args.put("barType", new String[]{"1"});
            if (missingSymbols.size() > 0) {
                Log.info("Adding {} stocks are necessary.", (Object)String.join((CharSequence)",", missingSymbols));
            } else {
                Log.info("No adding stocks are necessary.");
            }
            Collections.shuffle(allSymbols);
            args.put("updateSymbols", new String[]{String.join((CharSequence)",", allSymbols)});
            Log.info("Running update process");
            Program.get((String)"DataSourceSQEquityData").call("add", new Object[]{args});
        }
        catch (Exception e) {
            DownloadSemaphore.getInstance().downloadFinished();
            throw e;
        }
    }
}

