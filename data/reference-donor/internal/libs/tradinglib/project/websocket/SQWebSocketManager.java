/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.app.MainApp
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.console.CLILogger;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocket;
import com.strategyquant.tradinglib.project.websocket.WebSocketPublisher;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.concurrent.locks.StampedLock;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQWebSocketManager {
    private static final Logger Log = LoggerFactory.getLogger(SQWebSocketManager.class);
    private static LinkedHashMap<String, SQWebSocket> sockets = new LinkedHashMap();
    private static SQWebSocketManager instance;
    public HashMap<String, ArrayList<WebSocketPublisher>> appPublishers = new HashMap();
    private HashMap<String, ArrayList<DataToSend>> dataToSend = new HashMap();
    ArrayList<DataToSend> tempData = new ArrayList();
    private StampedLock lock = new StampedLock();

    public SQWebSocketManager() {
        if (!MainApp.runInConsole()) {
            Log.info("WebSocketManager initialized.");
        }
        new Thread(){

            @Override
            public void run() {
                while (true) {
                    try {
                        Thread.sleep(1000L);
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                    if (!MainApp.AppLoaded) continue;
                    SQWebSocketManager.this.sendData();
                }
            }
        }.start();
        instance = this;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void sendData() {
        try {
            long l = this.lock.writeLock();
            try {
                if (MainApp.runInConsoleWithoutActiveWebserver()) {
                    for (String string : this.appPublishers.keySet()) {
                        ArrayList<WebSocketPublisher> arrayList = this.appPublishers.get(string);
                        if (arrayList == null) continue;
                        for (int i = 0; i < arrayList.size(); ++i) {
                            WebSocketPublisher webSocketPublisher;
                            WebSocketPublisher webSocketPublisher2 = webSocketPublisher = arrayList.get(i);
                            synchronized (webSocketPublisher2) {
                                this.logCmdMessage(webSocketPublisher.getDataToSend());
                                arrayList.get(i).confirmBroadcast();
                                continue;
                            }
                        }
                    }
                } else {
                    this.sendCommonMessages();
                    if (!(MainApp.checkProduct((String)"AlgoWizard") || MainApp.checkProduct((String)"QDM") || MainApp.checkProduct((String)"BACKTESTNODE"))) {
                        this.sendProjectsUpdates();
                    }
                }
            }
            finally {
                this.lock.unlock(l);
            }
        }
        catch (Throwable throwable) {
            Log.error("WebSocketManager error", throwable);
        }
    }

    public void logCmdMessage(DataToSend ... dataToSendArray) {
        for (int i = 0; i < dataToSendArray.length; ++i) {
            DataToSend dataToSend = dataToSendArray[i];
            if (dataToSend == null) continue;
            if (dataToSend.getDataObject() != null) {
                this.printCmdMessage(dataToSend.getDataObject());
                continue;
            }
            if (dataToSend.getDataArray() == null) continue;
            for (int j = 0; j < dataToSend.getDataArray().length(); ++j) {
                this.printCmdMessage((JSONObject)dataToSend.getDataArray().get(j));
            }
        }
    }

    private void printCmdMessage(JSONObject jSONObject) {
        if (!jSONObject.has("logStr")) {
            return;
        }
        String string = "";
        if (jSONObject.has("key")) {
            string = string + jSONObject.getString("key") + ", ";
        }
        if (jSONObject.has("pct")) {
            if (jSONObject.getInt("pct") < 0) {
                string = string + "ERROR: ";
                string = string + jSONObject.getString("logStr") + ", ";
            } else {
                string = string + jSONObject.getString("logStr") + ", ";
                string = string + jSONObject.getInt("pct") + "%, ";
            }
        } else {
            string = string + jSONObject.getString("logStr") + ", ";
        }
        string = string.substring(0, string.length() - 2);
        CLILogger.log(string);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void sendCommonMessages() {
        HashMap<String, String> hashMap = new HashMap<String, String>();
        for (String string : sockets.keySet()) {
            try {
                this.tempData.clear();
                String string2 = this.normalizeSocketName(string);
                String string3 = (String)hashMap.get(string2);
                if (string3 == null) {
                    ArrayList<DataToSend> arrayList;
                    ArrayList<WebSocketPublisher> arrayList2 = this.appPublishers.get(string2);
                    if (arrayList2 != null) {
                        for (int i = 0; i < arrayList2.size(); ++i) {
                            WebSocketPublisher webSocketPublisher;
                            WebSocketPublisher webSocketPublisher2 = webSocketPublisher = arrayList2.get(i);
                            synchronized (webSocketPublisher2) {
                                this.tempData.add(webSocketPublisher.getDataToSend());
                                webSocketPublisher.confirmBroadcast();
                                continue;
                            }
                        }
                    }
                    if ((arrayList = this.dataToSend.get(string2)) != null) {
                        this.tempData.addAll(arrayList);
                    }
                    string3 = this.stringifyMessage(this.tempData);
                    hashMap.put(string2, string3);
                }
                if (string3.equals("{}")) continue;
                sockets.get(string).sendMessage(string3);
            }
            catch (Exception exception) {
                Log.error("Cannot send common message to socket '" + string + "'. ", (Throwable)exception);
            }
        }
        this.dataToSend.clear();
    }

    private String normalizeSocketName(String string) {
        String string2 = string;
        int n = string.indexOf("(");
        if (n > 0) {
            string2 = string.substring(0, n);
        }
        return string2;
    }

    private void sendProjectsUpdates() {
        List<SQProject> list = ProjectEngine.list();
        for (int i = 0; i < list.size(); ++i) {
            SQProject sQProject = list.get(i);
            this.sendProjectUpdates(sQProject);
        }
    }

    private void sendProjectUpdates(SQProject sQProject) {
        try {
            DataToSend dataToSend = sQProject.publisher.getDataToSend();
            sQProject.publisher.confirmBroadcast();
            if (dataToSend == null) {
                return;
            }
            String string = this.stringifyMessage(dataToSend);
            for (String string2 : sockets.keySet()) {
                SQWebSocket sQWebSocket = sockets.get(string2);
                try {
                    String string3 = this.normalizeSocketName(string2);
                    if (!SQWebSocketManager.getProductCode(sQProject.getName()).equals(string3)) continue;
                    sQWebSocket.sendMessage(string);
                }
                catch (Exception exception) {
                    Log.error("Cannot send project update to websocket '" + string2 + "'. ", (Throwable)exception);
                }
            }
        }
        catch (Exception exception) {
            Log.error("Cannot send update for project '" + sQProject.getName() + "'. ", (Throwable)exception);
        }
    }

    public static String getProductCode(String string) {
        switch (string) {
            case "Builder": {
                return "BUILDER";
            }
            case "Retester": {
                return "RETESTER";
            }
            case "Optimizer": {
                return "OPTIMIZER";
            }
            case "PortfolioMaster": {
                return "PORTFOLIOMASTER";
            }
            case "PortfolioComposer": {
                return "PORTFOLIOCOMPOSER";
            }
        }
        return "TASKMANAGER";
    }

    public static String getProjectName(String string) {
        switch (string) {
            case "BUILDER": {
                return "Builder";
            }
            case "RETESTER": {
                return "Retester";
            }
            case "OPTIMIZER": {
                return "Optimizer";
            }
            case "PORTFOLIOMASTER": {
                return "PortfolioMaster";
            }
            case "PORTFOLIOCOMPOSER": {
                return "PortfolioComposer";
            }
        }
        return null;
    }

    private String stringifyMessage(DataToSend ... dataToSendArray) {
        JSONObject jSONObject = new JSONObject();
        for (int i = 0; i < dataToSendArray.length; ++i) {
            DataToSend dataToSend = dataToSendArray[i];
            if (dataToSend == null) continue;
            if (dataToSend.getDataObject() != null) {
                jSONObject.put(dataToSend.getName(), (Object)dataToSend.getDataObject());
                continue;
            }
            if (dataToSend.getDataArray() == null) continue;
            jSONObject.put(dataToSend.getName(), (Object)dataToSend.getDataArray());
        }
        return jSONObject.toString();
    }

    private String stringifyMessage(ArrayList<DataToSend> arrayList) {
        JSONObject jSONObject = new JSONObject();
        for (int i = 0; i < arrayList.size(); ++i) {
            DataToSend dataToSend = arrayList.get(i);
            if (dataToSend == null) continue;
            if (dataToSend.getDataObject() != null) {
                jSONObject.put(dataToSend.getName(), (Object)dataToSend.getDataObject());
                continue;
            }
            if (dataToSend.getDataArray() == null) continue;
            jSONObject.put(dataToSend.getName(), (Object)dataToSend.getDataArray());
        }
        return jSONObject.toString();
    }

    public static SQWebSocketManager getInstance() {
        if (instance == null) {
            new SQWebSocketManager();
        }
        return instance;
    }

    public static void addToDataQueue(DataToSend dataToSend, String ... stringArray) {
        SQWebSocketManager.getInstance()._addToDataQueue(dataToSend, stringArray);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void addClient(SQWebSocket sQWebSocket) {
        long l = this.lock.writeLock();
        try {
            sockets.put(sQWebSocket.getUniqueId(), sQWebSocket);
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void removeClient(String string) {
        long l = this.lock.writeLock();
        try {
            sockets.remove(string);
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public boolean containsClient(String string) {
        long l = this.lock.readLock();
        try {
            boolean bl = sockets.containsKey(string);
            return bl;
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void addAppPublisher(String string, WebSocketPublisher webSocketPublisher) {
        long l = this.lock.writeLock();
        try {
            ArrayList<WebSocketPublisher> arrayList = this.appPublishers.get(string);
            if (arrayList == null) {
                arrayList = new ArrayList();
                arrayList.add(webSocketPublisher);
                this.appPublishers.put(string, arrayList);
            } else {
                arrayList.add(webSocketPublisher);
            }
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void removeAppPublisher(String string, WebSocketPublisher webSocketPublisher) {
        long l = this.lock.writeLock();
        try {
            ArrayList<WebSocketPublisher> arrayList = this.appPublishers.get(string);
            if (arrayList != null) {
                arrayList.remove(webSocketPublisher);
            } else {
                Log.error("Publisher for app '" + string + "' doesn't exist");
            }
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void resetPublishersLastData(String string) {
        long l = this.lock.writeLock();
        try {
            ArrayList<WebSocketPublisher> arrayList = this.appPublishers.get(SQWebSocketManager.getProductCode(string));
            if (arrayList == null) {
                return;
            }
            for (int i = 0; i < arrayList.size(); ++i) {
                arrayList.get(i).resetLastData();
            }
        }
        catch (Exception exception) {
            Log.error("Cannot reset last data of publishers of project " + string, (Throwable)exception);
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void _addToDataQueue(DataToSend dataToSend, String ... stringArray) {
        long l = this.lock.writeLock();
        try {
            for (int i = 0; i < stringArray.length; ++i) {
                String string = stringArray[i];
                ArrayList<DataToSend> arrayList = this.dataToSend.get(string);
                if (arrayList == null) {
                    arrayList = new ArrayList();
                    arrayList.add(dataToSend);
                    this.dataToSend.put(string, arrayList);
                    continue;
                }
                arrayList.add(dataToSend);
            }
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public boolean checkWebSocketsConnected() {
        long l = this.lock.readLock();
        try {
            for (String string : sockets.keySet()) {
                if (string.endsWith(")")) continue;
                boolean bl = true;
                return bl;
            }
            boolean bl = false;
            return bl;
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void sendProjectDataImmediately(SQProject sQProject) {
        long l = this.lock.readLock();
        try {
            this.sendProjectUpdates(sQProject);
        }
        finally {
            this.lock.unlock(l);
        }
    }
}

