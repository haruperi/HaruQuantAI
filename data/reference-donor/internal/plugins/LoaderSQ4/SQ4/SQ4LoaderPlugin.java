/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.whitelabel.AbstractBroker
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.dailyEquity.DailyEquity
 *  com.strategyquant.tradinglib.optimization.OptimizationProfile
 *  com.strategyquant.tradinglib.results.file.ILoaderPlugin
 *  com.strategyquant.tradinglib.strategy.xml.SQ3StrategyConverter
 *  com.strategyquant.tradinglib.strategy.xml.StrategyFixer
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  net.lingala.zip4j.core.ZipFile
 *  net.lingala.zip4j.exception.ZipException
 *  net.lingala.zip4j.model.FileHeader
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.jdom2.Element
 *  org.jdom2.output.Format
 *  org.jdom2.output.XMLOutputter
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Loader.impl.SQ4;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.whitelabel.AbstractBroker;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.dailyEquity.DailyEquity;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.results.file.ILoaderPlugin;
import com.strategyquant.tradinglib.strategy.xml.SQ3StrategyConverter;
import com.strategyquant.tradinglib.strategy.xml.StrategyFixer;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.ObjectInput;
import java.io.ObjectInputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Enumeration;
import java.util.List;
import java.util.UUID;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import net.lingala.zip4j.core.ZipFile;
import net.lingala.zip4j.exception.ZipException;
import net.lingala.zip4j.model.FileHeader;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.jdom2.Element;
import org.jdom2.output.Format;
import org.jdom2.output.XMLOutputter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Author(name="Mark Fric")
@Name(name="SQXLoaderPlugin plugin")
@Category(name="File Loader")
@License(text="")
@ShortDesc(text="Short description")
@PluginImplementation
public class SQ4LoaderPlugin
implements ILoaderPlugin {
    public static final Logger Log = LoggerFactory.getLogger(SQ4LoaderPlugin.class);
    public static final String[] extensions = new String[]{"sq4", "sqw", "sqx"};
    private XMLOutputter xmlOutputter = new XMLOutputter(Format.getPrettyFormat());
    private static final long SLOW_LOAD_MS = 3000L;

    public String getProduct() {
        return "any";
    }

    public int getPreferredPosition() {
        return 0;
    }

    public void initPlugin() throws Exception {
    }

    public String[] getFileExtensions() {
        return extensions;
    }

    public ResultsGroup load(String fileName, boolean exceptionOnMissingInstrument, String missingInstrumentReplacement, String userSecretCode) throws Exception {
        if (fileName.endsWith("sq4") || fileName.endsWith("sqx")) {
            return this.loadSQ4File(fileName, exceptionOnMissingInstrument, missingInstrumentReplacement, userSecretCode);
        }
        return this.loadSQWFile(fileName, exceptionOnMissingInstrument, userSecretCode);
    }

    private ResultsGroup loadSQWFile(String fileName, boolean exceptionOnMissingInstrument, String userSecretCode) throws Exception {
        Log.debug("Loading SQW file {}", (Object)fileName);
        ResultsGroup rg = null;
        File f = new File(fileName);
        String strategyName = SQUtils.stripExtension((String)f.getName());
        rg = new ResultsGroup(strategyName);
        rg.setResultFileName(fileName);
        String strategyXML = SQUtils.fileToString((File)f);
        if (strategyXML == null) {
            throw new Exception(L.t((String)"Cannot load strategy XML from the file.", (Object[])new Object[0]));
        }
        strategyXML = MainApp.getDataProtector().decryptBase64(strategyXML, userSecretCode);
        Element elStrategy = XMLUtil.stringToElement((String)strategyXML);
        if (elStrategy != null) {
            String version = elStrategy.getAttributeValue("version");
            try {
                if (version != null && Double.parseDouble(version) < 3.8) {
                    elStrategy = SQ3StrategyConverter.getInstance().convert(elStrategy);
                }
                elStrategy = StrategyFixer.fixStrategy((String)XMLUtil.elementToString((Element)elStrategy));
            }
            catch (Exception e) {
                Log.error("Modifying XML config failed", (Throwable)e);
            }
        }
        rg.addSubresult(strategyName, new SettingsMap());
        rg.computeAllStats();
        rg.portfolio().addStrategyXml(elStrategy);
        rg.updated = true;
        return rg;
    }

    private ResultsGroup loadSQ4File(String fileName, boolean exceptionOnMissingInstrument, String missingInstrumentReplacement, String userSecretCode) throws Exception {
        ResultsGroup resultsGroup;
        String tmpFile;
        block20: {
            Log.debug("Loading file {}", (Object)fileName);
            tmpFile = null;
            try {
                ZipFile zipFile = new ZipFile(fileName);
                if (zipFile.isEncrypted()) {
                    AbstractBroker broker = MainApp.getLicenseInfo().getBroker();
                    if (broker == null || broker.getPassword() == null) {
                        throw new Exception(L.t((String)"Cannot read strategy file - it is broker-locked", (Object[])new Object[0]));
                    }
                    String tmpPath = MainApp.getDataPath() + "/internal/tmp/";
                    tmpFile = tmpPath + UUID.randomUUID();
                    List fileHeaders = zipFile.getFileHeaders();
                    String simpleFileName = ((FileHeader)fileHeaders.get(0)).getFileName();
                    zipFile.setPassword(broker.getPassword());
                    zipFile.extractAll(tmpPath);
                    new File(tmpPath + simpleFileName).renameTo(new File(tmpFile));
                }
            }
            catch (ZipException e) {
                Log.error("Cannot read strategy file", (Throwable)e);
                throw new Exception(L.t((String)"Cannot read strategy file", (Object[])new Object[0]) + " - " + e.getMessage());
            }
            java.util.zip.ZipFile jarFile = null;
            ResultsGroup rg = null;
            try {
                String strategyXML;
                jarFile = new JarFile(tmpFile == null ? fileName : tmpFile);
                File f = new File(fileName);
                String strategyName = SQUtils.stripExtension((String)f.getName());
                rg = new ResultsGroup(strategyName);
                rg.setResultFileName(fileName);
                JarEntry versionFile = ((JarFile)jarFile).getJarEntry("version.txt");
                int version = this.recognizeVersion((JarFile)jarFile, versionFile);
                Log.debug("Version recognized to: {}", (Object)version);
                JarEntry strategyFile = ((JarFile)jarFile).getJarEntry("strategy_Portfolio.xml");
                JarEntry settingsFile = ((JarFile)jarFile).getJarEntry("settings.xml");
                Element elStrategy = null;
                if (strategyFile == null && settingsFile == null) {
                    throw new Exception(L.t((String)"Cannot load ResultsGroup from file. Cannot find any settings inside the file.", (Object[])new Object[0]));
                }
                long phaseStart = System.currentTimeMillis();
                if (strategyFile != null && (strategyXML = SQUtils.inputStreamToString((InputStream)((JarFile)jarFile).getInputStream(strategyFile))) != null) {
                    strategyXML = MainApp.getDataProtector().decryptBase64(strategyXML, userSecretCode);
                    try {
                        elStrategy = StrategyFixer.fixStrategy((String)strategyXML);
                    }
                    catch (Exception e) {
                        Log.error("Modifying XML config failed", (Throwable)e);
                    }
                }
                long strategyXmlMs = System.currentTimeMillis() - phaseStart;
                phaseStart = System.currentTimeMillis();
                this.loadOrders(rg.orders(), (JarFile)jarFile);
                long ordersMs = System.currentTimeMillis() - phaseStart;
                phaseStart = System.currentTimeMillis();
                if (settingsFile != null) {
                    Element xmlConfig = XMLUtil.readXmlFile((InputStream)((JarFile)jarFile).getInputStream(settingsFile));
                    this.fixOldSettingsResultKeys(xmlConfig);
                    rg.setFromXML(xmlConfig);
                } else {
                    rg.addSubresult(strategyName, new SettingsMap());
                    rg.computeAllStats();
                }
                long settingsMs = System.currentTimeMillis() - phaseStart;
                phaseStart = System.currentTimeMillis();
                this.loadLastSettings(rg, (JarFile)jarFile);
                this.loadOptimizationProfile(rg, (JarFile)jarFile);
                long profilesMs = System.currentTimeMillis() - phaseStart;
                phaseStart = System.currentTimeMillis();
                this.loadResultsData(rg, (JarFile)jarFile);
                long resultsDataMs = System.currentTimeMillis() - phaseStart;
                phaseStart = System.currentTimeMillis();
                this.loadCrossCheckData(rg, (JarFile)jarFile);
                long crossCheckMs = System.currentTimeMillis() - phaseStart;
                phaseStart = System.currentTimeMillis();
                if (elStrategy != null) {
                    rg.portfolio().addStrategyXml(elStrategy);
                }
                if (version == 0) {
                    Log.debug("Recomputing daily equity");
                    Long2FloatRBTreeMap portfolioWorstDailyEquity = rg.recomputeMergedDailyEquity();
                    if (portfolioWorstDailyEquity != null) {
                        rg.portfolio().setWorstDailyEquity(portfolioWorstDailyEquity);
                    }
                }
                long portfolioMs = System.currentTimeMillis() - phaseStart;
                this.logLoadPhases(fileName, rg.orders().size(), strategyXmlMs, ordersMs, settingsMs, profilesMs, resultsDataMs, crossCheckMs, portfolioMs);
                rg.updated = true;
                resultsGroup = rg;
                if (jarFile == null) break block20;
            }
            catch (Exception e) {
                try {
                    throw e;
                }
                catch (Throwable throwable) {
                    if (jarFile != null) {
                        jarFile.close();
                    }
                    if (tmpFile != null) {
                        Files.delete(new File(tmpFile).toPath());
                    }
                    throw throwable;
                }
            }
            jarFile.close();
        }
        if (tmpFile != null) {
            Files.delete(new File(tmpFile).toPath());
        }
        return resultsGroup;
    }

    private void logLoadPhases(String fileName, int orderCount, long strategyXmlMs, long ordersMs, long settingsMs, long profilesMs, long resultsDataMs, long crossCheckMs, long portfolioMs) {
        long total = strategyXmlMs + ordersMs + settingsMs + profilesMs + resultsDataMs + crossCheckMs + portfolioMs;
        String message = "Loaded {} ({} orders) in {} ms - strategyXml {}, orders {}, settings {}, profiles {}, resultsData {}, crossChecks {}, portfolio {}";
        if (total >= 3000L) {
            Log.info(message, new Object[]{fileName, orderCount, total, strategyXmlMs, ordersMs, settingsMs, profilesMs, resultsDataMs, crossCheckMs, portfolioMs});
        } else {
            Log.debug(message, new Object[]{fileName, orderCount, total, strategyXmlMs, ordersMs, settingsMs, profilesMs, resultsDataMs, crossCheckMs, portfolioMs});
        }
    }

    private int recognizeVersion(JarFile jarFile, JarEntry versionFile) {
        if (versionFile == null) {
            return 0;
        }
        try {
            String line;
            BufferedReader br = new BufferedReader(new InputStreamReader(jarFile.getInputStream(versionFile), StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            while ((line = br.readLine()) != null) {
                sb.append(line);
            }
            br.close();
            return Integer.parseInt(sb.toString());
        }
        catch (Exception e) {
            Log.error("Cannot recognize version");
            return 0;
        }
    }

    private void fixOldSettingsResultKeys(Element xmlConfig) {
    }

    private void loadLastSettings(ResultsGroup rg, JarFile jarFile) throws IOException, Exception {
        try {
            JarEntry lastSettingsFile = jarFile.getJarEntry("lastSettings.xml");
            if (lastSettingsFile != null) {
                String lastSettingsXml = SQUtils.inputStreamToString((InputStream)jarFile.getInputStream(lastSettingsFile));
                lastSettingsXml = SQUtils.optimizeLastSettings((String)lastSettingsXml);
                rg.setLastSettings(lastSettingsXml.intern());
            }
        }
        catch (Exception e) {
            Log.error("Problem loading last setting ", (Throwable)e);
        }
    }

    private void loadOptimizationProfile(ResultsGroup rg, JarFile jarFile) throws IOException, Exception {
        try {
            JarEntry optimizationProfileFileBin;
            OptimizationProfile op;
            JarEntry optimizationProfileFileXml = jarFile.getJarEntry("optimizationProfile.xml");
            if (optimizationProfileFileXml != null) {
                Element xmlOP = XMLUtil.readXmlFile((InputStream)jarFile.getInputStream(optimizationProfileFileXml));
                op = new OptimizationProfile();
                op.setFromXML(xmlOP);
                rg.setOptimizationProfile(op);
            }
            if ((optimizationProfileFileBin = jarFile.getJarEntry("optimizationProfile.bin")) != null) {
                op = new OptimizationProfile();
                ObjectInputStream dis = new ObjectInputStream(jarFile.getInputStream(optimizationProfileFileBin));
                op.deserialize((ObjectInput)dis);
                dis.close();
                rg.setOptimizationProfile(op);
            }
        }
        catch (Exception e) {
            Log.error("Problem loading optimization profile ", (Throwable)e);
        }
    }

    private void loadCrossCheckData(ResultsGroup rg, JarFile jarFile) throws Exception {
        for (ICrossCheck plugin : SQPluginManager.getPlugins(ICrossCheck.class)) {
            try {
                plugin.loadDataFromFile(rg, jarFile);
            }
            catch (Exception e) {
                Log.error("Loading crosscheck '" + plugin.getName() + "' settings failed", (Throwable)e);
            }
        }
    }

    private void loadResultsData(ResultsGroup rg, JarFile jarFile) throws Exception {
        Enumeration<JarEntry> entries = jarFile.entries();
        while (entries.hasMoreElements()) {
            int pos2;
            String name = entries.nextElement().getName();
            if (!name.startsWith("Results/") || (pos2 = name.lastIndexOf("/")) <= 8) continue;
            String resultKey = name.substring(8, pos2);
            try {
                Result result = rg.subResult(SQUtils.correctDirnameToResultKey((String)resultKey));
                if (result == null) {
                    throw new Exception(L.t((String)"Result '%s' is null!", (Object[])new Object[]{resultKey}));
                }
                if (name.endsWith("dailyEquity.csv")) {
                    this.loadDailyEquityDataOldFormat(result, resultKey, jarFile);
                }
                if (!name.endsWith("dailyEquity.bin")) continue;
                this.loadDailyEquityData(result, resultKey, jarFile);
            }
            catch (IllegalArgumentException e) {
                Log.error("Cannot find result", (Throwable)e);
            }
        }
    }

    private void loadDailyEquityDataOldFormat(Result result, String resultKey, JarFile jarFile) throws Exception {
        JarEntry csvFileEntry = jarFile.getJarEntry("Results/" + resultKey + "/dailyEquity.csv");
        if (csvFileEntry == null) {
            return;
        }
        DailyEquity.loadCsv((Result)result, (InputStream)jarFile.getInputStream(csvFileEntry));
    }

    private void loadDailyEquityData(Result result, String resultKey, JarFile jarFile) throws Exception {
        JarEntry fileEntry = jarFile.getJarEntry("Results/" + resultKey + "/dailyEquity.bin");
        if (fileEntry == null) {
            return;
        }
        if (fileEntry.getSize() > 0L) {
            DailyEquity.load((Result)result, (InputStream)jarFile.getInputStream(fileEntry));
        }
    }

    private void loadOrders(OrdersList orders, JarFile jarFile) throws Exception {
        JarEntry ordersFile = jarFile.getJarEntry("orders.bin");
        try {
            if (ordersFile != null && ordersFile.getSize() > 10L) {
                long start = System.currentTimeMillis();
                ObjectInputStream dis = new ObjectInputStream(jarFile.getInputStream(ordersFile));
                orders.deserialize((ObjectInput)dis);
                dis.close();
                long l = System.currentTimeMillis();
            }
        }
        catch (Exception e) {
            Log.error("Error loading orders", (Throwable)e);
        }
    }

    public ResultsGroup finishLoad(ResultsGroup result) throws Exception {
        return result;
    }
}

