/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.session.NinjaTraderSessionReader
 *  com.strategyquant.datalib.session.NinjaTraderSessionReader$Result
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionElement
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender
 *  com.strategyquant.tradinglib.project.websocket.DataManagerConfirm
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
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
package com.strategyquant.plugin.DataManager.impl.Sessions;

import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.session.NinjaTraderSessionReader;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionElement;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerConfirm;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedList;
import java.util.Map;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SessionsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(SessionsServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "listSessions": {
                return this.onListSessions();
            }
            case "addSession": {
                return this.onAddSession(parameterMap);
            }
            case "updateSession": {
                return this.onUpdateSession(parameterMap);
            }
            case "removeSession": {
                return this.onRemoveSession(parameterMap);
            }
            case "load": {
                return this.onLoad(parameterMap);
            }
            case "save": {
                return this.onSave(parameterMap);
            }
            case "clone": {
                return this.onClone(parameterMap);
            }
            case "importNinjaTraderTemplates": {
                return this.onImportNinjaTraderTemplates(parameterMap);
            }
            case "listNinjaTraderTemplates": {
                return this.onListNinjaTraderTemplates(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onListSessions() {
        JSONObject response = new JSONObject();
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSessions(), (String[])new String[]{"SQUANT", "QDM"});
        }
        catch (Exception e) {
            return SessionsServlet.apiErrorJSON((String)L.t((String)"Cannot list sessions", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Session listed", (Object[])new Object[0]));
        return response.toString();
    }

    private String onAddSession(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(args, "name")[0];
            int broker = Integer.valueOf(this.tryGetParam(args, "broker")[0]);
            String[] elements = this.tryGetParam(args, "sessions[]");
            name = BrokerManager.getInstance().getBrokerDependantName(name, broker);
            Session session = new Session(name, this.getElements(elements));
            session.setBroker(broker);
            SessionManager.addSession((Session)session);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSessions(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception ex) {
            return SessionsServlet.apiErrorJSON((String)L.t((String)"Cannot add session", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Session added", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveSession(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String[] names = this.tryGetParam(args, "names")[0].split(",");
            if (names.length > 10) {
                this.removeSessionsAsync(names);
                response.put("success", (Object)L.t((String)"Sessions removing.", (Object[])new Object[0]));
                return response.toString();
            }
            for (int a = 0; a < names.length; ++a) {
                SessionManager.removeSession((String)names[a]);
            }
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSessions(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            response.put("success", (Object)L.t((String)"Session removed", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception ex) {
            return SessionsServlet.apiErrorJSON((String)L.t((String)"Cannot remove session", (Object[])new Object[0]), (Throwable)ex);
        }
    }

    private void removeSessionsAsync(final String[] names) {
        final int total = names.length;
        new Thread(this){
            final /* synthetic */ SessionsServlet this$0;
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
                for (int a = 0; a < names.length; ++a) {
                    try {
                        SessionManager.removeSession((String)names[a]);
                        Integer percent = SQUtils.round((double)(100.0 * (double)count / (double)total));
                        progress.put("percent", (Object)percent);
                        progress.put("info", (Object)L.t((String)"Removed session '%s'", (Object[])new Object[]{names[a]}));
                        if (percent == 100) {
                            progress.put("message", (Object)"Sessions removed");
                        }
                        DataManagerAddProgressSender.getInstance().sendData(progress);
                        continue;
                    }
                    catch (Exception e) {
                        errors.add(names[a]);
                        continue;
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
                progress.put("message", (Object)"Sessions removed");
                if (errors.size() > 0) {
                    progress.put("error", (Object)L.t((String)"Could'd be deleted: %s", (Object[])new Object[]{String.join((CharSequence)",", errors)}));
                }
                DataManagerAddProgressSender.getInstance().sendData(progress);
            }
        }.start();
    }

    private String onUpdateSession(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String name = this.tryGetParam(args, "name")[0];
            String[] elements = this.tryGetParam(args, "sessions[]");
            SessionManager.updateSession((String)name, this.getElements(elements));
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSessions(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception ex) {
            return SessionsServlet.apiErrorJSON((String)L.t((String)"Cannot modify session", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Session modified", (Object[])new Object[0]));
        return response.toString();
    }

    private ArrayList<SessionElement> getElements(String[] elements) throws Exception {
        ArrayList<SessionElement> sessionElements = new ArrayList<SessionElement>();
        for (String element : elements) {
            String[] elementData = element.split(",");
            if (elementData.length != 5) {
                throw new Exception(L.t((String)"Invalid session data length. Expected 5, got %d", (Object[])new Object[]{elementData.length}));
            }
            sessionElements.add(new SessionElement(elementData[0], elementData[1], elementData[2], elementData[3], elementData[4].equals("Yes")));
        }
        return sessionElements;
    }

    private String onLoad(Map<String, String[]> args) {
        try {
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            ArrayList<String> names = new ArrayList<String>();
            Element elSessions = XMLUtil.fileToXmlElement((File)file);
            if (!elSessions.getName().equals("Sessions")) {
                throw new Exception(L.t((String)"No Sessions found to import.", (Object[])new Object[0]));
            }
            for (Element elSession : elSessions.getChildren("Session")) {
                Session sessionLoaded = new Session();
                sessionLoaded.setFromXML(elSession);
                if (!SessionManager.checkSessionExists((String)sessionLoaded.getSessionName())) {
                    SessionManager.addSession((Session)sessionLoaded);
                    names.add(sessionLoaded.getSessionName());
                    continue;
                }
                DataManagerConfirm.get().awaitConfirmation(L.t((String)"Overwrite confirm", (Object[])new Object[0]), L.t((String)"Session '%s' already exists, do you want to overwrite it with the imported one?", (Object[])new Object[]{sessionLoaded.getSessionName()}));
                String action = DataManagerConfirm.get().getConfirmedAction();
                if (action.equals("skip")) continue;
                if (action.equals("cancel")) break;
                if (!action.equals("overwrite")) continue;
                SessionManager.updateSession((Session)sessionLoaded);
                names.add(sessionLoaded.getSessionName());
            }
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSessions(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            response.put("success", (Object)L.t((String)"Sessions (%d) loaded.", (Object[])new Object[]{names.size()}));
            return response.toString();
        }
        catch (Exception e) {
            return SessionsServlet.apiErrorJSON((String)L.t((String)"Cannot load sessions.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onSave(Map<String, String[]> args) {
        try {
            String[] names;
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            Element elSessions = new Element("Sessions");
            for (String name : names = this.tryGetParam(args, "names")[0].split(",")) {
                Session session = SessionManager.getSession((String)name);
                elSessions.addContent((Content)session.getXML());
            }
            XMLUtil.xmlToFile((Element)elSessions, (File)file);
            response.put("success", (Object)L.t((String)"Sessions saved.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return SessionsServlet.apiErrorJSON((String)L.t((String)"Cannot save sessions.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private static File defaultTemplatesFolder() {
        return new File(System.getProperty("user.home"), "Documents/NinjaTrader 8/templates/TradingHours");
    }

    private static File[] templateFiles(File target) throws Exception {
        if (!target.exists()) {
            throw new Exception(L.t((String)"'%s' does not exist.", (Object[])new Object[]{target.getAbsolutePath()}));
        }
        if (target.isFile()) {
            return new File[]{target};
        }
        File[] files = target.listFiles();
        ArrayList<File> xml = new ArrayList<File>();
        if (files != null) {
            for (int a = 0; a < files.length; ++a) {
                if (!files[a].isFile() || !files[a].getName().toLowerCase().endsWith(".xml")) continue;
                xml.add(files[a]);
            }
        }
        Collections.sort(xml);
        return xml.toArray(new File[0]);
    }

    private String onListNinjaTraderTemplates(Map<String, String[]> args) {
        try {
            File folder = SessionsServlet.hasParam(args, "path") ? new File(args.get("path")[0]) : SessionsServlet.defaultTemplatesFolder();
            JSONObject response = new JSONObject();
            JSONArray names = new JSONArray();
            response.put("folder", (Object)folder.getAbsolutePath());
            response.put("exists", folder.isDirectory());
            if (folder.isDirectory()) {
                File[] files = SessionsServlet.templateFiles(folder);
                for (int a = 0; a < files.length; ++a) {
                    names.put((Object)files[a].getName());
                }
            }
            response.put("templates", (Object)names);
            response.put("success", (Object)L.t((String)"%d template(s) found.", (Object[])new Object[]{names.length()}));
            return response.toString();
        }
        catch (Exception e) {
            return SessionsServlet.apiErrorJSON((String)L.t((String)"Cannot list NinjaTrader templates.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onImportNinjaTraderTemplates(Map<String, String[]> args) {
        try {
            File target = SessionsServlet.hasParam(args, "path") ? new File(args.get("path")[0]) : SessionsServlet.defaultTemplatesFolder();
            boolean overwrite = SessionsServlet.hasParam(args, "overwrite") && "true".equalsIgnoreCase(args.get("overwrite")[0]);
            File[] files = SessionsServlet.templateFiles(target);
            if (files.length == 0) {
                throw new Exception(L.t((String)"No .xml templates found in '%s'.", (Object[])new Object[]{target.getAbsolutePath()}));
            }
            JSONArray imported = new JSONArray();
            JSONArray skipped = new JSONArray();
            JSONArray failed = new JSONArray();
            int holidays = 0;
            int partialHolidays = 0;
            for (int a = 0; a < files.length; ++a) {
                if (files.length > 10) {
                    this.sendImportProgress(a, files.length, files[a].getName());
                }
                try {
                    NinjaTraderSessionReader.Result result = NinjaTraderSessionReader.read((File)files[a]);
                    Session session = result.session;
                    holidays += result.droppedHolidays;
                    partialHolidays += result.droppedPartialHolidays;
                    if (SessionManager.checkSessionExists((String)session.getSessionName())) {
                        if (!overwrite) {
                            skipped.put((Object)session.getSessionName());
                            continue;
                        }
                        SessionManager.updateSession((Session)session);
                    } else {
                        SessionManager.addSession((Session)session);
                    }
                    imported.put((Object)session.getSessionName());
                    continue;
                }
                catch (Exception e) {
                    failed.put((Object)new JSONObject().put("template", (Object)files[a].getName()).put("reason", (Object)String.valueOf(e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName())));
                }
            }
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSessions(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            JSONObject response = new JSONObject();
            response.put("imported", (Object)imported);
            response.put("skipped", (Object)skipped);
            response.put("failed", (Object)failed);
            response.put("droppedHolidays", holidays);
            response.put("droppedPartialHolidays", partialHolidays);
            response.put("success", (Object)L.t((String)"Imported %d session(s), skipped %d existing, %d failed. %d holidays and %d partial holidays were NOT imported - SQX has no equivalent.", (Object[])new Object[]{imported.length(), skipped.length(), failed.length(), holidays, partialHolidays}));
            return response.toString();
        }
        catch (Exception e) {
            return SessionsServlet.apiErrorJSON((String)L.t((String)"Cannot import NinjaTrader templates.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private void sendImportProgress(int done, int total, String template) {
        try {
            JSONObject progress = new JSONObject();
            progress.put("percent", (Object)SQUtils.round((double)(100.0 * (double)done / (double)total)));
            progress.put("info", (Object)L.t((String)"Reading '%s'", (Object[])new Object[]{template}));
            DataManagerAddProgressSender.getInstance().sendData(progress);
        }
        catch (Exception e) {
            Log.error("Cannot send import progress.", (Throwable)e);
        }
    }

    private static boolean hasParam(Map<String, String[]> args, String name) {
        return args != null && args.containsKey(name) && args.get(name).length > 0 && args.get(name)[0] != null && !args.get(name)[0].trim().isEmpty();
    }

    private String onClone(Map<String, String[]> args) {
        try {
            String name = this.tryGetParam(args, "name")[0];
            int broker = Integer.valueOf(this.tryGetParam(args, "broker")[0]);
            String clone = this.tryGetParam(args, "clone")[0];
            clone = BrokerManager.getInstance().getBrokerDependantName(clone, broker);
            Session session = SessionManager.getSession((String)clone);
            if (session != null) {
                throw new Exception(L.t((String)"Session with name '%s' already exists.", (Object[])new Object[]{name}));
            }
            session = SessionManager.getSession((String)name);
            if (session == null) {
                throw new Exception(L.t((String)"Session with name '%s' doesn't exist.", (Object[])new Object[]{name}));
            }
            Session newSession = new Session(clone, session.cloneElements());
            newSession.setBroker(broker);
            newSession.setTimeZone(session.getTimeZone());
            SessionManager.addSession((Session)newSession);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSessions(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            JSONObject response = new JSONObject();
            response.put("success", (Object)L.t((String)"Session cloned.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return SessionsServlet.apiErrorJSON((String)L.t((String)"Cannot clone session.", (Object[])new Object[0]), (Throwable)e);
        }
    }
}

