/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.whitelabel.AbstractBroker
 *  com.strategyquant.pluginlib.ISQPlugin
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.ProgramMethodDoesntExistException
 *  net.lingala.zip4j.core.ZipFile
 *  net.lingala.zip4j.model.ZipParameters
 *  org.jdom2.Document
 *  org.jdom2.Element
 *  org.jdom2.output.Format
 *  org.jdom2.output.XMLOutputter
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.results.file;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.whitelabel.AbstractBroker;
import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.ProgramMethodDoesntExistException;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.dailyEquity.DailyEquity;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.results.file.FileHandlerVariables;
import com.strategyquant.tradinglib.results.file.ILoaderPlugin;
import com.strategyquant.tradinglib.results.file.MissingInstrumentException;
import com.strategyquant.tradinglib.strategy.StrategyMerger;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.ObjectOutputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;
import java.util.zip.ZipOutputStream;
import net.lingala.zip4j.core.ZipFile;
import net.lingala.zip4j.model.ZipParameters;
import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.output.Format;
import org.jdom2.output.XMLOutputter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FileHandler
implements IProgram {
    public static final Logger Log = LoggerFactory.getLogger((String)"FileHandler");
    private ArrayList<ILoaderPlugin> loaderPlugins;
    private static final String xmlFileName = "settings.xml";
    private static final String ordersFileName = "orders.bin";
    private static final String dailyEquityFileName = "dailyEquity.bin";
    private static final String dailyEquityFileNameOld = "dailyEquity.old";
    private static final String versionFileName = "version.txt";
    private String lastSettingsFileName = "lastSettings.xml";
    private String optimizationProfileFileName = "optimizationProfile.bin";
    private ThreadLocal<FileHandlerVariables> localData = ThreadLocal.withInitial(() -> new FileHandlerVariables());

    public FileHandler() {
        this.loaderPlugins = SQPluginManager.getPlugins(ILoaderPlugin.class);
    }

    public Object call(String string, Object ... objectArray) throws Exception {
        switch (string) {
            case "loadFile": {
                if (objectArray.length == 1) {
                    return this.loadFile((String)objectArray[0]);
                }
                if (objectArray.length == 2) {
                    return this.loadFile((String)objectArray[0], (Boolean)objectArray[1], null, null);
                }
                if (objectArray.length == 3) {
                    return this.loadFile((String)objectArray[0], (Boolean)objectArray[1], (String)objectArray[2], null);
                }
                if (objectArray.length != 4) break;
                return this.loadFile((String)objectArray[0], (Boolean)objectArray[1], (String)objectArray[2], (String)objectArray[3]);
            }
            case "saveFile": {
                Map map = null;
                if (objectArray.length == 4) {
                    map = (Map)objectArray[3];
                }
                this.saveFile((ResultsGroup)objectArray[0], (String)objectArray[1], map);
                return null;
            }
            case "saveStrategyFile": {
                this.saveStrategyFile((Element)objectArray[0], (String)objectArray[1]);
                return null;
            }
        }
        throw new ProgramMethodDoesntExistException(string);
    }

    private ResultsGroup loadFile(String string) throws Exception {
        return this.loadFile(string, true, null, null);
    }

    private ResultsGroup loadFile(String string, boolean bl, String string2, String string3) throws Exception {
        FileHandlerVariables fileHandlerVariables = this.localData.get();
        File file = new File(string);
        if (!file.exists() || !file.isFile()) {
            throw new Exception("File '" + string + "' doesn't exist!");
        }
        fileHandlerVariables.loadedResult = null;
        fileHandlerVariables.loadedFilePath = string;
        this.preloadFile(bl, string2, string3);
        return this.finishLoad();
    }

    private ArrayList<ILoaderPlugin> getPossibleLoaders() {
        FileHandlerVariables fileHandlerVariables = this.localData.get();
        fileHandlerVariables.loadingErrorMessages = null;
        fileHandlerVariables.pluginLoaderUsed = null;
        String string = SQUtils.getExtension((String)fileHandlerVariables.loadedFilePath);
        if (!fileHandlerVariables.mapLoaders.containsKey(string.hashCode())) {
            ArrayList<ILoaderPlugin> arrayList = new ArrayList<ILoaderPlugin>();
            for (ILoaderPlugin iLoaderPlugin : this.loaderPlugins) {
                String[] stringArray = iLoaderPlugin.getFileExtensions();
                if (stringArray == null || stringArray.length <= 0) continue;
                for (int i = 0; i < stringArray.length; ++i) {
                    if (!stringArray[i].equalsIgnoreCase(string)) continue;
                    arrayList.add(iLoaderPlugin);
                }
            }
            fileHandlerVariables.mapLoaders.put(string.hashCode(), arrayList);
        }
        return (ArrayList)fileHandlerVariables.mapLoaders.get(string.hashCode());
    }

    private void preloadFile(boolean bl, String string, String string2) throws MissingInstrumentException {
        FileHandlerVariables fileHandlerVariables = this.localData.get();
        fileHandlerVariables.loadingErrorMessages = null;
        fileHandlerVariables.pluginLoaderUsed = null;
        ArrayList<ILoaderPlugin> arrayList = this.getPossibleLoaders();
        if (arrayList == null) {
            return;
        }
        for (int i = 0; i < arrayList.size(); ++i) {
            ILoaderPlugin iLoaderPlugin = arrayList.get(i);
            String string3 = SQPluginManager.getPluginName((ISQPlugin)iLoaderPlugin);
            try {
                iLoaderPlugin.initPlugin();
                ResultsGroup resultsGroup = iLoaderPlugin.load(fileHandlerVariables.loadedFilePath, bl, string, string2);
                if (resultsGroup == null) {
                    if (Log.isDebugEnabled()) {
                        Log.debug(" - Load using {} failed.", (Object)string3);
                    }
                    continue;
                }
                fileHandlerVariables.loadedResult = resultsGroup;
                fileHandlerVariables.loadingErrorMessages = null;
                fileHandlerVariables.pluginLoaderUsed = iLoaderPlugin;
                return;
            }
            catch (MissingInstrumentException missingInstrumentException) {
                throw missingInstrumentException;
            }
            catch (Exception exception) {
                if (Log.isDebugEnabled()) {
                    Log.debug(" - Load using {} failed with exception: {}", (Object)string3, (Object)exception.getMessage());
                }
                Log.error("Error loading file {}", (Object)fileHandlerVariables.loadedFilePath, (Object)exception);
                Log.info(SQUtils.getStackTrace());
                fileHandlerVariables.loadingErrorMessages = fileHandlerVariables.loadingErrorMessages == null ? "- error loading using " + string3 + " - " + exception.getMessage() + "\n" : fileHandlerVariables.loadingErrorMessages + "- error loading using " + string3 + " - " + exception.getMessage() + "\n";
                fileHandlerVariables.lastLoaderExc = exception;
            }
        }
    }

    private ResultsGroup finishLoad() throws Exception {
        FileHandlerVariables fileHandlerVariables = this.localData.get();
        if (fileHandlerVariables.loadedResult == null) {
            if (fileHandlerVariables.lastLoaderExc == null) {
                throw new Exception("No plugin loader was able to recognize file '" + fileHandlerVariables.loadedFilePath + "'");
            }
            throw new Exception(fileHandlerVariables.lastLoaderExc.getMessage());
        }
        fileHandlerVariables.loadedResult = fileHandlerVariables.pluginLoaderUsed.finishLoad(fileHandlerVariables.loadedResult);
        return fileHandlerVariables.loadedResult;
    }

    protected String getParam(Map<String, String[]> map, String string, String string2) throws Exception {
        if (map == null || !map.containsKey(string)) {
            return string2;
        }
        return map.get(string)[0];
    }

    public void saveFile(ResultsGroup resultsGroup, String string, Map<String, String[]> map) throws Exception {
        AbstractBroker abstractBroker;
        Object object;
        Object object2;
        Object object3;
        Object object4;
        String string2 = resultsGroup.specialValues().getString(SpecialValues.Note, "");
        boolean bl = Boolean.parseBoolean(this.getParam(map, "setNoteActive", "false"));
        if (bl) {
            object4 = this.getParam(map, "setNoteType", "");
            object3 = this.getParam(map, "setNoteCustomText", "");
            object2 = null;
            object = null;
            object2 = resultsGroup.mainResult().containsKey(SpecialValues.Symbol) ? resultsGroup.mainResult().getString(SpecialValues.Symbol) : resultsGroup.specialValues().getString(SpecialValues.Symbol, "N/A");
            object = resultsGroup.mainResult().containsKey(SpecialValues.Timeframe) ? resultsGroup.mainResult().getString(SpecialValues.Timeframe) : resultsGroup.specialValues().getString(SpecialValues.Timeframe, "N/A");
            switch (object4) {
                case "symbol": {
                    resultsGroup.specialValues().setString(SpecialValues.Note, (String)object2);
                    break;
                }
                case "timeframe": {
                    resultsGroup.specialValues().setString(SpecialValues.Note, (String)object);
                    break;
                }
                case "symbolTimeframe": {
                    resultsGroup.specialValues().setString(SpecialValues.Note, (String)object2 + "_" + (String)object);
                    break;
                }
                default: {
                    resultsGroup.specialValues().setString(SpecialValues.Note, (String)object3);
                }
            }
        }
        if (!((File)(object4 = new File(string))).getParentFile().exists()) {
            ((File)object4).getParentFile().mkdirs();
        }
        object3 = null;
        if (resultsGroup.specialValues().containsKey(SpecialValues.IsMergedPortfolio)) {
            object3 = StrategyMerger.getSplitResults(resultsGroup);
        }
        object2 = new Manifest();
        ((Manifest)object2).getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        object = new JarOutputStream((OutputStream)new BufferedOutputStream(new FileOutputStream((File)object4)), (Manifest)object2);
        try {
            this.writeSettingsFile(resultsGroup.getXML(), (JarOutputStream)object);
            this.writeStrategyFiles(resultsGroup, (JarOutputStream)object, this.getParam(map, "UserSecretCode", null));
            if (resultsGroup.storesChartData()) {
                this.writeTradingChartDataFiles(resultsGroup, (JarOutputStream)object);
            }
            this.writeCrossCheckData(resultsGroup, (JarOutputStream)object);
            this.writeLastSettingsFile(resultsGroup.getLastSettings(), (JarOutputStream)object);
            this.writeOptimizationProfileFile(resultsGroup.getOptimizationProfile(), (JarOutputStream)object);
            this.writeDailyEquityFiles(resultsGroup, (JarOutputStream)object);
            this.writeOrdersFile(resultsGroup.orders(), (JarOutputStream)object);
            if (bl) {
                resultsGroup.specialValues().setString(SpecialValues.Note, string2);
            }
            this.writeVersionFile((JarOutputStream)object, 1);
            if (object3 != null) {
                this.writeMergedStrategies((List<ResultsGroup>)object3, (JarOutputStream)object);
            }
            ((ZipOutputStream)object).close();
        }
        catch (Exception exception) {
            ((ZipOutputStream)object).close();
            object4 = new File(string);
            if (((File)object4).exists()) {
                ((File)object4).delete();
            }
            throw exception;
        }
        Object object5 = MainApp.v571hfnsHw();
        if (object5 != null && (abstractBroker = MainApp.v571hfnsHw().inygRmSMx7()) != null && abstractBroker.getPassword() != null) {
            File file = new File(string);
            File file2 = new File(string + "_tmp");
            ZipFile zipFile = new ZipFile(file2);
            ZipParameters zipParameters = new ZipParameters();
            zipParameters.setCompressionMethod(8);
            zipParameters.setCompressionLevel(9);
            zipParameters.setEncryptFiles(true);
            zipParameters.setEncryptionMethod(99);
            zipParameters.setAesKeyStrength(3);
            zipParameters.setPassword(abstractBroker.getPassword());
            zipFile.addFile(file, zipParameters);
            file.delete();
            file2.renameTo(file);
        }
    }

    private void writeVersionFile(JarOutputStream jarOutputStream, int n) throws Exception {
        JarEntry jarEntry = new JarEntry(versionFileName);
        jarOutputStream.putNextEntry(jarEntry);
        BufferedWriter bufferedWriter = new BufferedWriter(new OutputStreamWriter((OutputStream)jarOutputStream, StandardCharsets.UTF_8));
        String string = Integer.toString(n);
        bufferedWriter.write(string);
        bufferedWriter.flush();
    }

    private void writeCrossCheckData(ResultsGroup resultsGroup, JarOutputStream jarOutputStream) throws Exception {
        for (ICrossCheck iCrossCheck : SQPluginManager.getPlugins(ICrossCheck.class)) {
            try {
                iCrossCheck.saveDataToFile(resultsGroup, jarOutputStream);
            }
            catch (Exception exception) {
                Log.error("Saving crosscheck settings failed", (Throwable)exception);
            }
        }
    }

    private void writeTradingChartDataFiles(ResultsGroup resultsGroup, JarOutputStream jarOutputStream) throws Exception {
        for (String string : resultsGroup.getResultKeys()) {
            File file;
            Result result = resultsGroup.subResult(string);
            String string2 = result.getStockChartPath();
            if (string2 == null || !(file = new File(string2)).exists()) continue;
            try (JarFile jarFile = new JarFile(file);){
                string = SQUtils.correctResultKeyToDirname((String)string);
                Enumeration<JarEntry> enumeration = jarFile.entries();
                while (enumeration.hasMoreElements()) {
                    JarEntry jarEntry = enumeration.nextElement();
                    String string3 = jarEntry.getName();
                    if (string3.startsWith("META-INF")) continue;
                    JarEntry jarEntry2 = new JarEntry(jarEntry.getName());
                    InputStream inputStream = jarFile.getInputStream(jarEntry);
                    byte[] byArray = new byte[4096];
                    int n = 0;
                    jarOutputStream.putNextEntry(jarEntry2);
                    while ((n = inputStream.read(byArray)) != -1) {
                        jarOutputStream.write(byArray, 0, n);
                    }
                }
            }
            file.delete();
            result.clear();
        }
    }

    private void writeDailyEquityFiles(ResultsGroup resultsGroup, JarOutputStream jarOutputStream) throws Exception {
        for (String string : resultsGroup.getResultKeys()) {
            Result result = resultsGroup.subResult(string);
            string = SQUtils.correctResultKeyToDirname((String)string);
            JarEntry jarEntry = new JarEntry("Results/" + string + "/" + dailyEquityFileName);
            jarOutputStream.putNextEntry(jarEntry);
            ObjectOutputStream objectOutputStream = new ObjectOutputStream(new BufferedOutputStream(jarOutputStream));
            DailyEquity.serialize(result, objectOutputStream);
        }
    }

    private void writeStrategyFiles(ResultsGroup resultsGroup, JarOutputStream jarOutputStream, String string) throws Exception {
        for (String string2 : resultsGroup.getResultKeys()) {
            Result result = resultsGroup.subResult(string2);
            Element element = result.getStrategyXml();
            if (element == null) continue;
            JarEntry jarEntry = new JarEntry("strategy_Portfolio.xml");
            jarOutputStream.putNextEntry(jarEntry);
            Document document = new Document(element.clone());
            BufferedWriter bufferedWriter = new BufferedWriter(new OutputStreamWriter((OutputStream)jarOutputStream, "UTF8"));
            XMLOutputter xMLOutputter = new XMLOutputter(Format.getPrettyFormat());
            String string3 = xMLOutputter.outputString(document);
            if (string != null) {
                string3 = MainApp.getDataProtector().encryptBase64(string3, string);
            }
            bufferedWriter.write(string3);
            bufferedWriter.flush();
            return;
        }
    }

    private void writeSettingsFile(Element element, JarOutputStream jarOutputStream) throws IOException {
        JarEntry jarEntry = new JarEntry(xmlFileName);
        jarOutputStream.putNextEntry(jarEntry);
        Document document = new Document(element);
        BufferedWriter bufferedWriter = new BufferedWriter(new OutputStreamWriter((OutputStream)jarOutputStream, "UTF8"));
        XMLOutputter xMLOutputter = new XMLOutputter(Format.getRawFormat());
        xMLOutputter.output(document, (Writer)bufferedWriter);
    }

    private void writeLastSettingsFile(String string, JarOutputStream jarOutputStream) throws IOException {
        if (string != null) {
            JarEntry jarEntry = new JarEntry(this.lastSettingsFileName);
            jarOutputStream.putNextEntry(jarEntry);
            BufferedWriter bufferedWriter = new BufferedWriter(new OutputStreamWriter((OutputStream)jarOutputStream, "UTF8"));
            string = SQUtils.optimizeLastSettings((String)string);
            bufferedWriter.write(string);
            bufferedWriter.flush();
        }
    }

    private void writeOrdersFile(OrdersList ordersList, JarOutputStream jarOutputStream) throws Exception {
        JarEntry jarEntry = new JarEntry(ordersFileName);
        jarOutputStream.putNextEntry(jarEntry);
        ObjectOutputStream objectOutputStream = new ObjectOutputStream(new BufferedOutputStream(jarOutputStream));
        ordersList.serialize(objectOutputStream);
    }

    private void writeOptimizationProfileFile(OptimizationProfile optimizationProfile, JarOutputStream jarOutputStream) throws IOException {
        if (optimizationProfile != null) {
            JarEntry jarEntry = new JarEntry(this.optimizationProfileFileName);
            jarOutputStream.putNextEntry(jarEntry);
            ObjectOutputStream objectOutputStream = new ObjectOutputStream(new BufferedOutputStream(jarOutputStream));
            optimizationProfile.serialize(objectOutputStream);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void writeMergedStrategies(List<ResultsGroup> list, JarOutputStream jarOutputStream) {
        try {
            for (int i = 0; i < list.size(); ++i) {
                ResultsGroup resultsGroup = list.get(i);
                File file = new File(StrategyMerger.TempPath + UUID.randomUUID());
                this.saveFile(resultsGroup, file.getAbsolutePath(), null);
                InputStream inputStream = null;
                JarEntry jarEntry = new JarEntry("PortfolioParts/" + resultsGroup.getName() + ".sqx");
                jarOutputStream.putNextEntry(jarEntry);
                try {
                    int n;
                    inputStream = new BufferedInputStream(new FileInputStream(file));
                    byte[] byArray = new byte[1024];
                    while ((n = inputStream.read(byArray)) != -1) {
                        jarOutputStream.write(byArray, 0, n);
                    }
                }
                finally {
                    if (inputStream != null) {
                        inputStream.close();
                    }
                }
                try {
                    file.delete();
                    continue;
                }
                catch (Exception exception) {
                    Log.error("Error while deleting temp file", (Throwable)exception);
                }
            }
        }
        catch (Exception exception) {
            Log.error("Failed to save merged strategies into ResultsGroup file", (Throwable)exception);
        }
    }

    public void saveStrategyFile(Element element, String string) throws Exception {
        File file = new File(string);
        if (!file.getParentFile().exists()) {
            file.getParentFile().mkdirs();
        }
        Manifest manifest = new Manifest();
        manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
        JarOutputStream jarOutputStream = new JarOutputStream((OutputStream)new BufferedOutputStream(new FileOutputStream(file)), manifest);
        try {
            JarEntry jarEntry = new JarEntry("strategy_Portfolio.xml");
            jarOutputStream.putNextEntry(jarEntry);
            BufferedWriter bufferedWriter = new BufferedWriter(new OutputStreamWriter((OutputStream)jarOutputStream, "UTF8"));
            XMLOutputter xMLOutputter = new XMLOutputter(Format.getPrettyFormat());
            String string2 = xMLOutputter.outputString(element);
            bufferedWriter.write(string2);
            jarOutputStream.close();
        }
        catch (Exception exception) {
            jarOutputStream.close();
            file = new File(string);
            if (file.exists()) {
                file.delete();
            }
            throw exception;
        }
    }
}

