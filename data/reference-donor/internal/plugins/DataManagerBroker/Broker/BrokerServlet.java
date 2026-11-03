/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.broker.BrokerStockDto
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.DownloadSemaphore
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionException
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.pluginlib.program.ProgramDoesntExistException
 *  com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender
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
package com.strategyquant.plugin.DataManager.impl.Broker;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.broker.BrokerStockDto;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.DownloadSemaphore;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionException;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.plugin.DataManager.impl.Broker.BrokerXmlImporter;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.pluginlib.program.ProgramDoesntExistException;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
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
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BrokerServlet
extends HttpJSONServlet {
    private static final long serialVersionUID = 1L;
    private static final Logger Log = LoggerFactory.getLogger(BrokerServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "importGetOverview": {
                return this.onImportGetOverview(args);
            }
            case "importSessionInstrument": {
                return this.onImportSessionInstrument(args);
            }
            case "list": {
                return this.onListBroker(args);
            }
            case "save": {
                return this.onSaveBroker(args);
            }
            case "delete": {
                return this.onDeleteBroker(args);
            }
            case "listStocks": {
                return this.onListStocks(args);
            }
            case "editStocks": {
                return this.onEditStocks(args);
            }
            case "import": {
                return this.onImportStocks(args);
            }
            case "export": {
                return this.onExportStocks(args);
            }
            case "updateData": {
                return this.onUpdateData(args);
            }
            case "loadXml": {
                return this.onLoad(args);
            }
            case "importProfile": {
                return this.onImportProfile(args);
            }
            case "saveXml": {
                return this.onSave(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onImportGetOverview(Map<String, String[]> args) {
        try {
            String filePath = this.tryGetParam(args, "filePath")[0];
            String type = this.tryGetParam(args, "type")[0];
            BrokerXmlImporter importer = new BrokerXmlImporter();
            JSONObject response = new JSONObject();
            if (type.equals("session")) {
                List<Session> sessions = importer.importSessions(filePath, null);
                JSONArray data = new JSONArray();
                for (Session session : sessions) {
                    JSONObject obj = new JSONObject();
                    obj.put("name", (Object)session.getSessionName());
                    data.put((Object)obj);
                }
                response.put("data", (Object)data);
            } else {
                List<InstrumentInfo> instruments = importer.importInstruments(filePath, null);
                JSONArray data = new JSONArray();
                for (InstrumentInfo instrument : instruments) {
                    JSONObject obj = new JSONObject();
                    obj.put("name", (Object)instrument.instrument);
                    obj.put("description", (Object)instrument.description);
                    data.put((Object)obj);
                }
                response.put("data", (Object)data);
            }
            response.put("success", (Object)L.t((String)"Import overview", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return BrokerServlet.apiErrorJSON((String)L.t((String)"Cannot load XML content.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onImportSessionInstrument(Map<String, String[]> args) {
        try {
            String filePath = this.tryGetParam(args, "filePath")[0];
            String type = this.tryGetParam(args, "type")[0];
            String postfix = args.containsKey("postfix") ? this.tryGetParam(args, "postfix")[0] : "";
            int brokerId = Integer.valueOf(this.tryGetParam(args, "broker")[0]);
            List<String> selected = Arrays.asList(this.tryGetParam(args, "selected[]"));
            if (selected.isEmpty()) {
                throw new IllegalArgumentException("No records were selected.");
            }
            BrokerDto broker = BrokerManager.getInstance().getBroker(Integer.valueOf(brokerId));
            if (broker == null) {
                throw new IllegalArgumentException("Broker was not found");
            }
            BrokerXmlImporter importer = new BrokerXmlImporter();
            JSONObject response = new JSONObject();
            if (type.equals("session")) {
                List<Session> sessions = importer.importSessions(filePath, selected);
                if (sessions.size() > 10) {
                    this.importSessionAsync(sessions, brokerId, postfix, broker);
                } else {
                    for (Session session : sessions) {
                        this.performImportSession(session, brokerId, postfix, broker);
                    }
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSessions(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                }
            } else {
                List<InstrumentInfo> instruments = importer.importInstruments(filePath, selected);
                if (instruments.size() > 10) {
                    this.importInstrumentsAsync(instruments, brokerId, postfix, broker);
                } else {
                    for (InstrumentInfo instrumentInfo : instruments) {
                        this.performImportInstrument(instrumentInfo, brokerId, postfix, broker);
                    }
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                }
            }
            response.put("success", (Object)L.t((String)"File imported", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return BrokerServlet.apiErrorJSON((String)L.t((String)"Cannot import XML file.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private void importSessionAsync(final List<Session> sessions, final int brokerId, final String postfix, final BrokerDto broker) {
        final int total = sessions.size();
        new Thread(this){
            final /* synthetic */ BrokerServlet this$0;
            {
                this.this$0 = this$0;
            }

            /*
             * WARNING - Removed try catching itself - possible behaviour change.
             */
            @Override
            public void run() {
                JSONObject progress = new JSONObject();
                LinkedList<String> errors = new LinkedList<String>();
                int count = 0;
                for (Session session : sessions) {
                    try {
                        this.this$0.performImportSession(session, brokerId, postfix, broker);
                        Integer percent = SQUtils.round((double)(100.0 * (double)count / (double)total));
                        progress.put("percent", (Object)percent);
                        progress.put("info", (Object)L.t((String)"Imported session '%s'", (Object[])new Object[]{session.getSessionName()}));
                        if (percent == 100) {
                            progress.put("message", (Object)"Sessions imported");
                        }
                        DataManagerAddProgressSender.getInstance().sendData(progress);
                    }
                    catch (Exception e) {
                        errors.add(session.getSessionName());
                    }
                    finally {
                        ++count;
                    }
                }
                try {
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSessions(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                }
                catch (Exception e) {
                    Log.error("", (Throwable)e);
                }
                progress.put("percent", 100);
                progress.put("info", (Object)L.t((String)"Completed", (Object[])new Object[0]));
                progress.put("message", (Object)"Sessions imported");
                if (errors.size() > 0) {
                    progress.put("error", (Object)L.t((String)"Could'd be imported: %s", (Object[])new Object[]{String.join((CharSequence)",", errors)}));
                }
                DataManagerAddProgressSender.getInstance().sendData(progress);
            }
        }.start();
    }

    private void performImportSession(Session session, int brokerId, String postfix, BrokerDto broker) throws SessionException {
        session.setBroker(brokerId);
        String newName = session.getSessionName() + postfix;
        Session newSession = new Session(newName, session.cloneElements());
        newSession.setBroker(brokerId);
        newSession.setTimeZone(session.getTimeZone());
        if (SessionManager.checkSessionExists((String)newName)) {
            SessionManager.removeSession((String)newName);
        }
        SessionManager.addSession((Session)newSession);
    }

    private void performImportInstrument(InstrumentInfo instrumentInfo, int brokerId, String postfix, BrokerDto broker) throws Exception {
        instrumentInfo.broker = brokerId;
        instrumentInfo.instrument = instrumentInfo.instrument + postfix;
        if (InstrumentManager.checkInstrumentExists((String)instrumentInfo.instrument)) {
            InstrumentManager.removeInstrument((String)instrumentInfo.instrument);
        }
        InstrumentManager.addInstrument((InstrumentInfo)instrumentInfo);
    }

    private void importInstrumentsAsync(final List<InstrumentInfo> instruments, final int brokerId, final String postfix, final BrokerDto broker) {
        final int total = instruments.size();
        new Thread(this){
            final /* synthetic */ BrokerServlet this$0;
            {
                this.this$0 = this$0;
            }

            /*
             * WARNING - Removed try catching itself - possible behaviour change.
             */
            @Override
            public void run() {
                JSONObject progress = new JSONObject();
                LinkedList<String> errors = new LinkedList<String>();
                int count = 0;
                for (InstrumentInfo instrument : instruments) {
                    try {
                        this.this$0.performImportInstrument(instrument, brokerId, postfix, broker);
                        Integer percent = SQUtils.round((double)(100.0 * (double)count / (double)total));
                        progress.put("percent", (Object)percent);
                        progress.put("info", (Object)L.t((String)"Imported instrument '%s'", (Object[])new Object[]{instrument.instrument}));
                        if (percent == 100) {
                            progress.put("message", (Object)"Instruments imported");
                        }
                        DataManagerAddProgressSender.getInstance().sendData(progress);
                    }
                    catch (Exception e) {
                        errors.add(instrument.instrument);
                    }
                    finally {
                        ++count;
                    }
                }
                try {
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                }
                catch (Exception e) {
                    Log.error("", (Throwable)e);
                }
                progress.put("percent", 100);
                progress.put("info", (Object)L.t((String)"Completed", (Object[])new Object[0]));
                progress.put("message", (Object)"Instruments imported");
                if (errors.size() > 0) {
                    progress.put("error", (Object)L.t((String)"Could'd be imported: %s", (Object[])new Object[]{String.join((CharSequence)",", errors)}));
                }
                DataManagerAddProgressSender.getInstance().sendData(progress);
            }
        }.start();
    }

    private String onLoad(Map<String, String[]> args) {
        try {
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            Element elBrokers = XMLUtil.fileToXmlElement((File)file);
            if (!elBrokers.getName().equals("Brokers")) {
                throw new Exception(L.t((String)"No Brokers found to import.", (Object[])new Object[0]));
            }
            LinkedList<String> names = new LinkedList<String>();
            for (Element elBroker : elBrokers.getChildren("Broker")) {
                BrokerDto existingBroker;
                BrokerDto brokerLoaded = new BrokerDto();
                String name = elBroker.getAttributeValue("name");
                if (name.startsWith("[[")) {
                    name = name.substring(1, name.length() - 1);
                }
                brokerLoaded.setName(name);
                brokerLoaded.setDesc(elBroker.getChildText("Desc"));
                String stockPickinerUseStr = elBroker.getAttributeValue("stockPickerUse");
                brokerLoaded.setStockPickerUse(stockPickinerUseStr == null ? false : Boolean.valueOf(stockPickinerUseStr));
                String mtUseStr = elBroker.getAttributeValue("mtUse");
                brokerLoaded.setMtUse(mtUseStr == null ? false : Boolean.valueOf(mtUseStr));
                if (brokerLoaded.isMtUse()) {
                    brokerLoaded.setMtTimezone(elBroker.getAttributeValue("mtTimezone"));
                    brokerLoaded.setPostfix(elBroker.getAttributeValue("mtPostfix"));
                }
                ArrayList<BrokerStockDto> stocks = new ArrayList<BrokerStockDto>();
                Element stocksEl = elBroker.getChild("Stocks");
                if (stocksEl != null) {
                    List stockElements = stocksEl.getChildren("Stock");
                    for (Element stockEl : stockElements) {
                        BrokerStockDto dto = new BrokerStockDto();
                        dto.setTicker(stockEl.getAttributeValue("name"));
                        stocks.add(dto);
                    }
                    if (stocks.size() > 0) {
                        brokerLoaded.setStockPickerUse(true);
                    }
                }
                if ((existingBroker = BrokerManager.getInstance().getBroker(name)) == null || MainApp.runInConsole()) {
                    if (existingBroker != null) {
                        brokerLoaded.setId(existingBroker.getId());
                    }
                    BrokerManager.getInstance().saveBroker(brokerLoaded);
                    BrokerManager.getInstance().saveStocks(brokerLoaded.getId().intValue(), stocks);
                    names.add(brokerLoaded.getName());
                    continue;
                }
                DataManagerConfirm.get().awaitConfirmation(L.t((String)"Overwrite confirm", (Object[])new Object[0]), L.t((String)"Broker '%s' already exists, do you want to overwrite it with the imported one?", (Object[])new Object[]{name}));
                String action = DataManagerConfirm.get().getConfirmedAction();
                if (action.equals("skip")) continue;
                if (action.equals("cancel")) break;
                if (!action.equals("overwrite") && !action.equals("overwrite_all")) continue;
                brokerLoaded.setId(existingBroker.getId());
                BrokerManager.getInstance().saveBroker(brokerLoaded);
                BrokerManager.getInstance().saveStocks(brokerLoaded.getId().intValue(), stocks);
                names.add(brokerLoaded.getName());
            }
            BrokerManager.getInstance().refresh();
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBrokers(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            response.put("success", (Object)L.t((String)"Brokers (%d) loaded.", (Object[])new Object[]{names.size()}));
            return response.toString();
        }
        catch (Exception e) {
            return BrokerServlet.apiErrorJSON((String)L.t((String)"Cannot load brokers.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onImportProfile(Map<String, String[]> args) {
        try {
            String ref;
            String filePath = this.tryGetParam(args, "filePath")[0];
            boolean overwrite = !args.containsKey("overwrite") || "1".equals(args.get("overwrite")[0]);
            String postfix = args.containsKey("postfix") ? args.get("postfix")[0] : "";
            Element root = XMLUtil.fileToXmlElement((File)new File(filePath));
            JSONObject response = new JSONObject();
            if (root.getName().equals("Brokers")) {
                LinkedList<String> imported = new LinkedList<String>();
                LinkedList<String> skipped = new LinkedList<String>();
                for (Element elBroker : root.getChildren("Broker")) {
                    BrokerDto existing;
                    String storedName;
                    BrokerDto loaded = new BrokerDto();
                    String name = elBroker.getAttributeValue("name");
                    if (name.startsWith("[[")) {
                        name = name.substring(1, name.length() - 1);
                    }
                    loaded.setName(name);
                    loaded.setDesc(elBroker.getChildText("Desc"));
                    String stockPickerUseStr = elBroker.getAttributeValue("stockPickerUse");
                    loaded.setStockPickerUse(stockPickerUseStr != null && Boolean.valueOf(stockPickerUseStr) != false);
                    String mtUseStr = elBroker.getAttributeValue("mtUse");
                    loaded.setMtUse(mtUseStr != null && Boolean.valueOf(mtUseStr) != false);
                    if (loaded.isMtUse()) {
                        loaded.setMtTimezone(elBroker.getAttributeValue("mtTimezone"));
                        loaded.setPostfix(elBroker.getAttributeValue("mtPostfix"));
                    }
                    ArrayList<BrokerStockDto> stocks = new ArrayList<BrokerStockDto>();
                    Element stocksEl = elBroker.getChild("Stocks");
                    if (stocksEl != null) {
                        for (Element stockEl : stocksEl.getChildren("Stock")) {
                            BrokerStockDto dto = new BrokerStockDto();
                            dto.setTicker(stockEl.getAttributeValue("name"));
                            stocks.add(dto);
                        }
                        if (!stocks.isEmpty()) {
                            loaded.setStockPickerUse(true);
                        }
                    }
                    if (!(storedName = name.trim()).startsWith("[")) {
                        storedName = "[" + storedName;
                    }
                    if (!storedName.endsWith("]")) {
                        storedName = storedName + "]";
                    }
                    if ((existing = BrokerManager.getInstance().getBroker(storedName)) != null && !overwrite) {
                        skipped.add(name);
                        continue;
                    }
                    if (existing != null) {
                        loaded.setId(existing.getId());
                    }
                    BrokerManager.getInstance().saveBroker(loaded);
                    BrokerManager.getInstance().saveStocks(loaded.getId().intValue(), stocks);
                    imported.add(loaded.getName());
                }
                BrokerManager.getInstance().refresh();
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBrokers(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                response.put("brokers", (Object)BrokerServlet.toJsonArray(imported));
                if (!skipped.isEmpty()) {
                    response.put("skippedExisting", (Object)BrokerServlet.toJsonArray(skipped));
                }
                response.put("success", (Object)L.t((String)"Brokers (%d) loaded.", (Object[])new Object[]{imported.size()}));
                return response.toString();
            }
            BrokerDto broker = args.containsKey("broker") && !args.get("broker")[0].trim().isEmpty() ? ((ref = args.get("broker")[0].trim()).matches("-?\\d+") ? BrokerManager.getInstance().getBroker(Integer.valueOf(ref)) : BrokerManager.getInstance().getBroker(ref)) : BrokerManager.getInstance().getDefaultBroker();
            if (broker == null) {
                throw new IllegalArgumentException(L.t((String)"Broker was not found", (Object[])new Object[0]));
            }
            int brokerId = broker.getId();
            BrokerXmlImporter importer = new BrokerXmlImporter();
            LinkedList<String> sessionsImported = new LinkedList<String>();
            LinkedList<String> instrumentsImported = new LinkedList<String>();
            for (Session session : importer.importSessions(filePath, null)) {
                this.performImportSession(session, brokerId, postfix, broker);
                sessionsImported.add(session.getSessionName() + postfix);
            }
            for (InstrumentInfo instrumentInfo : importer.importInstruments(filePath, null)) {
                this.performImportInstrument(instrumentInfo, brokerId, postfix, broker);
                instrumentsImported.add(instrumentInfo.instrument);
            }
            if (sessionsImported.isEmpty() && instrumentsImported.isEmpty()) {
                throw new Exception(L.t((String)"No Brokers found to import.", (Object[])new Object[0]));
            }
            if (!sessionsImported.isEmpty()) {
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSessions(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            }
            if (!instrumentsImported.isEmpty()) {
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            }
            response.put("broker", (Object)broker.getName());
            response.put("brokerId", brokerId);
            response.put("sessions", (Object)BrokerServlet.toJsonArray(sessionsImported));
            response.put("instruments", (Object)BrokerServlet.toJsonArray(instrumentsImported));
            response.put("success", (Object)L.t((String)"File imported", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return BrokerServlet.apiErrorJSON((String)L.t((String)"Cannot import XML file.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private static JSONArray toJsonArray(List<String> values) {
        JSONArray out = new JSONArray();
        for (String value : values) {
            out.put((Object)value);
        }
        return out;
    }

    private String onSave(Map<String, String[]> args) {
        try {
            String[] ids;
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            Element elSessions = new Element("Brokers");
            for (String id : ids = this.tryGetParam(args, "ids[]")) {
                BrokerDto broker = BrokerManager.getInstance().getBroker(Integer.valueOf(id));
                List stocks = BrokerManager.getInstance().getStocks(broker.getId().intValue());
                elSessions.addContent((Content)this.toXML(broker, stocks));
            }
            XMLUtil.xmlToFile((Element)elSessions, (File)file);
            response.put("success", (Object)L.t((String)"Brokers saved.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return BrokerServlet.apiErrorJSON((String)L.t((String)"Cannot save brokers.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private Element toXML(BrokerDto broker, List<String> stocks) {
        Element elBroker = new Element("Broker");
        elBroker.setAttribute("name", broker.getName());
        elBroker.setAttribute("stockPickerUse", String.valueOf(broker.isStockPickerUse()));
        elBroker.setAttribute("mtUse", String.valueOf(broker.isMtUse()));
        if (broker.isMtUse()) {
            elBroker.setAttribute("mtTimezone", broker.getMtTimezone());
            elBroker.setAttribute("mtPostfix", broker.getPostfix());
        }
        Element descEl = new Element("Desc");
        descEl.setText(broker.getDesc());
        elBroker.addContent((Content)descEl);
        Element elStocks = new Element("Stocks");
        elBroker.addContent((Content)elStocks);
        for (String stock : stocks) {
            Element elStockElement = new Element("Stock");
            elStockElement.setAttribute("name", stock);
            elStocks.addContent((Content)elStockElement);
        }
        return elBroker;
    }

    private String onUpdateData(Map<String, String[]> parameterMap) throws Exception {
        if (!DownloadSemaphore.getInstance().startDownloadData(5)) {
            return BrokerServlet.apiErrorJSON((String)L.t((String)"Please wait couple of seconds and try again.", (Object[])new Object[0]), null);
        }
        try {
            String[] groupIdsStr = this.tryGetParamValue(parameterMap, "brokerId").split(",");
            final LinkedList<String> stocks = new LinkedList<String>();
            for (String idStr : groupIdsStr) {
                Integer brokerId = Integer.valueOf(idStr);
                BrokerDto dto = BrokerManager.getInstance().getBroker(brokerId);
                if (dto == null) {
                    DownloadSemaphore.getInstance().downloadFinished();
                    return BrokerServlet.apiErrorJSON((String)L.t((String)"Broker doesn't exist", (Object[])new Object[0]), null);
                }
                List stockList = BrokerManager.getInstance().getStocks(brokerId.intValue());
                for (String stock : stockList) {
                    if (stocks.contains(stock)) continue;
                    stocks.add(stock);
                }
            }
            if (stocks.isEmpty()) {
                DownloadSemaphore.getInstance().downloadFinished();
                return this.getSuccessResult(L.t((String)"Nothing to update. Broker is without any stocks.", (Object[])new Object[0]));
            }
            if (MainApp.runInConsoleWithoutActiveWebserver()) {
                this._onUpdateData(stocks);
            } else {
                new Thread(new Runnable(){
                    final /* synthetic */ BrokerServlet this$0;
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

    private void _onUpdateData(List<String> stocks) throws ProgramDoesntExistException, Exception {
        try {
            HashMap<String, String[]> args = new HashMap<String, String[]>();
            ArrayList<String> allSymbols = new ArrayList<String>();
            ArrayList<String> missingSymbols = new ArrayList<String>();
            WebSocketNotification.sendSuccess((String)L.t((String)"Loading stock informations.", (Object[])new Object[0]), (String[])new String[]{"QDM"});
            for (int i = 0; i < stocks.size(); ++i) {
                boolean symbolExists;
                String symbol = stocks.get(i);
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
            Collections.shuffle(allSymbols);
            args.put("updateSymbols", new String[]{String.join((CharSequence)",", allSymbols)});
            Program.get((String)"DataSourceSQEquityData").call("add", new Object[]{args});
        }
        catch (Exception e) {
            DownloadSemaphore.getInstance().downloadFinished();
            throw e;
        }
    }

    private String onExportStocks(Map<String, String[]> args) throws Exception {
        String filePath = this.tryGetParam(args, "filePath")[0];
        Integer brokerId = Integer.valueOf(this.tryGetParam(args, "brokerId")[0]);
        try {
            BrokerDto dto = BrokerManager.getInstance().getBroker(brokerId);
            if (dto == null) {
                return BrokerServlet.apiErrorJSON((String)L.t((String)"Broker doesn't exist.", (Object[])new Object[0]), null);
            }
            List stocks = BrokerManager.getInstance().getStocks(brokerId.intValue());
            this.writeStocksToCsv(filePath, stocks);
            return this.getSuccessResult(L.t((String)"Stocks were exported.", (Object[])new Object[0]));
        }
        catch (Exception e) {
            return BrokerServlet.apiErrorJSON((String)L.t((String)"Cannot export stocks.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private void writeStocksToCsv(String filePath, List<String> stocks) throws IOException {
        StringBuilder sb = new StringBuilder();
        for (String stock : stocks) {
            sb.append(stock);
            sb.append("\n");
        }
        Files.writeString(new File(filePath).toPath(), (CharSequence)sb.toString(), StandardOpenOption.CREATE);
    }

    private String onImportStocks(Map<String, String[]> args) throws Exception {
        String filePath = this.tryGetParam(args, "filePath")[0];
        Integer brokerId = Integer.valueOf(this.tryGetParam(args, "brokerId")[0]);
        String prefix = this.getParam(args, "prefix", "");
        try {
            BrokerDto dto = BrokerManager.getInstance().getBroker(brokerId);
            if (dto == null) {
                return BrokerServlet.apiErrorJSON((String)L.t((String)"Broker doesn't exist.", (Object[])new Object[0]), null);
            }
            if (dto.isSystem()) {
                return BrokerServlet.apiErrorJSON((String)L.t((String)"This broker profile can't be modified.", (Object[])new Object[0]), null);
            }
            if (!dto.isStockPickerUse()) {
                return BrokerServlet.apiErrorJSON((String)L.t((String)"This broker profile can't hold any stocks.", (Object[])new Object[0]), null);
            }
            String lines = Files.readString(new File(filePath).toPath());
            BrokerManager.getInstance().importFromCsv(lines, brokerId, prefix);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBrokers(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            return this.getSuccessResult(L.t((String)"Stocks were imported", (Object[])new Object[0]));
        }
        catch (Exception e) {
            return BrokerServlet.apiErrorJSON((String)L.t((String)"Cannot import stocks from file '%s'.", (Object[])new Object[]{filePath}), (Throwable)e);
        }
    }

    private String onDeleteBroker(Map<String, String[]> args) throws Exception {
        String[] brokers;
        for (String strBrokerId : brokers = this.tryGetParam(args, "brokers")[0].split("\\,")) {
            int id = Integer.valueOf(strBrokerId);
            BrokerDto broker = BrokerManager.getInstance().deleteBroker(id, false);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)broker.getName(), (String)"remove"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBrokers(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        return this.getSuccessResult(L.t((String)"Broker deleted", (Object[])new Object[0]));
    }

    private String getSuccessResult(String message) {
        JSONObject response = new JSONObject();
        response.put("success", (Object)message);
        return response.toString();
    }

    private String onSaveBroker(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(args, "name")[0];
            String desc = this.tryGetParam(args, "desc")[0];
            String idStr = this.tryGetParam(args, "id")[0];
            String postfix = this.tryGetParam(args, "postfix")[0];
            String mtTimezone = this.tryGetParam(args, "mtTimezone")[0];
            boolean mtUse = Boolean.valueOf(this.tryGetParam(args, "mtUse")[0]);
            boolean stockPickerUse = Boolean.valueOf(this.tryGetParam(args, "stockPickerUse")[0]);
            Integer id = null;
            try {
                id = Integer.valueOf(idStr);
            }
            catch (Exception exception) {
                // empty catch block
            }
            BrokerDto dto = new BrokerDto();
            dto.setId(id);
            dto.setName(name);
            dto.setDesc(desc);
            dto.setMtTimezone(mtTimezone);
            dto.setPostfix(postfix);
            dto.setStockPickerUse(stockPickerUse);
            dto.setMtUse(mtUse);
            BrokerManager.getInstance().saveBroker(dto);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBrokers(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            response.put("success", (Object)L.t((String)"broker saved.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return BrokerServlet.apiErrorJSON((String)L.t((String)"Cannot save broker.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onListBroker(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        JSONArray rows = new JSONArray();
        BrokerManager.getInstance().refresh();
        List brokers = BrokerManager.getInstance().getAllBrokers();
        for (int i = 0; i < brokers.size(); ++i) {
            BrokerDto info = (BrokerDto)brokers.get(i);
            JSONObject userdata = new JSONObject();
            userdata.put("id", (Object)info.getId());
            userdata.put("system", info.isSystem());
            userdata.put("name", (Object)info.getName());
            userdata.put("desc", (Object)info.getDesc());
            userdata.put("postfix", (Object)info.getPostfix());
            userdata.put("mtUse", info.isMtUse());
            userdata.put("mtTimezone", (Object)info.getMtTimezone());
            userdata.put("stockPickerUse", info.isStockPickerUse());
            userdata.put("customizedStocks", info.getCustomizedStocks());
            userdata.put("customizedInstruments", info.getCustomizedInstruments());
            userdata.put("customizedSessions", info.getCustomizedSessions());
            JSONObject row = new JSONObject();
            row.put("userdata", (Object)userdata);
            JSONArray data = new JSONArray();
            data.put((Object)info.getName());
            data.put((Object)info.getDesc());
            data.put((Object)info.getPostfix());
            data.put((Object)info.getMtTimezone());
            if (!MainApp.checkProduct((String)"QDM")) {
                data.put(info.getCustomizedStocks());
            }
            data.put(info.getCustomizedInstruments());
            if (!MainApp.checkProduct((String)"QDM")) {
                data.put(info.getCustomizedSessions());
            }
            row.put("data", (Object)data);
            rows.put((Object)row);
        }
        response.put("rows", (Object)rows);
        response.put("success", (Object)L.t((String)"Brokers listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onEditStocks(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        Integer brokerId = Integer.valueOf(this.tryGetParam(args, "id")[0]);
        String stocks = "";
        try {
            stocks = this.tryGetParam(args, "stocks")[0];
        }
        catch (Exception exception) {
            // empty catch block
        }
        List stocksDtos = BrokerManager.getInstance().updateStocksFromStr(stocks, brokerId, "");
        SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getBrokers(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        for (BrokerStockDto stockDto : stocksDtos) {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)stockDto.getTicker(), (String)"update"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        response.put("success", (Object)L.t((String)"Stocks saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onListStocks(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        Integer brokerId = Integer.valueOf(this.tryGetParam(args, "brokerId")[0]);
        BrokerDto dto = BrokerManager.getInstance().getBroker(brokerId);
        if (dto == null) {
            return BrokerServlet.apiErrorJSON((String)L.t((String)"Broker doesn't exist.", (Object[])new Object[0]), null);
        }
        List stocks = BrokerManager.getInstance().getStocks(brokerId.intValue());
        StringBuilder stocksStr = new StringBuilder();
        for (int i = 0; i < stocks.size(); ++i) {
            String stock = (String)stocks.get(i);
            stocksStr.append(stock);
            stocksStr.append("\n");
        }
        response.put("stocks", (Object)stocksStr);
        response.put("success", (Object)L.t((String)"Stocks listed.", (Object[])new Object[0]));
        return response.toString();
    }
}

