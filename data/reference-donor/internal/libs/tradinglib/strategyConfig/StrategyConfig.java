/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.pluginlib.SQPluginManager
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.strategyConfig;

import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.simulator.Engines;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyConfig {
    private static final Logger Log = LoggerFactory.getLogger(StrategyConfig.class);

    public JSONArray print(List<String> list, Element element, Element element2) {
        JSONArray jSONArray = new JSONArray();
        JSONArray jSONArray2 = null;
        JSONArray jSONArray3 = null;
        int n = this.getEngine(element);
        int n2 = this.getEngine(element2);
        ArrayList arrayList = SQPluginManager.getPlugins(ISettingTabPlugin.class);
        for (ISettingTabPlugin iSettingTabPlugin : arrayList) {
            for (String string : list) {
                String string2 = iSettingTabPlugin.getSettingName();
                if (!string2.equals(string)) continue;
                String string3 = iSettingTabPlugin.getName();
                try {
                    JSONObject jSONObject;
                    JSONObject jSONObject2 = new JSONObject();
                    jSONObject2.put("name", (Object)string3);
                    jSONObject2.put("key", (Object)string2);
                    JSONArray jSONArray4 = new JSONArray();
                    JSONArray jSONArray5 = new JSONArray();
                    if (element != null) {
                        iSettingTabPlugin.getStrategyConfigSettings(element, jSONArray4);
                    }
                    if (element2 != null) {
                        iSettingTabPlugin.getStrategyConfigSettings(element2, jSONArray5);
                    }
                    if (string2.equals("Data")) {
                        try {
                            String string4;
                            int n3;
                            for (n3 = 0; n3 < jSONArray4.length(); ++n3) {
                                jSONObject = jSONArray4.getJSONObject(n3);
                                string4 = jSONObject.getString("key");
                                if (string4 == null || !string4.equals("Instruments")) continue;
                                jSONArray2 = ((JSONObject)jSONArray4.remove(n3)).getJSONArray("value");
                                break;
                            }
                            for (n3 = 0; n3 < jSONArray5.length(); ++n3) {
                                jSONObject = jSONArray5.getJSONObject(n3);
                                string4 = jSONObject.getString("key");
                                if (string4 == null || !string4.equals("Instruments")) continue;
                                jSONArray3 = ((JSONObject)jSONArray5.remove(n3)).getJSONArray("value");
                                break;
                            }
                        }
                        catch (Exception exception) {
                            Log.error("Cannot load instrument settings", (Throwable)exception);
                        }
                    }
                    if (string2.equals("Options")) {
                        if (Engines.isAWCloudEngine(n) || Engines.isAWCloudEngine(n2)) {
                            JSONArray jSONArray6 = this.printSettings(Engines.isAWCloudEngine(n) ? (jSONArray4.length() > 0 ? jSONArray4.getJSONArray(0) : new JSONArray()) : new JSONArray(), Engines.isAWCloudEngine(n2) ? (jSONArray5.length() > 0 ? jSONArray5.getJSONArray(0) : new JSONArray()) : new JSONArray(), string2);
                            if (jSONArray6.length() > 0) {
                                jSONObject = new JSONObject();
                                jSONObject.put("name", (Object)L.t((String)"Trading options (AWCloud engines)", (Object[])new Object[0]));
                                jSONObject.put("key", (Object)"Trading options (AWCloud engines)");
                                jSONObject.put("settings", (Object)jSONArray6);
                                jSONArray.put((Object)jSONObject);
                            }
                        }
                        if (!Engines.isStandardEngine(n) && !Engines.isStandardEngine(n2)) continue;
                        JSONArray jSONArray7 = this.printSettings(Engines.isStandardEngine(n) ? (jSONArray4.length() > 1 ? jSONArray4.getJSONArray(1) : new JSONArray()) : new JSONArray(), Engines.isStandardEngine(n2) ? (jSONArray5.length() > 1 ? jSONArray5.getJSONArray(1) : new JSONArray()) : new JSONArray(), string2);
                        if (jSONArray7.length() <= 0) continue;
                        jSONObject = new JSONObject();
                        jSONObject.put("name", (Object)L.t((String)"Trading options (standard engines)", (Object[])new Object[0]));
                        jSONObject.put("key", (Object)"Trading options (standard engines)");
                        jSONObject.put("settings", (Object)jSONArray7);
                        jSONArray.put((Object)jSONObject);
                        continue;
                    }
                    if (string2.equals("CrossChecks") || string2.equals("ATMs")) {
                        JSONArray jSONArray8 = this.printSettings(Engines.isAWCloudEngine(n) ? new JSONArray() : jSONArray4, Engines.isAWCloudEngine(n2) ? new JSONArray() : jSONArray5, string2);
                        if (jSONArray8.length() == 0) continue;
                        jSONObject2.put("settings", (Object)jSONArray8);
                        jSONArray.put((Object)jSONObject2);
                        continue;
                    }
                    JSONArray jSONArray9 = this.printSettings(jSONArray4, jSONArray5, string2);
                    if (jSONArray9.length() == 0) continue;
                    jSONObject2.put("settings", (Object)jSONArray9);
                    jSONArray.put((Object)jSONObject2);
                }
                catch (Exception exception) {
                    Log.error("Error while loading '" + string3 + "' settings. Exc.", (Throwable)exception);
                }
            }
        }
        if (jSONArray2 != null || jSONArray3 != null) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("name", (Object)"Instruments");
            jSONObject.put("key", (Object)"Instruments");
            jSONObject.put("settings", (Object)this.printSettings(jSONArray2, jSONArray3, "Instruments"));
            jSONArray.put((Object)jSONObject);
        }
        return jSONArray;
    }

    private int getEngine(Element element) {
        if (element != null) {
            try {
                Element element2;
                Element element3 = element.getChild("Data");
                if (element3 != null && (element2 = element3.getChild("Setups").getChild("Setup")) != null) {
                    int n = Engines.getEngine(element2.getAttributeValue("engine"));
                    return n;
                }
            }
            catch (Exception exception) {
                Log.error("Failed to parse engine.", (Throwable)exception);
            }
        }
        return -1;
    }

    private JSONArray printSettings(JSONArray jSONArray, JSONArray jSONArray2, String string) {
        JSONObject jSONObject;
        String string2;
        String string3;
        String string4;
        JSONObject jSONObject2;
        int n;
        JSONArray jSONArray3 = new JSONArray();
        if (jSONArray != null) {
            for (n = 0; n < jSONArray.length(); ++n) {
                jSONObject2 = jSONArray.getJSONObject(n);
                string4 = jSONObject2.getString("key");
                string3 = jSONObject2.get("value") + "";
                String string5 = string2 = jSONArray2 != null ? this.getValueByKey(jSONArray2, string4) : null;
                if (string2 == null) {
                    string2 = string.equals("Blocks") || string.equals("CrossChecks") ? L.t((String)"no", (Object[])new Object[0]) : L.t((String)"N/A", (Object[])new Object[0]);
                }
                jSONObject = new JSONObject();
                jSONObject.put("key", (Object)string4);
                jSONObject.put("value_str", (Object)string3.replaceAll("\n", "<br>"));
                jSONObject.put("value_task", (Object)string2.replaceAll("\n", "<br>"));
                jSONObject.put("match", string3.equals(string2));
                jSONArray3.put((Object)jSONObject);
            }
        }
        if (jSONArray2 != null) {
            for (n = 0; n < jSONArray2.length(); ++n) {
                jSONObject2 = jSONArray2.getJSONObject(n);
                string4 = jSONObject2.getString("key");
                if (this.containsKey(jSONArray3, string4)) continue;
                string3 = jSONObject2.get("value") + "";
                string2 = string.equals("Blocks") || string.equals("CrossChecks") ? L.t((String)"no", (Object[])new Object[0]) : L.t((String)"N/A", (Object[])new Object[0]);
                jSONObject = new JSONObject();
                jSONObject.put("key", (Object)string4);
                jSONObject.put("value_str", (Object)string2.replaceAll("\n", "<br>"));
                jSONObject.put("value_task", (Object)string3.replaceAll("\n", "<br>"));
                jSONObject.put("match", string2.equals(string3));
                if (jSONArray3.length() > n) {
                    this.addToPos(n, jSONObject, jSONArray3);
                    continue;
                }
                jSONArray3.put((Object)jSONObject);
            }
        }
        return jSONArray3;
    }

    public void addToPos(int n, JSONObject jSONObject, JSONArray jSONArray) {
        for (int i = jSONArray.length(); i > n; --i) {
            jSONArray.put(i, jSONArray.get(i - 1));
        }
        jSONArray.put(n, (Object)jSONObject);
    }

    private boolean containsKey(JSONArray jSONArray, String string) {
        for (int i = 0; i < jSONArray.length(); ++i) {
            JSONObject jSONObject = jSONArray.getJSONObject(i);
            if (!jSONObject.getString("key").equals(string)) continue;
            return true;
        }
        return false;
    }

    private String getValueByKey(JSONArray jSONArray, String string) {
        for (int i = 0; i < jSONArray.length(); ++i) {
            JSONObject jSONObject = jSONArray.getJSONObject(i);
            if (jSONObject == null || jSONObject.getString("key") == null || !jSONObject.getString("key").equals(string)) continue;
            return jSONObject.get("value") + "";
        }
        return null;
    }
}

