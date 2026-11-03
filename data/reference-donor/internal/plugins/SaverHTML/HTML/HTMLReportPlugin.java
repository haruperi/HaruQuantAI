/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.ReportGenerator
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StatsTypeCombination
 *  com.strategyquant.tradinglib.results.file.ISaverPlugin
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Saver.impl.HTML;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ReportGenerator;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.results.file.ISaverPlugin;
import java.io.File;
import java.util.Map;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Mark Fric")
@Name(name="HTML report")
@Category(name="File Saver")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class HTMLReportPlugin
extends ReportGenerator
implements ISaverPlugin,
IProgram {
    public static final Logger Log = LoggerFactory.getLogger(HTMLReportPlugin.class);
    public static final String[] extensions = new String[]{"html"};

    public HTMLReportPlugin() {
        super("html");
        try {
            this.setName(L.tsq((String)"SQ Default"));
            this.setHtmlTemplateName("sqdefault_template.htm");
            String filePath = MainApp.getDataPath() + "internal/plugins/SaverHTML/templates/" + this.htmlTemplateName;
            this.templateOrig = SQUtils.fileToString((File)new File(filePath));
        }
        catch (Exception e) {
            Log.error("Overview template couldn't be loaded. Exc. ", (Throwable)e);
        }
    }

    public String getProduct() {
        return "any";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
        Program.register((String)"SaverHTML", (IProgram)this);
    }

    public String[] getFileExtensions() {
        return extensions;
    }

    public Object call(String methodName, Object ... parameters) throws Exception {
        if (methodName.equals("save")) {
            this.save((ResultsGroup)parameters[0], (String)parameters[1], (Map)parameters[2]);
        } else if (methodName.equals("resolveCharts")) {
            this.resolveCharts((JSONObject)parameters[0]);
        }
        return null;
    }

    public void save(ResultsGroup rg, String fileName, Map<String, String[]> parameterMap) throws Exception {
        try {
            this.file = new File(fileName);
            if (!this.file.exists() && this.file.getParentFile() != null) {
                this.file.getParentFile().mkdirs();
            }
            String html = this.drawValues(rg, "Portfolio", new StatsTypeCombination(0, 10, 127));
            Log.info("---- SAVING TO FILE {}", (Object)this.file.getAbsolutePath());
            SQUtils.stringToFile((File)this.file, (String)html);
        }
        catch (Exception ex) {
            Log.error("Failed to save report as HTML '" + rg.getName() + "'. Exc: ", (Throwable)ex);
            throw new Exception("\"Failed to save report as HTML '" + rg.getName() + "'. Reason: " + ex.getMessage());
        }
    }

    public ISaverPlugin clone() {
        return new HTMLReportPlugin();
    }
}

