/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.snippets.CustomClassesReg
 *  com.strategyquant.lib.snippets.ICustomClasses
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.tradelist;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.snippets.CustomClassesReg;
import com.strategyquant.lib.snippets.ICustomClasses;
import com.strategyquant.tradinglib.TradelistColumn;
import com.strategyquant.tradinglib.tradelist.TradelistColumnsList;
import com.strategyquant.tradinglib.tradelist.TradelistTableColumnEntry;
import com.strategyquant.tradinglib.tradelist.TradelistTableView;
import java.io.File;
import java.util.HashMap;
import java.util.List;
import java.util.concurrent.locks.StampedLock;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradelistViewsManager
implements ICustomClasses {
    private static final Logger Log = LoggerFactory.getLogger(TradelistViewsManager.class);
    private static final String viewsFolder = MainApp.getDataPath() + "/user/settings/views/tradelists";
    private static final String fileExtension = "vw";
    private static final String defaultViewName = "Default";
    private HashMap<String, TradelistTableView> views = new HashMap();
    private StampedLock lock = new StampedLock();
    private static TradelistViewsManager instance;

    public static synchronized TradelistViewsManager getInstance() {
        if (instance == null) {
            instance = new TradelistViewsManager();
        }
        return instance;
    }

    private TradelistViewsManager() {
        CustomClassesReg.add((ICustomClasses)this);
        this.loadViews();
    }

    private void loadViews() {
        Object object;
        this.views.clear();
        File file = new File(TradelistViewsManager.getViewsFolder());
        if (!file.exists()) {
            file.mkdirs();
        } else {
            object = file.listFiles();
            if (object != null) {
                for (File file2 : object) {
                    try {
                        String string = SQUtils.fileToString((File)file2);
                        this.addView(string, false);
                    }
                    catch (Exception exception) {
                        Log.error("Cannot load tradelist view from file '" + file2.getName() + "'");
                    }
                }
            }
        }
        object = TradelistViewsManager.createDefaultView();
        this.views.put(defaultViewName, (TradelistTableView)object);
    }

    public HashMap<String, TradelistTableView> getViews() {
        return this.views;
    }

    public TradelistTableView getView(String string) throws Exception {
        if (this.views.containsKey(string)) {
            return this.views.get(string);
        }
        throw new Exception("View with name '" + string + "' doesn't exist.");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public TradelistTableView addView(String string, boolean bl) throws Exception {
        long l = this.lock.writeLock();
        try {
            Object object;
            TradelistTableView tradelistTableView = TradelistViewsManager.getTableView(string);
            tradelistTableView.lastChanged = System.currentTimeMillis();
            if (this.views.containsKey(tradelistTableView.name)) {
                throw new Exception("Tradelist view with name '" + tradelistTableView.name + "' already exists.");
            }
            this.views.put(tradelistTableView.name, tradelistTableView);
            if (bl) {
                object = new File(TradelistViewsManager.getViewFilePath(tradelistTableView.name));
                SQUtils.stringToFile((File)object, (String)string);
            }
            object = tradelistTableView;
            return object;
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public TradelistTableView updateView(String string) throws Exception {
        long l = this.lock.writeLock();
        try {
            Object object;
            boolean bl;
            TradelistTableView tradelistTableView = TradelistViewsManager.getTableView(string);
            tradelistTableView.lastChanged = System.currentTimeMillis();
            Element element = XMLUtil.stringToElement((String)string);
            String string2 = element.getAttributeValue("originalName");
            String string3 = element.getAttributeValue("name");
            boolean bl2 = bl = string2 != null && !string2.equals(string3);
            if (bl) {
                this.views.remove(string2);
                object = new File(TradelistViewsManager.getViewFilePath(string2));
                ((File)object).delete();
            }
            if (!bl && !this.views.containsKey(tradelistTableView.name)) {
                throw new Exception("Tradelist view with name '" + tradelistTableView.name + "' doesn't exist.");
            }
            this.views.put(tradelistTableView.name, tradelistTableView);
            object = new File(TradelistViewsManager.getViewFilePath(tradelistTableView.name));
            SQUtils.stringToFile((File)object, (String)string);
            object = tradelistTableView;
            return object;
        }
        finally {
            this.lock.unlock(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void removeView(String string) throws Exception {
        block5: {
            long l = this.lock.writeLock();
            try {
                if (this.views.containsKey(string)) {
                    this.views.remove(string);
                    File file = new File(TradelistViewsManager.getViewFilePath(string));
                    if (!file.delete()) {
                        throw new Exception("Cannot delete file '" + file.getName() + "'");
                    }
                    break block5;
                }
                throw new Exception("Tradelist view with name '" + string + "' doesn't exist.");
            }
            finally {
                this.lock.unlock(l);
            }
        }
    }

    private static TradelistTableView getTableView(String string) throws Exception {
        TradelistTableView tradelistTableView = new TradelistTableView();
        Element element = XMLUtil.stringToElement((String)SQUtils.removeUTF8BOM((String)string));
        tradelistTableView.setFromXML(element);
        return tradelistTableView;
    }

    private static String getViewFilePath(String string) {
        return TradelistViewsManager.getViewsFolder() + "/" + string + "." + fileExtension;
    }

    protected static String getViewsFolder() {
        return viewsFolder;
    }

    public static TradelistTableView createDefaultView() {
        TradelistTableView tradelistTableView = new TradelistTableView();
        tradelistTableView.name = defaultViewName;
        String[] stringArray = new String[]{"Ticket", "Symbol", "Type", "OpenTime", "OpenPrice", "Size", "CloseTime", "ClosePrice", "ProfitLoss", "Balance", "SampleType", "CloseType", "MAE", "MFE", "TimeInTrade", "Comment"};
        List list = TradelistColumnsList.get().cloneAvailableClasses();
        block0: for (String string : stringArray) {
            for (TradelistColumn tradelistColumn : list) {
                if (!tradelistColumn.getClass().getSimpleName().equals(string)) continue;
                tradelistTableView.columns.add(new TradelistTableColumnEntry(tradelistColumn));
                continue block0;
            }
        }
        return tradelistTableView;
    }

    /*
     * Exception decompiling
     */
    public TradelistTableView getSelectedTradelistView() {
        /*
         * This method has failed to decompile.  When submitting a bug report, please provide this stack trace, and (if you hold appropriate legal rights) the relevant class file.
         * 
         * org.benf.cfr.reader.util.ConfusedCFRException: Tried to end blocks [5[CATCHBLOCK]], but top level block is 3[TRYBLOCK]
         *     at org.benf.cfr.reader.bytecode.analysis.opgraph.Op04StructuredStatement.processEndingBlocks(Op04StructuredStatement.java:435)
         *     at org.benf.cfr.reader.bytecode.analysis.opgraph.Op04StructuredStatement.buildNestedBlocks(Op04StructuredStatement.java:484)
         *     at org.benf.cfr.reader.bytecode.analysis.opgraph.Op03SimpleStatement.createInitialStructuredBlock(Op03SimpleStatement.java:736)
         *     at org.benf.cfr.reader.bytecode.CodeAnalyser.getAnalysisInner(CodeAnalyser.java:850)
         *     at org.benf.cfr.reader.bytecode.CodeAnalyser.getAnalysisOrWrapFail(CodeAnalyser.java:278)
         *     at org.benf.cfr.reader.bytecode.CodeAnalyser.getAnalysis(CodeAnalyser.java:201)
         *     at org.benf.cfr.reader.entities.attributes.AttributeCode.analyse(AttributeCode.java:94)
         *     at org.benf.cfr.reader.entities.Method.analyse(Method.java:531)
         *     at org.benf.cfr.reader.entities.ClassFile.analyseMid(ClassFile.java:1055)
         *     at org.benf.cfr.reader.entities.ClassFile.analyseTop(ClassFile.java:942)
         *     at org.benf.cfr.reader.Driver.doJarVersionTypes(Driver.java:257)
         *     at org.benf.cfr.reader.Driver.doJar(Driver.java:139)
         *     at org.benf.cfr.reader.CfrDriverImpl.analyse(CfrDriverImpl.java:76)
         *     at org.benf.cfr.reader.Main.main(Main.java:54)
         */
        throw new IllegalStateException("Decompilation failed");
    }

    public void reload() throws Exception {
        this.loadViews();
    }
}

