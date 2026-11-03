/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.jfx.net.JFXServer
 *  com.jfx.strategy.Strategy
 *  com.jfx.ts.io.PSUtils
 *  net.lingala.zip4j.core.ZipFile
 *  net.lingala.zip4j.exception.ZipException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Connection.impl.MT4;

import com.jfx.net.JFXServer;
import com.jfx.strategy.Strategy;
import com.jfx.ts.io.PSUtils;
import java.io.File;
import java.io.PrintWriter;
import java.util.HashMap;
import net.lingala.zip4j.core.ZipFile;
import net.lingala.zip4j.exception.ZipException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MT4TerminalManager {
    private static final Logger Log = LoggerFactory.getLogger(MT4TerminalManager.class);
    private static String curTerminalPath;
    private static String terminalsFolder;
    private static String zipPath;
    private static final String host = "127.0.0.1";
    private static final int port = 7777;
    private static HashMap<String, Integer> terminalPIDs;

    public static void init() throws Exception {
        System.setProperty("jfx_server_host", host);
        System.setProperty("jfx_server_port", String.valueOf(7777));
        System.setProperty("nj4x_server_port", String.valueOf(7777));
        String userDir = System.getProperty("user.dir");
        terminalsFolder = userDir + "/internal/SQTRADER/terminals";
        zipPath = terminalsFolder + "/terminal.zip";
        JFXServer.getInstance();
        try {
            JFXServer.getInstance();
            Log.info("JFX server initialized at 127.0.0.1:7777");
        }
        catch (Exception ex) {
            String message = "JFX server initialization at 127.0.0.1:7777 failed.";
            Log.info(message);
            throw new Exception(message);
        }
    }

    public static void deinit() throws Exception {
        PSUtils.getInstance().deinit();
        JFXServer.stop();
    }

    public static void createTerminal(String user, String password, String brokerIP, String terminalName, Strategy strategy, boolean hide, boolean minimize, boolean connectOnStart) throws Exception {
        if (!MT4TerminalManager.terminalExists(terminalName)) {
            MT4TerminalManager.createTerminalFolderFromZip(zipPath, terminalsFolder, terminalName);
            MT4TerminalManager.createMTInitFile(user, password, brokerIP);
            MT4TerminalManager.createEASetFile(host, 7777, terminalName);
            MT4TerminalManager.startMetaTrader(terminalName, hide, minimize);
        } else {
            MT4TerminalManager.startMetaTrader(terminalName, hide, minimize);
        }
    }

    private static void createTerminalFolderFromZip(String zipPath, String folderPath, String folderName) throws Exception {
        curTerminalPath = folderPath + "/" + folderName;
        Log.info("Creating terminal folder \"" + curTerminalPath + "\"");
        File folder = new File(curTerminalPath);
        MT4TerminalManager.deleteDirectory(folder);
        if (folder.exists() || folder.mkdirs()) {
            try {
                ZipFile zipFile = new ZipFile(zipPath);
                zipFile.extractAll(curTerminalPath);
            }
            catch (ZipException e) {
                throw new Exception("Cannot unzip file \"" + zipPath + "\" into \"" + curTerminalPath + "\"");
            }
        } else {
            throw new Exception("Cannot create folder \"" + folderName + "\" in \"" + folderPath + "\"");
        }
    }

    private static void startMetaTrader(String terminalName, boolean hide, boolean minimize) {
        Log.info("Starting MT4...");
        String exePath = "\"" + curTerminalPath + "/terminal.exe\"";
        String iniPath = "\"" + curTerminalPath + "/init.ini\"";
        String args = " /portable /skipupdate " + iniPath;
        boolean minimized = minimize;
        if (hide) {
            minimized = false;
        }
        int pid = PSUtils.getInstance().startProcess2(exePath + args, curTerminalPath, hide, true, minimized);
        terminalPIDs.put(terminalName, pid);
    }

    private static void createMTInitFile(String user, String password, String brokerIP) throws Exception {
        String fileName = curTerminalPath + "/init.ini";
        try (PrintWriter writer = new PrintWriter(fileName);){
            writer.println("; common settings");
            writer.println("Profile=default");
            writer.println("Login=" + user);
            writer.println("Password=" + password);
            writer.println("Server=" + brokerIP);
            writer.println("AutoConfiguration=false");
            writer.println(";  DataServer=192.168.0.1:443");
            writer.println("EnableDDE=false");
            writer.println("EnableNews=false");
            writer.println("ProxyEnable=false");
            writer.println("ProxyServer=$ProxyServer$");
            writer.println("ProxyType=$ProxyType$");
            writer.println("ProxyLogin=$ProxyLogin$");
            writer.println("ProxyPassword=$ProxyPassword$");
            writer.println("; experts settings");
            writer.println("ExpertsEnable=true");
            writer.println("ExpertsDllImport=true");
            writer.println("ExpertsDllConfirm=false");
            writer.println("ExpertsExpImport=true");
            writer.println("ExpertsTrades=true");
            writer.println("ExpertsTradesConfirm=false");
            writer.println("Expert=jfx");
            writer.println("ExpertParameters=jfx_ea.set");
            writer.println("Symbol=EURUSD");
            writer.println("Period=H4");
            writer.flush();
            writer.close();
        }
        catch (Exception e) {
            throw new Exception("Error creating Strategy set file: \"" + fileName + "\"", e);
        }
    }

    private static void createEASetFile(String host, int port, String strategyName) throws Exception {
        String fileName = curTerminalPath + "/MQL4/Presets/jfx_ea.set";
        try (PrintWriter writer = new PrintWriter(fileName);){
            writer.println("jfxHost=" + host);
            writer.println("jfxPort=" + port);
            writer.println("strategy=" + strategyName);
            writer.println("param1=0.0");
            writer.println("param2=0.0");
            writer.println("param3=0.0");
            writer.println("param4=0.0");
            writer.println("param5=0.0");
            writer.println("param6=0.0");
            writer.println("param7=0.0");
            writer.println("param8=0.0");
            writer.println("param9=0.0");
            writer.println("param10=0.0");
            writer.println("DEBUG_DLL=false");
            writer.flush();
            writer.close();
        }
        catch (Exception e) {
            throw new Exception("Error creating Strategy set file: \"" + fileName + "\"", e);
        }
    }

    public static void removeAllTerminals() throws Exception {
        for (String terminalName : terminalPIDs.keySet()) {
            MT4TerminalManager.removeTerminal(terminalName);
        }
    }

    /*
     * Enabled force condition propagation
     * Lifted jumps to return sites
     */
    public static void removeTerminal(String terminalName) throws Exception {
        Log.info("Removing teminal \"" + terminalName + "\"");
        if (MT4TerminalManager.terminalExists(terminalName)) {
            if (!MT4TerminalManager.killTerminalProcess(terminalName)) throw new Exception("Cannot terminate terminal process");
            terminalPIDs.remove(terminalName);
            try {
                Thread.sleep(1000L);
            }
            catch (InterruptedException e) {
                e.printStackTrace();
            }
            String path = terminalsFolder + "/" + terminalName;
            if (MT4TerminalManager.deleteDirectory(new File(path))) return;
            Log.error("Cannot delete folder \"" + path + "\"");
            return;
        }
        Log.warn("Terminal \"" + terminalName + "\" does not exist.");
    }

    private static boolean terminalExists(String name) {
        for (String terminalName : terminalPIDs.keySet()) {
            if (terminalName.compareTo(name) != 0) continue;
            return true;
        }
        return false;
    }

    private static boolean deleteDirectory(File directory) {
        File[] files;
        if (directory.exists() && null != (files = directory.listFiles())) {
            for (int i = 0; i < files.length; ++i) {
                if (files[i].isDirectory()) {
                    MT4TerminalManager.deleteDirectory(files[i]);
                    continue;
                }
                files[i].delete();
            }
        }
        return directory.delete();
    }

    public static int getTerminalPID(String connectionName) {
        return terminalPIDs.get(connectionName);
    }

    public static boolean killTerminalProcess(String connectionName) {
        int pid = terminalPIDs.get(connectionName);
        boolean alreadyTerminated = PSUtils.getInstance().getHwndByPID(pid) == 0;
        return alreadyTerminated || PSUtils.getInstance().terminateApp(pid, 1000);
    }

    static {
        terminalPIDs = new HashMap();
    }
}

