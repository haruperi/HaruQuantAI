/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.lib.SQTime
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.mt5api;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.python.PythonRunner;
import java.io.File;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.locks.ReentrantLock;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Mt5ApiManager {
    private static final Logger Log = LoggerFactory.getLogger(Mt5ApiManager.class);
    private final ReentrantLock lock = new ReentrantLock(true);
    private static Mt5ApiManager instance = new Mt5ApiManager();
    private final PythonRunner pyRunner = new PythonRunner();

    public static Mt5ApiManager get() {
        return instance;
    }

    private Mt5ApiManager() {
    }

    public boolean isAvailable() {
        return !this.lock.isLocked();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String runPython(PythonRunner.ProgressCallback progressCallback, String ... stringArray) throws Exception {
        this.lock.lock();
        try {
            final AtomicReference<Object> atomicReference = new AtomicReference<Object>(null);
            final AtomicReference<Object> atomicReference2 = new AtomicReference<Object>(null);
            PythonRunner.ProgressCallbackAdapter progressCallbackAdapter = new PythonRunner.ProgressCallbackAdapter(this){
                final /* synthetic */ Mt5ApiManager this$0;
                {
                    this.this$0 = mt5ApiManager;
                }

                @Override
                public void onMessage(String string) {
                    Log.debug(string);
                }

                @Override
                public void onError(String string) {
                    Log.error("MT5 error: " + string);
                    atomicReference2.set(string);
                }

                @Override
                public void onResult(String string) {
                    atomicReference.set(string);
                }
            };
            PythonRunner.ProgressCallback progressCallback2 = progressCallback != null ? progressCallback : progressCallbackAdapter;
            this.pyRunner.run("mt5api.py", progressCallback2, stringArray);
            this.sleep();
            if (atomicReference.get() == null && atomicReference2.get() != null) {
                throw new RuntimeException(atomicReference2.get());
            }
            String string = atomicReference.get();
            return string;
        }
        finally {
            this.lock.unlock();
        }
    }

    private String runPython(String ... stringArray) throws Exception {
        return this.runPython((PythonRunner.ProgressCallback)null, stringArray);
    }

    public Map<String, Object> getPriceSymbolInfoJson(Source source, String string, String string2) throws Exception {
        List<String> list = this.buildParams(source, string, "symbol_price_info", "--symbol", string2);
        return this.parseJsonToMap(this.runPython(list.toArray(new String[0])));
    }

    public Map<String, Object> getSymbolInfoJson(Source source, String string, String string2) throws Exception {
        List<String> list = this.buildParams(source, string, "symbol_info", "--symbol", string2);
        return this.parseJsonToMap(this.runPython(list.toArray(new String[0])));
    }

    public File downloadData(Source source, String string, DataInfo dataInfo, long l, long l2, PythonRunner.ProgressCallback progressCallback) throws Exception {
        File file = this.pyRunner.getTmpFile("", ".csv");
        String string2 = dataInfo.timeframe.equals("TICK") ? "ticks" : "ohlc";
        LinkedList<String> linkedList = new LinkedList<String>(List.of("fetch", "--symbol", dataInfo.uSymbol, "--type", string2, "--output", file.getAbsolutePath()));
        if (l != -1L) {
            linkedList.addAll(List.of("--from-date", SQTime.toString((long)l, (DateTimeFormatter)DateTimeFormat.forPattern((String)"yyyy-MM-dd"))));
        }
        if (l2 != -1L) {
            linkedList.addAll(List.of("--to-date", SQTime.toString((long)l2, (DateTimeFormatter)DateTimeFormat.forPattern((String)"yyyy-MM-dd"))));
        }
        this.addRunningParameters(source, string, linkedList);
        this.runPython(progressCallback, linkedList.toArray(new String[0]));
        return file;
    }

    public List<JSONObject> getSymbolListJson(Source source, String string) throws Exception {
        List<String> list = this.buildParams(source, string, "symbol_list");
        String string2 = this.runPython(list.toArray(new String[0]));
        if (string2 == null) {
            return new LinkedList<JSONObject>();
        }
        JSONArray jSONArray = new JSONArray(string2);
        LinkedList<JSONObject> linkedList = new LinkedList<JSONObject>();
        for (int i = 0; i < jSONArray.length(); ++i) {
            JSONObject jSONObject = jSONArray.getJSONObject(i);
            String string3 = jSONObject.getString("path");
            int n = string3.lastIndexOf(92);
            String string4 = n >= 0 ? string3.substring(0, n) : string3;
            JSONObject jSONObject2 = new JSONObject();
            jSONObject2.put("name", (Object)jSONObject.getString("name"));
            jSONObject2.put("description", (Object)jSONObject.getString("description"));
            jSONObject2.put("category", (Object)jSONObject.getString("category"));
            jSONObject2.put("path", (Object)string4.replace('\\', '-'));
            linkedList.add(jSONObject2);
        }
        return linkedList;
    }

    private List<String> buildParams(Source source, String string, String ... stringArray) {
        LinkedList<String> linkedList = new LinkedList<String>(List.of(stringArray));
        this.addRunningParameters(source, string, linkedList);
        return linkedList;
    }

    private Map<String, Object> parseJsonToMap(String string) {
        JSONObject jSONObject = new JSONObject(string);
        HashMap<String, Object> hashMap = new HashMap<String, Object>();
        for (String string2 : jSONObject.keySet()) {
            hashMap.put(string2, jSONObject.get(string2));
        }
        return hashMap;
    }

    private void addRunningParameters(Source source, String string, List<String> list) {
        if (source == Source.portable) {
            if (string == null) {
                throw new RuntimeException("You have to select MT5 installation folder");
            }
            File file = new File(string, "terminal64.exe");
            if (!file.exists()) {
                throw new RuntimeException("Selected folder doesn't contains terminal64.exe");
            }
            list.add("--mt5-path");
            list.add(file.getAbsolutePath());
            list.add("--portable");
        }
    }

    private void sleep() {
        try {
            Thread.sleep(500L);
        }
        catch (InterruptedException interruptedException) {
            Thread.currentThread().interrupt();
        }
    }

    public void cancel() {
        if (this.pyRunner != null) {
            this.pyRunner.cancel();
        }
    }

    public double getTickSize(Map<String, Object> map) {
        return ((Number)map.get("tick_size")).doubleValue();
    }

    public double getTickStep(Map<String, Object> map) {
        return ((Number)map.get("tick_step")).doubleValue();
    }

    public double getPointValue(Map<String, Object> map) {
        double d = ((Number)map.get("point_value")).doubleValue();
        return d;
    }

    public double getDefaultSpread(Map<String, Object> map) {
        return ((Number)map.get("spread")).doubleValue();
    }

    public String getDescription(Map<String, Object> map) {
        return (String)map.get("description");
    }

    public static enum Source {
        installed,
        portable;

    }
}

