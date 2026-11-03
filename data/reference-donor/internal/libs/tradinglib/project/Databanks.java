/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.databank.IProgressListener;
import com.strategyquant.tradinglib.project.DatabankPositionComparator;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Databanks
extends LinkedHashMap<String, Databank> {
    public static final Logger Log = LoggerFactory.getLogger(Databanks.class);
    private String databanksFolder = null;
    private String projectName;
    private DatabankPositionComparator positionComparator = new DatabankPositionComparator();

    public Databanks(String string) {
        this.projectName = string;
        this.databanksFolder = SQPaths.projectsDirPath + "/" + this.projectName + "/databanks";
    }

    public Databank add(String string) {
        if (this.containsKey(string)) {
            return (Databank)this.get(string);
        }
        Databank databank = new Databank(this.projectName, string, this.databanksFolder);
        this.put(string, databank);
        return databank;
    }

    public void add(Databank databank) throws Exception {
        String string = databank.getName();
        if (this.containsKey(string)) {
            throw new Exception(L.t((String)"Databank with name '%s' already exists.", (Object[])new Object[]{string}));
        }
        this.put(string, databank);
    }

    public void remove(Databank databank) throws Exception {
        String string = databank.getName();
        if (this.containsKey(string)) {
            throw new Exception(L.t((String)"Databank with name '%s' does not exist.", (Object[])new Object[]{string}));
        }
        databank.destroyTimers();
        super.remove(string);
    }

    public ArrayList<Databank> list() {
        return new ArrayList<Databank>(this.values());
    }

    public boolean loadFromConfig(Element element) throws Exception {
        Element element2 = XMLUtil.getChildElem((Element)element, (String)"Databanks");
        List list = element2.getChildren("Databank");
        boolean bl = false;
        for (int i = 0; i < list.size(); ++i) {
            Element element3 = (Element)list.get(i);
            String string = element3.getAttributeValue("name");
            String string2 = element3.getAttributeValue("view");
            String string3 = element3.getAttributeValue("syncType");
            String string4 = element3.getAttributeValue("position");
            int n = this.getDatabankPosition(i);
            try {
                n = Integer.parseInt(string4);
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (this.containsKey(string)) continue;
            Databank databank = new Databank(this.projectName, string, this.databanksFolder);
            databank.setSyncType(string3 != null ? string3 : "Auto-sync never");
            databank.setPosition(n);
            if (!databank.setViewByName(string2)) {
                element3.setAttribute("view", "Default - Main data");
                bl = true;
            }
            this.add(databank);
        }
        if (this.size() == 0) {
            this.add("Results");
            bl = true;
        }
        return bl;
    }

    private synchronized void setProgressInfo(String string) {
        double d = 0.0;
        int n = this.size();
        if (this.loaded() || n == 0) {
            d = 100.0;
        } else {
            for (Databank object2 : this.list()) {
                d += object2.getPercentLoaded();
            }
            d /= (double)n;
        }
        int n2 = d == 100.0 ? 0 : 100;
        String string2 = d == 100.0 ? "" : "Loading strategies...";
        try {
            SQProject exception = ProjectEngine.get(this.projectName);
            exception.getTrackingInfo().infiniteProgress = false;
            exception.getTrackingInfo().progressPercent = d;
            exception.getTrackingInfo().info = string2;
            exception.progressEngine.setRunningStatus(n2);
            if (string != null) {
                exception.progressEngine.printToLog(string);
            }
        }
        catch (Exception exception) {
            Log.error("Sending loading progress of project '" + this.projectName + "' failed. ", (Throwable)exception);
        }
    }

    public void loadStrategies() throws Exception {
        for (final Databank databank : this.list()) {
            final long l = System.currentTimeMillis();
            databank.loadStrategies(new IProgressListener(){
                final /* synthetic */ Databanks this$0;
                {
                    this.this$0 = databanks;
                }

                @Override
                public void onError(double d, String string) {
                    String string2 = "Loading strategies to databank '" + databank.getProject() + "/" + databank.getName() + "' failed - " + string;
                    Log.error(string2);
                    this.this$0.setProgressInfo(string2);
                }

                @Override
                public void onDone() {
                    if (!databank.getRecords().isEmpty()) {
                        String string = "Databank '" + databank.getProject() + "/" + databank.getName() + "' loaded - " + databank.getRecords().size() + " strategies in " + (System.currentTimeMillis() - l) + "ms";
                        Log.info(string);
                        this.this$0.setProgressInfo(string);
                    }
                }

                @Override
                public void onProgress(double d) {
                    this.this$0.setProgressInfo(null);
                }
            });
        }
    }

    public boolean loaded() {
        for (Databank databank : this.list()) {
            if (!databank.isLoading()) continue;
            return false;
        }
        return true;
    }

    public void clear(boolean bl, String string) {
        for (Databank databank : this.list()) {
            try {
                databank.clearRecords(true, bl, string);
                databank.destroyTimers();
            }
            catch (Exception exception) {
                Log.error("Error clearing databank", (Throwable)exception);
            }
        }
    }

    public String getProjectName() {
        return this.projectName;
    }

    public static boolean isDefault(String string) {
        switch (string) {
            case "Results": 
            case "Last generation": 
            case "Initial population": 
            case "Strategies to improve": 
            case "Strategies to optimize": 
            case "Existing portfolio": 
            case "Simple strategies": {
                return true;
            }
        }
        return false;
    }

    public void setProjectName(String string) {
        this.projectName = string;
        this.databanksFolder = SQPaths.projectsDirPath + "/" + string + "/databanks";
        for (String string2 : this.keySet()) {
            ((Databank)this.get(string2)).setProjectName(string);
        }
    }

    public void move(String string, boolean bl) throws Exception {
        ArrayList<String> arrayList = new ArrayList<String>();
        int n = this.findAndListCustomDatabanks(string, arrayList);
        int n2 = n + (bl ? -1 : 1);
        if (!(n == 0 && bl || n == arrayList.size() - 1 && !bl)) {
            arrayList.remove(n);
            arrayList.add(n2, string);
        }
        for (int i = 0; i < arrayList.size(); ++i) {
            Databank databank = (Databank)this.get(arrayList.get(i));
            databank.setPosition(this.getDatabankPosition(i));
        }
        this.list().sort(this.positionComparator);
    }

    public void moveToPosition(String string, int n) throws Exception {
        ArrayList<String> arrayList = new ArrayList<String>();
        int n2 = this.findAndListCustomDatabanks(string, arrayList);
        int n3 = n - 1;
        if (n < 1 || n > arrayList.size()) {
            throw new Exception(L.t((String)"Incorrect position chosen (%d). Must be in range 1-%d", (Object[])new Object[]{n, arrayList.size()}));
        }
        arrayList.remove(n2);
        arrayList.add(n3, string);
        for (int i = 0; i < arrayList.size(); ++i) {
            Databank databank = (Databank)this.get(arrayList.get(i));
            databank.setPosition(this.getDatabankPosition(i));
        }
        this.list().sort(this.positionComparator);
    }

    private int findAndListCustomDatabanks(String string, ArrayList<String> arrayList) throws Exception {
        if (!this.containsKey(string)) {
            throw new Exception(L.t((String)"Databank '%s' doesn't exist", (Object[])new Object[]{string}));
        }
        ArrayList<Databank> arrayList2 = this.list();
        arrayList2.sort(this.positionComparator);
        int n = 0;
        int n2 = 0;
        for (int i = 0; i < arrayList2.size(); ++i) {
            Databank databank = arrayList2.get(i);
            if (databank.isDefault()) {
                databank.setPosition(n2++);
                continue;
            }
            arrayList.add(databank.getName());
            if (!databank.getName().equals(string)) continue;
            n = arrayList.size() - 1;
        }
        return n;
    }

    public void rename(String string, String string2) throws Exception {
        Databank databank = (Databank)this.remove(string);
        if (databank == null) {
            throw new Exception(L.t((String)"Databank '%s' doesn't exist", (Object[])new Object[]{string}));
        }
        databank.rename(string2);
        this.put(string2, databank);
    }

    public void updatePositions() {
        ArrayList<Databank> arrayList = this.list();
        arrayList.sort(this.positionComparator);
        for (int i = 0; i < arrayList.size(); ++i) {
            Databank databank = arrayList.get(i);
            if (databank.isDefault()) {
                databank.setPosition(i);
                continue;
            }
            databank.setPosition(this.getDatabankPosition(i));
        }
    }

    private int getDatabankPosition(int n) {
        return 100 * (n + 1);
    }
}

