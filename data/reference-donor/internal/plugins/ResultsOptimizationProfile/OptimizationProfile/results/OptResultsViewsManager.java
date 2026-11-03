/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.databank.DatabankTableColumnEntry
 *  com.strategyquant.tradinglib.databank.DatabankTableView
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.OptimizationProfile.results;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import java.io.File;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptResultsViewsManager {
    private static final Logger Log = LoggerFactory.getLogger(OptResultsViewsManager.class);
    private HashMap<String, DatabankTableView> views = new HashMap();
    private final String viewsFolder;
    private final String fileExtension = "vw";
    public static final String SettingsKey = "optResultsView";

    public OptResultsViewsManager(String viewsFolder) {
        this.viewsFolder = viewsFolder;
        this.loadViews();
    }

    public void loadViews() {
        File folder = new File(this.viewsFolder);
        if (!folder.exists()) {
            folder.mkdirs();
        } else {
            File[] viewFiles = folder.listFiles();
            if (viewFiles != null) {
                for (File viewFile : viewFiles) {
                    try {
                        String viewConfig = SQUtils.fileToString((File)viewFile);
                        this._addView(viewConfig, false);
                    }
                    catch (Exception e) {
                        Log.error("Cannot load View from file '" + viewFile.getName() + "'");
                    }
                }
            }
        }
        DatabankTableView defaultView = this.createDefaultView();
        this.views.put("Default", defaultView);
    }

    public HashMap<String, DatabankTableView> getViews() {
        return this.views;
    }

    public DatabankTableView getView(String name) throws Exception {
        if (this.views.containsKey(name)) {
            return this.views.get(name);
        }
        throw new Exception(L.t((String)"View with name '%s' doesn't exist.", (Object[])new Object[]{name}));
    }

    public void addView(String xmlConfig) throws Exception {
        this._addView(xmlConfig, true);
    }

    private void _addView(String xmlConfig, boolean createFile) throws Exception {
        DatabankTableView view = this.getTableView(xmlConfig);
        if (this.views.containsKey(view.name)) {
            throw new Exception(L.t((String)"View with name '%s' already exists.", (Object[])new Object[]{view.name}));
        }
        this.views.put(view.name, view);
        if (createFile) {
            File newFile = new File(this.getViewFilePath(view.name));
            SQUtils.stringToFile((File)newFile, (String)xmlConfig);
        }
    }

    public DatabankTableView updateView(String xmlConfig) throws Exception {
        File viewFile;
        boolean renamed;
        DatabankTableView view = this.getTableView(xmlConfig);
        Element elView = XMLUtil.stringToElement((String)xmlConfig);
        String originalName = elView.getAttributeValue("originalName");
        String newName = elView.getAttributeValue("name");
        boolean bl = renamed = originalName != null && !originalName.equals(newName);
        if (renamed) {
            this.views.remove(originalName);
            viewFile = new File(this.getViewFilePath(originalName));
            viewFile.delete();
        }
        if (!renamed && !this.views.containsKey(view.name)) {
            throw new Exception(L.t((String)"Databank view with name '%s' doesn't exist.", (Object[])new Object[]{view.name}));
        }
        this.views.put(view.name, view);
        viewFile = new File(this.getViewFilePath(view.name));
        SQUtils.stringToFile((File)viewFile, (String)xmlConfig);
        return view;
    }

    public void removeView(String name) throws Exception {
        if (this.views.containsKey(name)) {
            this.views.remove(name);
            File viewFile = new File(this.getViewFilePath(name));
            if (!viewFile.delete()) {
                throw new Exception(L.t((String)"Cannot delete file '%s'", (Object[])new Object[]{viewFile.getName()}));
            }
        } else {
            throw new Exception(L.t((String)"View with name '%s' doesn't exist.", (Object[])new Object[]{name}));
        }
    }

    public DatabankTableView createDefaultView() {
        DatabankTableView view = new DatabankTableView();
        view.name = "Default - Main data";
        String[] columnClassNames = new String[]{"Fitness", "NetProfit", "NumberOfTrades", "PctWins", "ProfitFactor", "SharpeRatio", "RExpectancy", "AnnualPctReturn", "Stability", "Symmetry", "Drawdown", "WinLossRatio", "ReturnDDRatio"};
        List columns = DatabankColumns.get().cloneAvailableClasses();
        block0: for (String className : columnClassNames) {
            for (DatabankColumn column : columns) {
                if (!column.getClass().getSimpleName().equals(className)) continue;
                view.columns.add(new DatabankTableColumnEntry(column, "portfolio", 0, 10, 127));
                continue block0;
            }
        }
        return view;
    }

    private DatabankTableView getTableView(String xmlConfig) throws Exception {
        DatabankTableView view = new DatabankTableView();
        Element viewElem = XMLUtil.stringToElement((String)SQUtils.removeUTF8BOM((String)xmlConfig));
        view.setFromXML(viewElem);
        return view;
    }

    private String getViewFilePath(String viewName) {
        return this.viewsFolder + "/" + viewName + "." + "vw";
    }

    public DatabankTableView getSelectedView() {
        String viewName = MainApp.settings().get(SettingsKey);
        if (viewName != null) {
            try {
                return this.getView(viewName);
            }
            catch (Exception e) {
                Log.error("Cannot load selected Optimization Results view. Using default view...");
            }
        }
        try {
            return this.getView("Default");
        }
        catch (Exception e) {
            Log.error("Cannot load default Optimization Results view");
            return null;
        }
    }
}

