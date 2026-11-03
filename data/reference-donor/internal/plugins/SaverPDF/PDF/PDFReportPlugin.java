/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.snippets.compile.SQStructure
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
 *  org.zefer.pd4ml.PD4ML
 */
package com.strategyquant.plugin.Saver.impl.PDF;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.snippets.compile.SQStructure;
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
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.UUID;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.zefer.pd4ml.PD4ML;

@Author(name="Mark Fric")
@Name(name="PDF report")
@Category(name="File Saver")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class PDFReportPlugin
extends ReportGenerator
implements ISaverPlugin,
IProgram {
    public static final Logger Log = LoggerFactory.getLogger(PDFReportPlugin.class);
    public static final String[] extensions = new String[]{"pdf"};

    public PDFReportPlugin() {
        super("pdf");
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
        Program.register((String)"SaverPDF", (IProgram)this);
    }

    public String[] getFileExtensions() {
        return extensions;
    }

    public Object call(String methodName, Object ... parameters) throws Exception {
        if (methodName.equals("save")) {
            this.save((ResultsGroup)parameters[0], (String)parameters[1], (Map)parameters[2]);
        } else if (methodName.equals("resolveCharts")) {
            this.resolveCharts((JSONObject)parameters[0]);
        } else if (methodName.equals("htmlToPdf")) {
            this.htmlToPdf((String)parameters[0], (String)parameters[1]);
        }
        return null;
    }

    public void save(ResultsGroup rg, String fileName, Map<String, String[]> parameterMap) throws Exception {
        try {
            PD4ML pd4ml = new PD4ML();
            String tempDir = SQStructure.TEMP_DIR_PATH + "pdf_" + UUID.randomUUID() + "/";
            String tempPath = tempDir + SQUtils.stripExtension((String)new File(fileName).getName()) + ".html";
            this.file = new File(tempPath);
            if (!this.file.exists() && this.file.getParentFile() != null) {
                this.file.getParentFile().mkdirs();
            }
            String html = this.drawValues(rg, "Portfolio", new StatsTypeCombination(0, 10, 127));
            SQUtils.stringToFile((String)tempPath, (String)html);
            this.file = new File(fileName);
            if (!this.file.exists() && this.file.getParentFile() != null) {
                this.file.getParentFile().mkdirs();
            }
            InputStreamReader reader = new InputStreamReader((InputStream)new FileInputStream(tempPath), StandardCharsets.UTF_8);
            FileOutputStream fop = new FileOutputStream(this.file);
            URL base = new URL("file:" + tempDir);
            pd4ml.adjustHtmlWidth();
            pd4ml.enableImgSplit(false);
            pd4ml.render(reader, (OutputStream)fop, base);
            Log.info("Saved to PDF at {}, temp: {}", (Object)fileName, (Object)tempDir);
            SQUtils.deleteDirectory((String)tempDir);
        }
        catch (Exception ex) {
            Log.error("Failed to save report as PDF '" + rg.getName() + "'. Exc: ", (Throwable)ex);
            throw new Exception("\"Failed to save report as PDF '" + rg.getName() + "'. Reason: " + ex.getMessage());
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void htmlToPdf(String htmlPath, String pdfPath) throws Exception {
        try {
            PD4ML pd4ml = new PD4ML();
            File htmlFile = new File(htmlPath);
            if (!htmlFile.isFile()) {
                throw new Exception("HTML file not found: " + htmlPath);
            }
            File pdfFile = new File(pdfPath);
            if (!pdfFile.exists() && pdfFile.getParentFile() != null) {
                pdfFile.getParentFile().mkdirs();
            }
            InputStreamReader reader = new InputStreamReader((InputStream)new FileInputStream(htmlFile), StandardCharsets.UTF_8);
            FileOutputStream fop = new FileOutputStream(pdfFile);
            try {
                URL base = htmlFile.getAbsoluteFile().getParentFile().toURI().toURL();
                pd4ml.adjustHtmlWidth();
                pd4ml.enableImgSplit(false);
                pd4ml.render(reader, (OutputStream)fop, base);
            }
            finally {
                reader.close();
                fop.close();
            }
            Log.info("Saved HTML '{}' to PDF at {}", (Object)htmlPath, (Object)pdfPath);
        }
        catch (Exception ex) {
            Log.error("Failed to save HTML as PDF '" + htmlPath + "'. Exc: ", (Throwable)ex);
            throw new Exception("Failed to save HTML as PDF. Reason: " + ex.getMessage());
        }
    }

    public ISaverPlugin clone() {
        return new PDFReportPlugin();
    }
}

