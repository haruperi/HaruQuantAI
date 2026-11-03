/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntIterator
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StrategySaver;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntIterator;
import java.io.File;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategiesSaver {
    public static final Logger Log = LoggerFactory.getLogger((String)"StrategiesSaver");
    private static final String LOCK_STRATEGIESSAVER = "StrategiesSaver";
    private static boolean stopped = false;

    public static void saveAll(boolean bl, String string) {
        Object object;
        List<SQProject> list = ProjectEngine.list();
        int n = 0;
        stopped = false;
        for (int i = 0; i < list.size() && !stopped; ++i) {
            SQProject sQProject = list.get(i);
            object = sQProject.getDatabanks().list();
            for (int j = 0; j < ((ArrayList)object).size() && !stopped; ++j) {
                if (!bl && ((Databank)((ArrayList)object).get(j)).isFileBased() || ((Databank)((ArrayList)object).get(j)).getName().equals("Last generation")) continue;
                n += ((Databank)((ArrayList)object).get(j)).size();
            }
        }
        StrategySavedListener strategySavedListener = new StrategySavedListener(n, true);
        strategySavedListener.onStart();
        for (int i = 0; i < list.size() && !stopped; ++i) {
            object = list.get(i);
            ArrayList<Databank> arrayList = ((SQProject)object).getDatabanks().list();
            for (int j = 0; j < arrayList.size() && !stopped; ++j) {
                Databank databank = arrayList.get(j);
                if (!bl && databank.isFileBased() || arrayList.get(j).getName().equals("Last generation")) continue;
                StrategiesSaver.syncDatabankToFiles((SQProject)object, databank, strategySavedListener, string);
            }
        }
        if (stopped) {
            Log.info("Saving stopped by user");
            strategySavedListener.onFinish(L.t((String)"Saving stopped by user", (Object[])new Object[0]), n);
        } else {
            strategySavedListener.onFinish(null, n);
        }
        try {
            Thread.sleep(1000L);
        }
        catch (Exception exception) {
            // empty catch block
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static void syncDatabankToFiles(SQProject sQProject, Databank databank, StrategySavedListener strategySavedListener, String string) {
        block31: {
            if (!MainApp.AppLoaded) {
                return;
            }
            if (databank.isLoading()) {
                return;
            }
            if (MainApp.runInConsoleWithoutActiveWebserver() && !databank.isLoaded()) {
                return;
            }
            int n = 0;
            int n2 = 0;
            int n3 = 0;
            long l = System.currentTimeMillis();
            try {
                String[] stringArray;
                int n4;
                String[] stringArray2;
                Serializable serializable;
                int n5;
                File[] fileArray;
                StrategySaver strategySaver = new StrategySaver();
                String string2 = null;
                ArrayList<String> arrayList = databank.getRecordKeys();
                File file = new File(databank.getDatabankFolder());
                if (!file.exists()) {
                    file.mkdirs();
                }
                if ((fileArray = file.listFiles()) == null) {
                    return;
                }
                n3 = fileArray.length;
                Int2ObjectOpenHashMap int2ObjectOpenHashMap = new Int2ObjectOpenHashMap();
                for (n5 = 0; n5 < fileArray.length && !stopped; ++n5) {
                    serializable = fileArray[n5];
                    stringArray2 = ((File)serializable).getAbsolutePath();
                    n4 = SQUtils.betterHashCode((String)stringArray2);
                    stringArray = (String[])int2ObjectOpenHashMap.get(n4);
                    if (stringArray == null) {
                        int2ObjectOpenHashMap.put(n4, (Object)new String[]{stringArray2});
                        continue;
                    }
                    int n6 = stringArray.length;
                    stringArray = Arrays.copyOf(stringArray, n6 + 1);
                    stringArray[n6] = stringArray2;
                    int2ObjectOpenHashMap.put(n4, (Object)stringArray);
                }
                for (n5 = 0; n5 < arrayList.size() && !stopped; ++n5) {
                    block30: {
                        try {
                            serializable = databank.getLocked(arrayList.get(n5), LOCK_STRATEGIESSAVER);
                            try {
                                stringArray2 = new File(((ResultsGroup)serializable).getFilePath()).getAbsolutePath();
                                n4 = SQUtils.betterHashCode((String)stringArray2);
                                stringArray = (String[])int2ObjectOpenHashMap.get(n4);
                                if (stringArray != null) {
                                    if (stringArray.length == 1) {
                                        int2ObjectOpenHashMap.remove(n4);
                                    } else {
                                        boolean bl = true;
                                        for (int i = 0; i < stringArray.length; ++i) {
                                            if (stringArray[i] == null) continue;
                                            if (stringArray2.equals(stringArray[i])) {
                                                stringArray[i] = null;
                                                continue;
                                            }
                                            bl = false;
                                        }
                                        if (bl) {
                                            int2ObjectOpenHashMap.remove(n4);
                                        }
                                    }
                                }
                                if (((ResultsGroup)serializable).updated) {
                                    try {
                                        strategySaver.save((ResultsGroup)serializable, "sqx", (String)stringArray2, false, 0);
                                        ((ResultsGroup)serializable).updated = false;
                                        ++n;
                                    }
                                    catch (Exception exception) {
                                        Log.error("Saving to '" + (String)stringArray2 + "' failed", (Throwable)exception);
                                        String string3 = L.t((String)"Saving strategy '%s' failed. ", (Object[])new Object[0]);
                                        string2 = String.format(string3, ((ResultsGroup)serializable).getName()) + exception.getMessage();
                                    }
                                }
                            }
                            finally {
                                if (serializable != null) {
                                    ((ResultsGroup)serializable).releaseLock(LOCK_STRATEGIESSAVER);
                                }
                            }
                        }
                        catch (Exception exception) {
                            if (exception instanceof RecordNotFoundException) break block30;
                            Log.error("Cannot process strategy '" + arrayList.get(n5) + "'", (Throwable)exception);
                        }
                    }
                    if (strategySavedListener == null) continue;
                    strategySavedListener.onSave(string2);
                    string2 = null;
                }
                if (int2ObjectOpenHashMap != null) {
                    IntIterator intIterator = int2ObjectOpenHashMap.keySet().iterator();
                    while (intIterator.hasNext()) {
                        int n7 = (Integer)intIterator.next();
                        stringArray2 = (String[])int2ObjectOpenHashMap.get(n7);
                        if (stringArray2 == null) continue;
                        for (n4 = 0; n4 < stringArray2.length; ++n4) {
                            if (stringArray2[n4] == null) continue;
                            new File(stringArray2[n4]).delete();
                            ++n2;
                        }
                    }
                }
                if (n > 0 || n2 > 0) {
                    fileArray = file.listFiles();
                    if (fileArray == null) {
                        return;
                    }
                    int n8 = fileArray == null ? 0 : fileArray.length;
                    Log.info(L.t((String)"Databank '%s/%s' saved - files before sync %d / after sync %d / saved %d / removed %d in %.2f s. Sync triggered by '%s'.", (Object[])new Object[]{sQProject.getName(), databank.getName(), n3, n8, n, n2, (double)(System.currentTimeMillis() - l) / 1000.0, string}));
                    sQProject.printToLog(L.t((String)"Databank '%s/%s' saved - files before sync %d / after sync %d / saved %d / removed %d in %.2f s.", (Object[])new Object[]{sQProject.getName(), databank.getName(), n3, n8, n, n2, (double)(System.currentTimeMillis() - l) / 1000.0}));
                }
            }
            catch (Exception exception) {
                Log.error("Error while syncing databank " + databank.getName() + " into files", (Throwable)exception);
                if (strategySavedListener == null) break block31;
                strategySavedListener.onSave(L.t((String)"Syncing databank %s failed - %s", (Object[])new Object[]{databank.getName(), exception.getMessage()}));
            }
        }
    }

    public static void syncDatabank(Databank databank, boolean bl, String string) {
        block8: {
            SQProject sQProject = null;
            try {
                StrategySavedListener strategySavedListener;
                if (databank.getName().equals("Last generation")) {
                    return;
                }
                int n = databank.size();
                stopped = false;
                StrategySavedListener strategySavedListener2 = strategySavedListener = bl ? new StrategySavedListener(n, false) : null;
                if (strategySavedListener != null) {
                    strategySavedListener.onStart();
                }
                sQProject = ProjectEngine.get(databank.getProject());
                StrategiesSaver.syncDatabankToFiles(sQProject, databank, strategySavedListener, string);
                if (stopped) {
                    Log.info("Saving stopped by user");
                    if (strategySavedListener != null) {
                        strategySavedListener.onFinish(L.t((String)"Saving stopped by user", (Object[])new Object[]{false}), n);
                    }
                } else if (strategySavedListener != null) {
                    strategySavedListener.onFinish(null, n);
                }
            }
            catch (Exception exception) {
                Log.error("Synchronizing strategies failed", (Throwable)exception);
                if (sQProject == null) break block8;
                sQProject.printToLog(L.t((String)"Synchronizing strategies failed - ", (Object[])new Object[0]) + exception.getMessage());
            }
        }
    }

    public static void stop() {
        stopped = true;
    }

    private static class StrategySavedListener {
        private double strategiesProcessed = 0.0;
        private int totalCount;
        private DataToSend data;
        private JSONObject info;

        public StrategySavedListener(int n, boolean bl) {
            this.totalCount = n;
            this.data = new DataToSend("saveAllProgress");
            this.info = new JSONObject();
            this.data.setDataObject(this.info);
            this.info.put("isAppExit", bl);
            this.info.put("totalCount", n);
        }

        public void onStart() {
            this.info.put("progress", 0);
            this.info.put("currentCount", 0);
            SQWebSocketManager.addToDataQueue(this.data, "SQUANT");
        }

        public void onSave(String string) {
            double d = this.strategiesProcessed;
            this.strategiesProcessed = d + 1.0;
            this.info.put("progress", (int)(d / (double)this.totalCount * 100.0));
            this.info.put("currentCount", this.strategiesProcessed);
            this.info.put("totalCount", this.totalCount);
            if (string != null) {
                this.info.put("error", (Object)string);
            } else {
                this.info.remove("error");
            }
            SQWebSocketManager.addToDataQueue(this.data, "SQUANT");
        }

        public void onFinish(String string, int n) {
            this.info.put("progress", 100);
            if (string != null) {
                this.info.put("error", (Object)string);
            } else {
                this.info.remove("error");
            }
            this.info.put("currentCount", n);
            SQWebSocketManager.addToDataQueue(this.data, "SQUANT");
        }
    }
}

