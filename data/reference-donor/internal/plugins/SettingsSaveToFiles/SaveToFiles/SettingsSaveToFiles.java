/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerator
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerators
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.task.settings.ISettingTabPlugin
 *  com.strategyquant.tradinglib.task.settings.TaskSettingsData
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Settings.impl.SaveToFiles;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.sourcecode.SourceCodeGenerator;
import com.strategyquant.lib.sourcecode.SourceCodeGenerators;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.task.settings.ISettingTabPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.File;
import java.io.Serializable;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;

@Author(name="Tomas Brynda")
@Name(name="Settings SaveToFiles plugin")
@Category(name="Settings")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SettingsSaveToFiles
implements ISettingTabPlugin {
    private static final String tabTitle = "Save to files";

    public String getProduct() {
        return "SQUANT";
    }

    public int getPreferredPosition() {
        return 50;
    }

    public void initPlugin() throws Exception {
    }

    public void readSettings(String projectName, ISQTask task, Element elSettings, TaskSettingsData data) {
        Element elSaveToFiles = XMLUtil.tryAddElement((Element)elSettings, (String)this.getSettingName());
        try {
            SourceCodeGenerator sourceCodeGenerator;
            data.addParam("OverwriteFiles", (Serializable)Boolean.valueOf(XMLUtil.getBoolean((Element)elSaveToFiles, (String)"OverwriteFiles", (boolean)false)));
            String destDirectorySqx = XMLUtil.getChildElem((Element)elSaveToFiles, (String)"DestDirectorySqx").getText();
            boolean saveInSqxFormat = Boolean.parseBoolean(XMLUtil.getChildElem((Element)elSaveToFiles, (String)"SaveInSqxFormat").getText());
            if (saveInSqxFormat) {
                if (destDirectorySqx.isEmpty()) {
                    throw new Exception(L.t((String)"SQX target directory is not set.", (Object[])new Object[0]));
                }
                if (!new File(destDirectorySqx).exists()) {
                    throw new Exception(L.t((String)"SQX target directory doesn't exist.", (Object[])new Object[0]));
                }
            }
            data.addParam("SaveInSqxFormat", (Serializable)Boolean.valueOf(saveInSqxFormat));
            data.addParam("DestDirectorySqx", (Serializable)((Object)destDirectorySqx));
            String destDirectoryStr = XMLUtil.getChildElem((Element)elSaveToFiles, (String)"DestDirectoryStr").getText();
            boolean saveInStrFormat = Boolean.parseBoolean(XMLUtil.getChildElem((Element)elSaveToFiles, (String)"SaveInStrFormat").getText());
            if (saveInStrFormat) {
                if (destDirectoryStr.isEmpty()) {
                    throw new Exception(L.t((String)"STR (SQ3) target directory is not set.", (Object[])new Object[0]));
                }
                if (!new File(destDirectoryStr).exists()) {
                    throw new Exception(L.t((String)"STR (SQ3) target directory doesn't exist.", (Object[])new Object[0]));
                }
            }
            data.addParam("SaveInStrFormat", (Serializable)Boolean.valueOf(saveInStrFormat));
            data.addParam("DestDirectoryStr", (Serializable)((Object)destDirectoryStr));
            String destDirectoryDatabank = XMLUtil.getChildElem((Element)elSaveToFiles, (String)"DestDirectoryDatabank").getText();
            boolean exportDatabank = Boolean.parseBoolean(XMLUtil.getChildElem((Element)elSaveToFiles, (String)"ExportDatabank").getText());
            if (exportDatabank) {
                if (destDirectoryDatabank.isEmpty()) {
                    throw new Exception(L.t((String)"Export databank contents target directory is not set.", (Object[])new Object[0]));
                }
                if (!new File(destDirectoryDatabank).exists()) {
                    throw new Exception(L.t((String)"Export databank contents target directory doesn't exist.", (Object[])new Object[0]));
                }
            }
            data.addParam("ExportDatabank", (Serializable)Boolean.valueOf(exportDatabank));
            data.addParam("DestDirectoryDatabank", (Serializable)((Object)destDirectoryDatabank));
            String destDirectoryTrades = XMLUtil.getChildElem((Element)elSaveToFiles, (String)"DestDirectoryTrades").getText();
            boolean exportTrades = Boolean.parseBoolean(XMLUtil.getChildElem((Element)elSaveToFiles, (String)"ExportTrades").getText());
            if (exportTrades) {
                if (destDirectoryTrades.isEmpty()) {
                    throw new Exception(L.t((String)"Export trades target directory is not set.", (Object[])new Object[0]));
                }
                if (!new File(destDirectoryTrades).exists()) {
                    throw new Exception(L.t((String)"Export trades target directory doesn't exist.", (Object[])new Object[0]));
                }
            }
            data.addParam("ExportTrades", (Serializable)Boolean.valueOf(exportTrades));
            data.addParam("DestDirectoryTrades", (Serializable)((Object)destDirectoryTrades));
            String destDirectoryHtml = XMLUtil.getChildElem((Element)elSaveToFiles, (String)"DestDirectoryHtml").getText();
            boolean saveInHtmlFormat = Boolean.parseBoolean(XMLUtil.getChildElem((Element)elSaveToFiles, (String)"SaveInHtmlFormat").getText());
            if (saveInHtmlFormat) {
                if (destDirectoryHtml.isEmpty()) {
                    throw new Exception(L.t((String)"Html target directory is not set.", (Object[])new Object[0]));
                }
                if (!new File(destDirectoryHtml).exists()) {
                    throw new Exception(L.t((String)"Html target directory doesn't exist.", (Object[])new Object[0]));
                }
            }
            data.addParam("SaveInHtmlFormat", (Serializable)Boolean.valueOf(saveInHtmlFormat));
            data.addParam("DestDirectoryHtml", (Serializable)((Object)destDirectoryHtml));
            String destDirectoryPdf = XMLUtil.getChildElem((Element)elSaveToFiles, (String)"DestDirectoryPdf").getText();
            boolean saveInPdfFormat = Boolean.parseBoolean(XMLUtil.getChildElem((Element)elSaveToFiles, (String)"SaveInPdfFormat").getText());
            if (saveInPdfFormat) {
                if (destDirectoryPdf.isEmpty()) {
                    throw new Exception(L.t((String)"PDF target directory is not set.", (Object[])new Object[0]));
                }
                if (!new File(destDirectoryPdf).exists()) {
                    throw new Exception(L.t((String)"PDF target directory doesn't exist.", (Object[])new Object[0]));
                }
            }
            data.addParam("SaveInPdfFormat", (Serializable)Boolean.valueOf(saveInPdfFormat));
            data.addParam("DestDirectoryPdf", (Serializable)((Object)destDirectoryPdf));
            String destDirectorySC = XMLUtil.getChildElem((Element)elSaveToFiles, (String)"DestDirectorySC").getText();
            Element elSourceCode = XMLUtil.getChildElem((Element)elSaveToFiles, (String)"SaveSourceCode");
            boolean saveSourceCode = Boolean.parseBoolean(elSourceCode.getText());
            if (saveSourceCode) {
                if (destDirectorySC.isEmpty()) {
                    throw new Exception(L.t((String)"Source Code target directory is not set.", (Object[])new Object[0]));
                }
                if (!new File(destDirectorySC).exists()) {
                    throw new Exception(L.t((String)"Source Code target directory doesn't exist.", (Object[])new Object[0]));
                }
            }
            data.addParam("SaveSourceCode", (Serializable)Boolean.valueOf(saveSourceCode));
            data.addParam("DestDirectorySC", (Serializable)((Object)destDirectorySC));
            String type = SourceCodeGenerators.getInstance().canonicalize(XMLUtil.getAttr((Element)elSourceCode, (String)"type"));
            if (!type.equals("Strategy XML") && (sourceCodeGenerator = SourceCodeGenerators.getInstance().getGeneratorFromName(type)) == null) {
                throw new Exception(L.t((String)"Invalid source code generator", (Object[])new Object[0]));
            }
            data.addParam("SourceCodeType", (Serializable)((Object)type));
            String format = XMLUtil.getAttr((Element)elSourceCode, (String)"format", null);
            if (type.equals(SourceCodeGenerator.EasyLanguage)) {
                data.addParam("SourceCodeFormat", (Serializable)((Object)format));
            } else {
                data.addParam("SourceCodeFormat", null);
            }
            Databank sourceDatabank = ProjectConfigHelper.getInputDatabank((String)projectName, (Element)elSaveToFiles.getParentElement());
            if (sourceDatabank == null) {
                throw new Exception(L.t((String)"Source databank not found", (Object[])new Object[0]));
            }
            data.addParam("DatabankSource", (Serializable)sourceDatabank);
            data.addParam("MNActive", (Serializable)Boolean.valueOf(XMLUtil.getBoolean((Element)elSaveToFiles, (String)"MNActive", (boolean)false)));
            data.addParam("MNValue", (Serializable)Integer.valueOf(XMLUtil.getInt((Element)elSaveToFiles, (String)"MNValue", (int)12345)));
            data.addParam("Data", (Serializable)((Object)XMLUtil.getNodeValue((Element)elSaveToFiles, (String)"Data", (String)"all")));
            data.addParam("Format", (Serializable)((Object)XMLUtil.getNodeValue((Element)elSaveToFiles, (String)"Format", (String)"xlsx")));
            data.addParam("UseComma", (Serializable)Boolean.valueOf(XMLUtil.getBoolean((Element)elSaveToFiles, (String)"UseComma", (boolean)false)));
            data.addParam("SetNoteActive", (Serializable)Boolean.valueOf(XMLUtil.getBoolean((Element)elSaveToFiles, (String)"SetNoteActive", (boolean)false)));
            data.addParam("SetNoteType", (Serializable)((Object)XMLUtil.getNodeValue((Element)elSaveToFiles, (String)"SetNoteType", (String)"timeframe")));
            data.addParam("SetNoteCustom", (Serializable)((Object)XMLUtil.getNodeValue((Element)elSaveToFiles, (String)"SetNoteCustom", (String)"")));
        }
        catch (Exception e) {
            data.addError(this.getSettingName(), null, "Cannot load SaveToFiles settings. " + e.getMessage());
        }
    }

    public void getStrategyConfigSettings(Element elSettings, JSONArray settingsArray) throws Exception {
    }

    public String getSettingName() {
        return "SaveToFiles";
    }

    public String getName() {
        return L.tsq((String)tabTitle);
    }

    public JSONObject getInitializationData() throws Exception {
        return null;
    }
}

