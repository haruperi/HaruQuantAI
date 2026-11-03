/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer
 *  com.strategyquant.lib.utils.SQFileChooserFactory
 *  com.strategyquant.tradinglib.strategy.xml.StrategyFixerWizardOld
 *  freemarker.cache.FileTemplateLoader
 *  freemarker.cache.TemplateLoader
 *  freemarker.ext.dom.NodeModel
 *  freemarker.template.Configuration
 *  freemarker.template.Template
 *  freemarker.template.TemplateMethodModel
 *  freemarker.template.TemplateModelException
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 */
package com.strategyquant.wizard.desktop.loader;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer;
import com.strategyquant.lib.utils.SQFileChooserFactory;
import com.strategyquant.tradinglib.strategy.xml.StrategyFixerWizardOld;
import com.strategyquant.wizard.desktop.loader.Template;
import com.strategyquant.wizard.desktop.settings.Settings;
import com.strategyquant.wizard.desktop.utils.FileUtils;
import freemarker.cache.FileTemplateLoader;
import freemarker.cache.TemplateLoader;
import freemarker.ext.dom.NodeModel;
import freemarker.template.Configuration;
import freemarker.template.TemplateMethodModel;
import freemarker.template.TemplateModelException;
import java.awt.Component;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.StringReader;
import java.io.StringWriter;
import java.io.Writer;
import java.nio.file.Files;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import javax.swing.JFileChooser;
import javax.swing.filechooser.FileNameExtensionFilter;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.xml.sax.InputSource;

public class TransformEngineLoader {
    private Component parent;

    public TransformEngineLoader(Component component) {
        this.parent = component;
    }

    public String load() {
        String string = FileUtils.getAppFolder();
        File file = new File(FileUtils.getCodeFolder());
        File[] fileArray = file.listFiles();
        LinkedList<Template> linkedList = new LinkedList<Template>();
        Template template = new Template();
        if (fileArray != null) {
            for (File object : fileArray) {
                if (!object.isDirectory() || !this.dirContainsMainTpl(object)) continue;
                try {
                    linkedList.add(this.createTemplate(object));
                }
                catch (IOException iOException) {
                    iOException.printStackTrace();
                }
            }
        }
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("{\"templates\":[");
        int n = 1;
        for (Template template2 : linkedList) {
            if (n == 0) {
                stringBuilder.append(",");
            }
            stringBuilder.append(template2.toJson());
            n = 0;
        }
        stringBuilder.append("]}");
        return stringBuilder.toString();
    }

    private boolean dirContainsMainTpl(File file) {
        return new File(file, "Main.tpl").exists();
    }

    private String getResult(boolean bl, String string) {
        String string2 = bl ? "success" : "failure";
        string = string.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\\\n").replace("\r", "\\\\r").replace("\t", "\\\\t");
        return "{\"result\":\"" + string2 + "\",\"result\":\"" + string + "\"}";
    }

    public String transformCode(String string, String string2) {
        try {
            String string3 = this.performTransformCode(string, string2);
            return this.getResult(true, string3);
        }
        catch (Exception exception) {
            return this.getResult(false, exception.getMessage());
        }
    }

    public String performTransformCode(String string, String string2) {
        try {
            Element element = XMLUtil.stringToXmlElement((String)SQUtils.fixRenamedActionParams((String)string));
            XMLIndicatorsAnalyzer.init();
            XMLIndicatorsAnalyzer.fixItemAttributes((Element)element);
            string = XMLUtil.elementToString((Element)element);
            string = string.replace("\n", "").replace("\r", "").replace("\t", "").replaceAll(" +", " ").replace("> <", "><");
            Configuration configuration = new Configuration(Configuration.VERSION_2_3_0);
            System.out.println("Using folder:" + FileUtils.getCodeFolder());
            String string3 = FileUtils.getAppFolder();
            FileTemplateLoader fileTemplateLoader = new FileTemplateLoader(new File(FileUtils.getCodeFolder()), true);
            configuration.setTemplateLoader((TemplateLoader)fileTemplateLoader);
            freemarker.template.Template template = null;
            try {
                System.out.println("Using template:" + string2 + "\\Main.tpl");
                template = configuration.getTemplate(string2 + "\\Main.tpl");
            }
            catch (IOException iOException) {
                throw new RuntimeException(L.t((String)"Error while loading template - '%s'", (Object[])new Object[]{iOException.getMessage()}));
            }
            configuration.setDefaultEncoding("UTF-8");
            InputSource inputSource = new InputSource();
            inputSource.setCharacterStream(new StringReader(string));
            HashMap<String, Object> hashMap = new HashMap<String, Object>();
            hashMap.put("doc", NodeModel.parse((InputSource)inputSource));
            hashMap.put("blockFileExists", new BlockFileExistsDirectivaModel(string2));
            StringWriter stringWriter = new StringWriter();
            template.process(hashMap, (Writer)stringWriter);
            return stringWriter.toString();
        }
        catch (Exception exception) {
            throw new RuntimeException(L.t((String)"Error while generating template - '%s'", (Object[])new Object[]{exception.getMessage()}));
        }
    }

    public void transformCode(String string, String string2, String string3) throws JDOMException, Exception {
        File file = new File(string);
        if (!file.exists()) {
            System.err.println("File " + string + " doesn't exists.");
            return;
        }
        String string4 = null;
        try {
            string4 = new String(Files.readAllBytes(file.toPath()));
            string4 = StrategyFixerWizardOld.fixStrategy((String)string4, (String)(FileUtils.getAppFolder() + "//branding//global//config.xml"), (boolean)true);
            int n = string4.indexOf("<Strategy ");
            String string5 = string4.substring(0, n);
            String string6 = string4.substring(n);
            String string7 = this.getInformationsXml(file, string3);
            string4 = string5 + string7 + "<CustomForm></CustomForm>" + string6;
            string4 = string4.replace("\n", "").replace("\r", "").replace("\t", "").replaceAll(" +", " ").replace("> <", "><");
        }
        catch (IOException iOException) {
            System.err.println("Error while reading file's content " + string);
            return;
        }
        String string8 = this.performTransformCode(string4, string3);
        try {
            this.saveFile(string8, new File(string2));
            System.out.println("Saved file " + string2);
        }
        catch (IOException iOException) {
            System.err.println("Error while writing result file");
        }
    }

    private String getInformationsXml(File file, String string) {
        String string2 = file.getName();
        return "<options><StrategyName>" + string2 + "</StrategyName><Engine>" + string + "</Engine><Version></Version><Date>" + new SimpleDateFormat("dd/mm/yyyy HH:MM").format(new Date()) + "</Date></options>";
    }

    public void save(String string, String string2, String string3) {
        String string4 = Settings.get().get("resultFolder");
        JFileChooser jFileChooser = SQFileChooserFactory.createPersistingJFileChooser((String)(string4.isEmpty() ? null : string4)).getJFileChooser();
        FileNameExtensionFilter fileNameExtensionFilter = new FileNameExtensionFilter(string2, "*." + string3);
        jFileChooser.setFileFilter(fileNameExtensionFilter);
        int n = jFileChooser.showSaveDialog(this.parent);
        if (n == 0) {
            File file = jFileChooser.getSelectedFile();
            Settings.get().set("resultFolder", file.getParent());
            try {
                this.saveFile(string, file);
            }
            catch (IOException iOException) {
                iOException.printStackTrace();
            }
        } else {
            return;
        }
    }

    private void saveFile(String string, File file) throws IOException {
        FileWriter fileWriter = null;
        fileWriter = new FileWriter(file);
        fileWriter.write(string);
        fileWriter.close();
    }

    private Template createTemplate(File file) throws IOException {
        String string = new String(Files.readAllBytes(new File(file, "Main.tpl").toPath()));
        String string2 = this.getStringBetween(string, "<name>", "</name>");
        String string3 = this.getStringBetween(string, "<extension>", "</extension>");
        String string4 = this.getStringBetween(string, "<description>", "</description>");
        if (string4 != null) {
            string4 = string4.replaceAll("( +)", " ");
            string4 = string4.replaceAll("&lt;", "<");
            string4 = string4.replaceAll("&gt;", ">");
            string4 = string4.replace("\"", "'");
            string4 = string4.replace("\n", "");
            string4 = string4.replace("\r", "");
        } else {
            string4 = "";
        }
        String string5 = this.getStringBetween(string, "<form>", "</form>");
        Template template = new Template();
        template.setDescriptions(string4);
        template.setName(string2);
        template.setExtension(string3);
        template.setId(file.getName());
        template.setForm(string5);
        return template;
    }

    private String getStringBetween(String string, String string2, String string3) {
        int n = string.indexOf(string2) + string2.length();
        if (n < 0) {
            return null;
        }
        int n2 = string.indexOf(string3, n);
        if (n2 < 0 || n2 <= n) {
            return null;
        }
        return string.substring(n, n2);
    }

    public void dispose() {
        this.parent = null;
    }

    public static class BlockFileExistsDirectivaModel
    implements TemplateMethodModel {
        private String engine;

        public BlockFileExistsDirectivaModel(String string) {
            this.engine = string;
        }

        public Object exec(List list) throws TemplateModelException {
            String string = FileUtils.getCodeFolder();
            String string2 = string + "\\" + this.engine + "\\blocks\\";
            String string3 = (String)list.get(0);
            boolean bl = new File(string2, string3 + ".tpl").exists();
            return bl;
        }
    }
}

