/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.utils.JsonCreator
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.explore.Explore
 *  com.strategyquant.tradinglib.explore.ExploreOpenPositionMarks
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  it.unimi.dsi.fastutil.longs.Long2ObjectAVLTreeMap
 *  it.unimi.dsi.fastutil.longs.LongBidirectionalIterator
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  it.unimi.dsi.fastutil.objects.ObjectIterator
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.Explore;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.explore.Explore;
import com.strategyquant.tradinglib.explore.ExploreOpenPositionMarks;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import it.unimi.dsi.fastutil.longs.Long2ObjectAVLTreeMap;
import it.unimi.dsi.fastutil.longs.LongBidirectionalIterator;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import it.unimi.dsi.fastutil.objects.ObjectIterator;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ExploreServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(ExploreServlet.class);
    private static final String LOCK_EXPLORESERVLET = "ExploreServlet";
    private static IResultsGroupProvider rgProvider;
    private static final int MAX_CACHED_RESULTS = 15;
    private final DataCache dataCache = new DataCache(15);

    public ExploreServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "data": {
                return this.onData(parameterMap);
            }
            case "info": {
                return this.onInfo(parameterMap);
            }
            case "all": {
                return this.onAll(parameterMap);
            }
            case "release": {
                return this.onRelease(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onData(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"projectName", "databankName", "strategyName", "symbol", "dateFrom", "dateTo"});
        JsonCreator responseJSON = new JsonCreator();
        Explore explore = null;
        ResultsGroup resultsGroup = null;
        String identificator = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_EXPLORESERVLET);
            explore = (Explore)resultsGroup.specialValues().get(SpecialValues.Explore);
            identificator = this.getDataIdentificator(parameterMap, resultsGroup);
        }
        catch (RecordNotFoundException e) {
            Log.error("onData: " + e.getMessage());
            String string = ExploreServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_EXPLORESERVLET);
            }
        }
        if (explore == null) {
            responseJSON.put("total_count", (Object)0, true);
            responseJSON.beginObject();
            responseJSON.put("rows");
            responseJSON.beginArray();
            responseJSON.endArray(true);
            responseJSON.endObject(true);
            responseJSON.put("pos", (Object)0, false);
            return responseJSON.toString();
        }
        this.loadData(parameterMap, explore, identificator, responseJSON);
        return responseJSON.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onInfo(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[0]);
        JSONObject response = new JSONObject();
        JSONArray symbols = new JSONArray();
        JSONArray columns = new JSONArray();
        Explore explore = null;
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_EXPLORESERVLET);
            explore = (Explore)resultsGroup.specialValues().get(SpecialValues.Explore);
        }
        catch (RecordNotFoundException e) {
            Log.error("onData: " + e.getMessage());
            String string = ExploreServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_EXPLORESERVLET);
            }
        }
        if (explore != null) {
            ArrayList<String> list = new ArrayList<String>();
            ObjectIterator iterator = explore.getData().keySet().iterator();
            while (iterator.hasNext()) {
                list.add((String)iterator.next());
            }
            Collections.sort(list);
            for (int i = 0; i < list.size(); ++i) {
                symbols.put(list.get(i));
            }
            ObjectArrayList cols = explore.getColumns();
            for (int i = 0; i < cols.size(); ++i) {
                columns.put(cols.get(i));
            }
        }
        SettingsMap settings = resultsGroup.specialValues();
        String dateFrom = SQTime.toString((long)settings.getLong(SpecialValues.HistoryFrom), (String)"yyyy.MM.dd");
        String dateTo = SQTime.toString((long)settings.getLong(SpecialValues.HistoryTo), (String)"yyyy.MM.dd");
        response.put("symbols", (Object)symbols);
        response.put("dateFrom", (Object)dateFrom);
        response.put("dateTo", (Object)dateTo);
        response.put("columns", (Object)columns);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onAll(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"backtestID"});
        Explore explore = null;
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_EXPLORESERVLET);
            explore = (Explore)resultsGroup.specialValues().get(SpecialValues.Explore);
        }
        catch (RecordNotFoundException e) {
            Log.error("onAll: " + e.getMessage());
            String string = ExploreServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_EXPLORESERVLET);
            }
        }
        JSONObject response = new JSONObject();
        response.put("success", (Object)"ok");
        if (explore == null) {
            response.put("available", false);
            response.put("reason", (Object)"none");
            return response.toString();
        }
        if (!explore.isOpenPositionMarks()) {
            response.put("available", false);
            response.put("reason", (Object)"rule");
            return response.toString();
        }
        byte[] content = ExploreOpenPositionMarks.encode((Explore)explore);
        response.put("available", true);
        response.put("format", 1);
        response.put("symbols", explore.getData().size());
        response.put("marks", ExploreOpenPositionMarks.countMarks((Explore)explore));
        response.put("content", (Object)Base64.getEncoder().encodeToString(content));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onRelease(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"backtestID"});
        boolean released = false;
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_EXPLORESERVLET);
            released = ExploreOpenPositionMarks.release((ResultsGroup)resultsGroup);
        }
        catch (RecordNotFoundException e) {
            Log.error("onRelease: " + e.getMessage());
            String string = ExploreServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_EXPLORESERVLET);
            }
        }
        JSONObject response = new JSONObject();
        response.put("success", (Object)"ok");
        response.put("released", released);
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void loadData(Map<String, String[]> parameterMap, Explore explore, String identificator, JsonCreator json) {
        int start = 0;
        int count = 100;
        try {
            start = Integer.parseInt(parameterMap.get("posStart")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            count = Integer.parseInt(parameterMap.get("count")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        json.beginObject();
        json.put("rows");
        json.beginArray();
        try {
            ArrayList<Object[]> rowData = null;
            DataCache dataCache = this.dataCache;
            synchronized (dataCache) {
                rowData = (ArrayList<Object[]>)this.dataCache.get(identificator);
            }
            if (rowData == null) {
                rowData = this.generateNewData(explore, parameterMap);
                dataCache = this.dataCache;
                synchronized (dataCache) {
                    this.dataCache.put(identificator, rowData);
                }
            }
            for (int a = start; a < rowData.size() && a < start + count; ++a) {
                json.beginObject();
                json.put("data");
                json.beginArray();
                for (int i = 0; i < rowData.get(a).length; ++i) {
                    Object value = rowData.get(a)[i];
                    if (i < rowData.get(a).length - 1) {
                        json.setValue(value, true);
                        continue;
                    }
                    json.setValue(value, false);
                }
                json.endArray(true);
                json.put("id", (Object)("r" + (a + 1)), false);
                json.endObject(a < rowData.size() - 1 && a < start + count - 1);
            }
            json.endArray(true);
            json.put("total_count", (Object)rowData.size(), true);
            json.put("pos", (Object)start, false);
            json.endObject(false);
        }
        catch (Exception ex) {
            Log.error("Getting trades failed", (Throwable)ex);
        }
    }

    private ArrayList<Object[]> generateNewData(Explore explore, Map<String, String[]> parameterMap) throws Exception {
        String symbol = this.tryGetParamValue(parameterMap, "symbol");
        long dateFrom = SQTime.parseToMilis((String)this.tryGetParamValue(parameterMap, "dateFrom"), (String)"yyyy.MM.dd");
        long dateTo = SQTime.parseToMilis((String)this.tryGetParamValue(parameterMap, "dateTo"), (String)"yyyy.MM.dd");
        ArrayList<Object[]> data = new ArrayList<Object[]>();
        int columnsCount = explore.getColumns().size();
        Long2ObjectAVLTreeMap sd = explore.getSymbolData(symbol);
        if (sd == null) {
            throw new Exception(L.t((String)"No data found for symbol %s", (Object[])new Object[]{symbol}));
        }
        LongBidirectionalIterator i = sd.keySet().iterator();
        while (i.hasNext()) {
            long date = (Long)i.next();
            if (date < dateFrom) continue;
            if (date > dateTo) break;
            Object[] row = new Object[columnsCount + 2];
            row[0] = symbol;
            row[1] = SQTime.toFullDateMinuteString((long)date);
            double[] values = (double[])sd.get(date);
            for (int c = 0; c < columnsCount; ++c) {
                row[c + 2] = values[c];
            }
            data.add(row);
        }
        return data;
    }

    private String getDataIdentificator(Map<String, String[]> parameterMap, ResultsGroup rg) {
        StringBuilder builder = new StringBuilder();
        builder.append(this.getParam(parameterMap, "projectName"));
        builder.append(this.getParam(parameterMap, "databankName"));
        builder.append(parameterMap.containsKey("backtestID") ? this.getParam(parameterMap, "backtestID") : this.getParam(parameterMap, "strategyName"));
        builder.append(this.getParam(parameterMap, "symbol"));
        builder.append(this.getParam(parameterMap, "dateFrom"));
        builder.append(this.getParam(parameterMap, "dateTo"));
        builder.append(this.getParam(parameterMap, "sortColumn"));
        builder.append(this.getParam(parameterMap, "asc"));
        builder.append("#");
        builder.append(rg.specialValues().getLong(SpecialValues.LastModified));
        return builder.toString();
    }

    static class DataCache
    extends LinkedHashMap<String, ArrayList<Object[]>> {
        private static final long serialVersionUID = 1L;
        private final int maxEntries;

        DataCache(int maxEntries) {
            super(16, 0.75f, true);
            this.maxEntries = maxEntries;
        }

        @Override
        protected boolean removeEldestEntry(Map.Entry<String, ArrayList<Object[]>> eldest) {
            return this.size() > this.maxEntries;
        }
    }
}

