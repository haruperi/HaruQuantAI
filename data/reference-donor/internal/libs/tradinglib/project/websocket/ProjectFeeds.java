/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.concurrent.locks.StampedLock;

public class ProjectFeeds {
    private static HashMap<String, ArrayList<String>> feedMap = new HashMap();
    private static StampedLock lock = new StampedLock();
    private static String activeProductCode = null;

    public static void setActiveProduct(String string) {
        long l = lock.writeLock();
        try {
            activeProductCode = string;
        }
        finally {
            lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void subscribe(String string, String string2) {
        long l = lock.writeLock();
        try {
            if (feedMap.containsKey(string)) {
                ArrayList<String> arrayList = feedMap.get(string);
                if (!arrayList.contains(string2)) {
                    arrayList.add(string2);
                }
            } else {
                ArrayList<String> arrayList = new ArrayList<String>();
                arrayList.add(string2);
                feedMap.put(string, arrayList);
            }
        }
        finally {
            lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void unsubscribe(String string, String string2) {
        long l = lock.writeLock();
        try {
            if (feedMap.containsKey(string)) {
                ArrayList<String> arrayList = feedMap.get(string);
                arrayList.remove(string2);
            }
        }
        finally {
            lock.unlock(l);
        }
    }

    public static void unsubscribeAll(String string) {
        long l = lock.writeLock();
        try {
            if (feedMap.containsKey(string)) {
                feedMap.get(string).clear();
            }
        }
        finally {
            lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static ArrayList<String> getChannels(String string) {
        long l = lock.readLock();
        try {
            ArrayList<String> arrayList = feedMap.get(string);
            return arrayList;
        }
        finally {
            lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static boolean isSubscribed(String string, String string2) {
        long l = lock.readLock();
        try {
            if (!ProjectFeeds.checkProduct(string)) {
                boolean bl = false;
                return bl;
            }
            ArrayList<String> arrayList = feedMap.get(string);
            if (arrayList == null) {
                boolean bl = false;
                return bl;
            }
            boolean bl = arrayList.contains(string2);
            return bl;
        }
        finally {
            lock.unlock(l);
        }
    }

    private static boolean checkProduct(String string) {
        if (activeProductCode == null) {
            return true;
        }
        String string2 = SQWebSocketManager.getProjectName(activeProductCode);
        if (string2 != null && string2.equals(string)) {
            return true;
        }
        return activeProductCode.equals("TASKMANAGER") && !ProjectEngine.isDefaulProject(string);
    }
}

