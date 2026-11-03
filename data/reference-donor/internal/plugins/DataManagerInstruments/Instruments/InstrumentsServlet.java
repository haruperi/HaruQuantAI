/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.consts.DataTypes
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.CommissionsMethod
 *  com.strategyquant.tradinglib.SwapMethod
 *  com.strategyquant.tradinglib.SwapTypes
 *  com.strategyquant.tradinglib.commissions.CommissionsMethodsList
 *  com.strategyquant.tradinglib.project.ProjectResources
 *  com.strategyquant.tradinglib.project.console.CLILogger
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
package com.strategyquant.plugin.DataManager.impl.Instruments;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.consts.DataTypes;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.SwapTypes;
import com.strategyquant.tradinglib.commissions.CommissionsMethodsList;
import com.strategyquant.tradinglib.project.ProjectResources;
import com.strategyquant.tradinglib.project.console.CLILogger;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerConfirm;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.io.PrintWriter;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.Locale;
import java.util.Map;
import java.util.TreeSet;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class InstrumentsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(InstrumentsServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "list": {
                return this.onList(args);
            }
            case "listInstruments": {
                return this.onListInstruments();
            }
            case "addInstrument": {
                return this.onAddInstrument(args);
            }
            case "editInstrument": {
                return this.onEditInstrument(args);
            }
            case "massEditInstrument": {
                return this.onMassEditInstrument(args);
            }
            case "removeInstrument": {
                return this.onRemoveInstrument(args);
            }
            case "listAliases": {
                return this.onListAliases();
            }
            case "addAlias": {
                return this.onAddAlias(args);
            }
            case "editAlias": {
                return this.onEditAlias(args);
            }
            case "removeAlias": {
                return this.onRemoveAlias(args);
            }
            case "load": {
                return this.onLoad(args);
            }
            case "save": {
                return this.onSave(args);
            }
            case "clone": {
                return this.onClone(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onClone(Map<String, String[]> args) {
        try {
            String name = this.tryGetParam(args, "name")[0];
            int broker = Integer.valueOf(this.tryGetParam(args, "broker")[0]);
            String clone = this.tryGetParam(args, "clone")[0];
            clone = BrokerManager.getInstance().getBrokerDependantName(clone, broker);
            if (InstrumentManager.checkInstrumentExists((String)clone)) {
                throw new Exception(L.t((String)"Instrument with name '%s' already exists.", (Object[])new Object[]{name}));
            }
            InstrumentInfo instrument = InstrumentManager.getInstrumentInfo((String)name);
            if (instrument == null) {
                throw new Exception(L.t((String)"Instrument with name '%s' doesn't exist.", (Object[])new Object[]{name}));
            }
            InstrumentInfo newInstrument = instrument.clone();
            newInstrument.broker = broker;
            newInstrument.instrument = clone;
            InstrumentManager.addInstrument((InstrumentInfo)newInstrument);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            JSONObject response = new JSONObject();
            response.put("success", (Object)L.t((String)"Instrument cloned.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot clone session.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onList(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            PrintWriter csv = null;
            try {
                csv = new PrintWriter(this.tryGetParam(parameterMap, "csv")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            ArrayList instruments = InstrumentManager.list();
            DecimalFormat df = new DecimalFormat("0", DecimalFormatSymbols.getInstance(Locale.ENGLISH));
            df.setMaximumFractionDigits(10);
            String header = "Instrument,Description,Point value,Pip/Tick size,Pip/Tick step,Default spread,Default slippage,Data type,Order size multiplier,Order size step";
            if (csv == null) {
                CLILogger.log((String)header);
            } else {
                csv.println(header);
            }
            for (int i = 0; i < instruments.size(); ++i) {
                InstrumentInfo info = (InstrumentInfo)instruments.get(i);
                String dataType = DataTypes.toString((int)info.dataType);
                String line = info.instrument + "," + info.description + "," + info.pointValue + "," + df.format(info.tickSize) + "," + df.format(info.tickStep) + "," + info.defaultSpread + "," + info.defaultSlippage + "," + dataType + "," + info.orderSizeMultiplier + "," + info.orderSizeStep;
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
        } else {
            int dataType;
            this.checkParamExists(parameterMap, new String[]{"type", "search"});
            String search = parameterMap.get("search")[0];
            try {
                dataType = Integer.parseInt(parameterMap.get("type")[0]);
            }
            catch (Exception ex) {
                dataType = -1;
            }
            Integer brokerId = null;
            try {
                brokerId = Integer.parseInt(parameterMap.get("broker")[0]);
            }
            catch (Exception header) {
                // empty catch block
            }
            ArrayList instruments = InstrumentManager.list();
            ArrayList<InstrumentInfo> instrumentsNew = new ArrayList<InstrumentInfo>();
            for (int i = 0; i < instruments.size(); ++i) {
                InstrumentInfo info = (InstrumentInfo)instruments.get(i);
                if (dataType != -1 && info.dataType != dataType || !this.checkFilter(info, search) || info.instrument.startsWith("[") && info.instrument.endsWith("]") || brokerId != null && info.broker != brokerId) continue;
                instrumentsNew.add(info);
            }
            JSONArray rows = new JSONArray();
            for (int i = 0; i < instrumentsNew.size(); ++i) {
                InstrumentInfo info = (InstrumentInfo)instrumentsNew.get(i);
                BrokerDto brokerDto = BrokerManager.getInstance().getBroker(Integer.valueOf(info.broker));
                JSONObject row = new JSONObject();
                row.put("id", (Object)("r" + i));
                JSONArray data = new JSONArray();
                data.put((Object)info.instrument);
                data.put((Object)info.description);
                data.put((Object)(brokerDto == null ? "SQ default" : brokerDto.getName()));
                data.put(info.pointValue);
                data.put(info.tickSize);
                data.put(info.tickStep);
                data.put(info.defaultSpread);
                data.put(info.defaultSlippage);
                if (!MainApp.checkProduct((String)"QDM")) {
                    data.put((Object)this.printCommission(info.commissions));
                }
                if (!MainApp.checkProduct((String)"QDM")) {
                    data.put((Object)this.printSwap(info.swap));
                }
                data.put((Object)DataTypes.toString((int)info.dataType));
                data.put(info.orderSizeMultiplier);
                data.put(info.orderSizeStep);
                row.put("data", (Object)data);
                rows.put((Object)row);
            }
            response.put("rows", (Object)rows);
        }
        response.put("success", (Object)L.t((String)"Instruments listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String printCommission(String config) {
        String text = "";
        try {
            Element elMethod = XMLUtil.stringToElement((String)config);
            String type = elMethod.getAttributeValue("type");
            Element elCommissions = new Element("Commissions");
            elCommissions.addContent((Content)elMethod);
            CommissionsMethod method = (CommissionsMethod)CommissionsMethodsList.get().findClassByName(type);
            method.setFromXML(elCommissions);
            text = method.printFormatedName();
        }
        catch (Exception e) {
            text = "?";
        }
        return text;
    }

    private String printSwap(String config) {
        String text = "No swap";
        try {
            if (config != null && !config.isEmpty()) {
                Element elMethod = XMLUtil.stringToElement((String)config);
                SwapMethod swap = new SwapMethod();
                swap.setFromXML(elMethod);
                text = swap.isUsed() ? "Long: " + swap.getLongSwap() + ", Short: " + swap.getShortSwap() + " " + SwapTypes.toString((String)swap.getType()) : "Not used";
            }
        }
        catch (Exception e) {
            text = "?";
        }
        return text;
    }

    private boolean checkFilter(InstrumentInfo info, String search) throws DataException {
        if ((search = search.trim().toLowerCase()).length() == 0) {
            return true;
        }
        return info.instrument.toLowerCase().contains(search) || info.description.toLowerCase().contains(search);
    }

    private String onListInstruments() {
        JSONObject response = new JSONObject();
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM"});
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot get list of instruments.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Instruments listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onListAliases() {
        JSONObject response = new JSONObject();
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getAliases(), (String[])new String[]{"SQUANT", "QDM"});
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot get list of data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onAddInstrument(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            int broker = Integer.parseInt(this.tryGetParam(args, "broker")[0]);
            double minDistance = Double.parseDouble(this.tryGetParam(args, "minDistance")[0]);
            String instrument = this.tryGetParam(args, "instrument")[0];
            String description = this.tryGetParam(args, "description")[0];
            double pointValue = Double.parseDouble(this.tryGetParam(args, "pointValue")[0]);
            double tickSize = Double.parseDouble(this.tryGetParam(args, "tickSize")[0]);
            double tickStep = Double.parseDouble(this.tryGetParam(args, "tickStep")[0]);
            double defaultSpread = Double.parseDouble(this.tryGetParam(args, "defaultSpread")[0]);
            double defaultSlippage = Double.parseDouble(this.tryGetParam(args, "defaultSlippage")[0]);
            String commissions = this.tryGetParam(args, "commissions")[0];
            byte dataType = Byte.parseByte(this.tryGetParam(args, "dataType")[0]);
            double orderSizeMultiplier = Double.parseDouble(this.getParam(args, "orderSizeMultiplier", "1"));
            double orderSizeStep = Double.parseDouble(this.getParam(args, "orderSizeStep", "1"));
            String exchange = null;
            String country = null;
            String sector = null;
            String swap = null;
            String cot = null;
            String string = description = description.equals("not set") ? "" : description;
            if (instrument.trim().isEmpty()) {
                throw new Exception(L.t((String)"Intrument cannot be empty.", (Object[])new Object[0]));
            }
            try {
                exchange = this.tryGetParam(args, "exchange")[0];
                if (InstrumentManager.trySaveExchange((String)exchange)) {
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getExchanges(), (String[])new String[]{"SQUANT", "QDM"});
                }
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                country = this.tryGetParam(args, "country")[0];
                if (InstrumentManager.trySaveCountry((String)country)) {
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getCountries(), (String[])new String[]{"SQUANT", "QDM"});
                }
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                sector = this.tryGetParam(args, "sector")[0];
                if (InstrumentManager.trySaveSector((String)sector)) {
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSectors(), (String[])new String[]{"SQUANT", "QDM"});
                }
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                swap = this.tryGetParam(args, "swap")[0];
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                cot = InstrumentsServlet.emptyToNull(this.tryGetParam(args, "cot")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            instrument = BrokerManager.getInstance().getBrokerDependantName(instrument, broker);
            InstrumentManager.addInstrument((String)instrument, (int)broker, (String)description, (double)pointValue, (double)tickSize, (double)tickStep, (double)defaultSpread, (double)defaultSlippage, (double)minDistance, (String)commissions, (byte)dataType, (String)exchange, (String)country, (String)sector, (String)swap, (double)orderSizeMultiplier, (double)orderSizeStep, (String)cot);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot add instrument.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Instrument added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onEditInstrument(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String instrument = this.tryGetParam(args, "instrument")[0];
            String exchange = null;
            String country = null;
            String sector = null;
            String swap = null;
            try {
                exchange = this.tryGetParam(args, "exchange")[0];
                if (InstrumentManager.trySaveExchange((String)exchange)) {
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getExchanges(), (String[])new String[]{"SQUANT", "QDM"});
                }
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                country = this.tryGetParam(args, "country")[0];
                if (InstrumentManager.trySaveCountry((String)country)) {
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getCountries(), (String[])new String[]{"SQUANT", "QDM"});
                }
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                sector = this.tryGetParam(args, "sector")[0];
                if (InstrumentManager.trySaveSector((String)sector)) {
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getSectors(), (String[])new String[]{"SQUANT", "QDM"});
                }
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                swap = this.tryGetParam(args, "swap")[0];
            }
            catch (Exception exception) {
                // empty catch block
            }
            InstrumentInfo info = InstrumentManager.getInstrumentInfo((String)instrument);
            String description = info.description;
            double pointValue = info.pointValue;
            double tickSize = info.tickSize;
            double tickStep = info.tickStep;
            double defaultSpread = info.defaultSpread;
            double defaultSlippage = info.defaultSlippage;
            double orderSizeMultiplier = info.orderSizeMultiplier;
            double orderSizeStep = info.orderSizeStep;
            double minDistance = info.minDistance;
            String commissions = info.commissions;
            byte dataType = (byte)info.dataType;
            String cot = info.cot;
            try {
                description = this.tryGetParam(args, "description")[0];
                description = description.equals("not set") ? "" : description;
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                pointValue = Double.parseDouble(this.tryGetParam(args, "pointValue")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                tickSize = Double.parseDouble(this.tryGetParam(args, "tickSize")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                minDistance = Double.parseDouble(this.tryGetParam(args, "minDistance")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                tickStep = Double.parseDouble(this.tryGetParam(args, "tickStep")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                defaultSpread = Double.parseDouble(this.tryGetParam(args, "defaultSpread")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                defaultSlippage = Double.parseDouble(this.tryGetParam(args, "defaultSlippage")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                commissions = this.tryGetParam(args, "commissions")[0];
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                dataType = Byte.parseByte(this.tryGetParam(args, "dataType")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                orderSizeMultiplier = Double.parseDouble(this.tryGetParam(args, "orderSizeMultiplier")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                orderSizeStep = Double.parseDouble(this.tryGetParam(args, "orderSizeStep")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                cot = InstrumentsServlet.emptyToNull(this.tryGetParam(args, "cot")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            InstrumentManager.updateInstrument((String)instrument, (String)description, (double)pointValue, (double)tickSize, (double)tickStep, (double)defaultSpread, (double)defaultSlippage, (double)minDistance, (String)commissions, (byte)dataType, (String)exchange, (String)country, (String)sector, (String)swap, (double)orderSizeMultiplier, (double)orderSizeStep, (String)cot);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)"", (String)"list"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot edit instrument.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Instrument updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onMassEditInstrument(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String[] instruments;
            for (String instrument : instruments = this.tryGetParam(args, "instruments[]")) {
                InstrumentInfo info = InstrumentManager.getInstrumentInfo((String)instrument);
                try {
                    if (this.getBoolean(args, "changeSwap")) {
                        info.swap = this.tryGetParam(args, "swap")[0];
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    if (this.getBoolean(args, "changePointValue")) {
                        info.pointValue = Double.parseDouble(this.tryGetParam(args, "pointValue")[0]);
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    if (this.getBoolean(args, "changeTickSize")) {
                        info.tickSize = Double.parseDouble(this.tryGetParam(args, "tickSize")[0]);
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    if (this.getBoolean(args, "changeMinDistance")) {
                        info.minDistance = Double.parseDouble(this.tryGetParam(args, "minDistance")[0]);
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    if (this.getBoolean(args, "changeTickStep")) {
                        info.tickStep = Double.parseDouble(this.tryGetParam(args, "tickStep")[0]);
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    if (this.getBoolean(args, "changeDefaultSpread")) {
                        info.defaultSpread = Double.parseDouble(this.tryGetParam(args, "defaultSpread")[0]);
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    if (this.getBoolean(args, "changeDefaultSlippage")) {
                        info.defaultSlippage = Double.parseDouble(this.tryGetParam(args, "defaultSlippage")[0]);
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    if (this.getBoolean(args, "changeCommisionModel")) {
                        info.commissions = this.tryGetParam(args, "commissions")[0];
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    if (this.getBoolean(args, "changeDataType")) {
                        info.dataType = Byte.parseByte(this.tryGetParam(args, "dataType")[0]);
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    if (this.getBoolean(args, "changeSizeMultiplier")) {
                        info.orderSizeMultiplier = Double.parseDouble(this.tryGetParam(args, "orderSizeMultiplier")[0]);
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    if (this.getBoolean(args, "changeOrderSizeStep")) {
                        info.orderSizeStep = Double.parseDouble(this.tryGetParam(args, "orderSizeStep")[0]);
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    if (this.getBoolean(args, "changeCot")) {
                        info.cot = InstrumentsServlet.emptyToNull(this.tryGetParam(args, "cot")[0]);
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                InstrumentManager.updateInstrument((InstrumentInfo)info);
            }
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)"", (String)"list"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot edit instrument.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Instrument updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private static String emptyToNull(String value) {
        return value == null || value.trim().isEmpty() ? null : value;
    }

    private boolean getBoolean(Map<String, String[]> args, String parameter) {
        try {
            String val = this.tryGetParamValue(args, parameter);
            return Boolean.valueOf(val);
        }
        catch (Exception e) {
            return false;
        }
    }

    private String onRemoveInstrument(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String[] instruments = this.tryGetParam(args, "instruments")[0].split("\\,");
            if (instruments.length > 10) {
                this.removeInstrumentsAsync(instruments);
                response.put("success", (Object)L.t((String)"Instruments removing.", (Object[])new Object[0]));
                return response.toString();
            }
            for (String instrument : instruments) {
                InstrumentManager.removeInstrument((String)instrument);
            }
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            response.put("success", (Object)L.t((String)"Instruments removed.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot remove instruments.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private void removeInstrumentsAsync(final String[] instruments) {
        final int total = instruments.length;
        new Thread(this){
            final /* synthetic */ InstrumentsServlet this$0;
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
                for (String instrument : instruments) {
                    try {
                        InstrumentManager.removeInstrument((String)instrument);
                        Integer percent = SQUtils.round((double)(100.0 * (double)count / (double)total));
                        progress.put("percent", (Object)percent);
                        progress.put("info", (Object)L.t((String)"Removed instrument '%s'", (Object[])new Object[]{instrument}));
                        if (percent == 100) {
                            progress.put("message", (Object)"Instruments removed");
                        }
                        DataManagerAddProgressSender.getInstance().sendData(progress);
                    }
                    catch (Exception e) {
                        errors.add(instrument);
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
                progress.put("message", (Object)"Instruments removed");
                if (errors.size() > 0) {
                    progress.put("error", (Object)L.t((String)"Could'd be deleted: %s", (Object[])new Object[]{String.join((CharSequence)",", errors)}));
                }
                DataManagerAddProgressSender.getInstance().sendData(progress);
            }
        }.start();
    }

    private String onAddAlias(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String instrument = this.tryGetParam(args, "instrument")[0];
            String alias = this.tryGetParam(args, "alias")[0];
            InstrumentManager.addAlias((String)alias, (String)instrument, (String)"");
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot add alias.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Alias added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onEditAlias(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String instrument = this.tryGetParam(args, "instrument")[0];
            String alias = this.tryGetParam(args, "alias")[0];
            String description = this.tryGetParam(args, "description")[0];
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot edit alias.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Alias updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveAlias(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String alias = this.tryGetParam(args, "alias")[0];
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot remove alias.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Alias removed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoad(Map<String, String[]> args) {
        try {
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            ArrayList<String> names = new ArrayList<String>();
            Element elInstruments = XMLUtil.fileToXmlElement((File)file);
            if (!elInstruments.getName().equals("Instruments")) {
                throw new Exception(L.t((String)"No Instruments found to import.", (Object[])new Object[0]));
            }
            HashMap<Integer, Integer> brokerIdMap = new HashMap<Integer, Integer>();
            for (Element elBrokerInfo : elInstruments.getChildren("Broker")) {
                BrokerDto broker = ProjectResources.loadBrokerElement((Element)elBrokerInfo);
                Integer originalBrokerId = broker.getId();
                BrokerDto existingBroker = BrokerManager.getInstance().getBroker(broker.getName());
                if (existingBroker != null) {
                    brokerIdMap.put(originalBrokerId, existingBroker.getId());
                    continue;
                }
                broker.setId(null);
                BrokerManager.getInstance().saveBroker(broker);
                brokerIdMap.put(originalBrokerId, broker.getId());
            }
            boolean overwriteAll = false;
            for (Element elInstrument : elInstruments.getChildren("InstrumentInfo")) {
                InstrumentInfo instrumentLoaded = new InstrumentInfo();
                instrumentLoaded.setFromXML(elInstrument);
                Integer instrumentBrokerId = (Integer)brokerIdMap.get(instrumentLoaded.broker);
                int n = instrumentLoaded.broker = instrumentBrokerId == null ? -1 : instrumentBrokerId;
                if (!InstrumentManager.checkInstrumentExists((String)instrumentLoaded.instrument)) {
                    ProjectResources.checkInstrumentExists((InstrumentInfo)instrumentLoaded);
                    names.add(instrumentLoaded.instrument);
                    continue;
                }
                String action = "";
                if (!overwriteAll) {
                    DataManagerConfirm.get().awaitConfirmation(L.t((String)"Overwrite confirm", (Object[])new Object[0]), L.t((String)"Instrument '%s' already exists, do you want to overwrite it with the imported one?", (Object[])new Object[]{instrumentLoaded.instrument}));
                    action = DataManagerConfirm.get().getConfirmedAction();
                }
                if (action.equals("skip")) continue;
                if (action.equals("cancel")) break;
                if (!action.equals("overwrite") && !action.equals("overwrite_all") && !overwriteAll) continue;
                if (action.equals("overwrite_all")) {
                    overwriteAll = true;
                }
                InstrumentManager.updateInstrument((InstrumentInfo)instrumentLoaded);
                names.add(instrumentLoaded.instrument);
            }
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            response.put("success", (Object)L.t((String)"Instruments (%d) loaded.", (Object[])new Object[]{names.size()}));
            return response.toString();
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot load instruments.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onSave(Map<String, String[]> args) {
        try {
            String filePath = this.tryGetParam(args, "filePath")[0];
            File file = new File(filePath);
            JSONObject response = new JSONObject();
            Element elInstruments = new Element("Instruments");
            String[] instruments = this.tryGetParam(args, "instruments")[0].split("\\,");
            TreeSet<Integer> usedBrokerIds = new TreeSet<Integer>();
            for (String instrument : instruments) {
                InstrumentInfo info = InstrumentManager.getInstrumentInfo((String)instrument);
                elInstruments.addContent((Content)info.getXML());
                usedBrokerIds.add(info.broker);
            }
            for (Integer brokerId : usedBrokerIds) {
                if (brokerId == -1) continue;
                BrokerDto broker = BrokerManager.getInstance().getBroker(brokerId);
                elInstruments.addContent((Content)ProjectResources.createBrokerElement((BrokerDto)broker));
            }
            XMLUtil.xmlToFile((Element)elInstruments, (File)file);
            response.put("success", (Object)L.t((String)"Instruments saved.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return InstrumentsServlet.apiErrorJSON((String)L.t((String)"Cannot save instruments.", (Object[])new Object[0]), (Throwable)e);
        }
    }
}

