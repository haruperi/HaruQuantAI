/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.mql;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import java.io.File;
import java.nio.file.CopyOption;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.concurrent.TimeUnit;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MQLMarketConverter {
    public static final Logger Log = LoggerFactory.getLogger(MQLMarketConverter.class);
    private static final String iCustomStr = "iCustom";
    private static final String volumeCheckFn = " bool CheckVolumeValue(double volume)\r\n  {\r\n//--- minimal allowed volume for trade operations\r\n   double min_volume=SymbolInfoDouble(Symbol(),SYMBOL_VOLUME_MIN);\r\n   if(volume<min_volume)\r\n     {\r\n      Verbose(StringFormat(\"Volume is less than the minimal allowed SYMBOL_VOLUME_MIN=%.2f\",min_volume));\r\n      return(false);\r\n     }\r\n\r\n//--- maximal allowed volume of trade operations\r\n   double max_volume=SymbolInfoDouble(Symbol(),SYMBOL_VOLUME_MAX);\r\n   if(volume>max_volume)\r\n     {\r\n      Verbose(StringFormat(\"Volume is greater than the maximal allowed SYMBOL_VOLUME_MAX=%.2f\",max_volume));\r\n      return(false);\r\n     }\r\n\r\n//--- get minimal step of volume changing\r\n   double volume_step=SymbolInfoDouble(Symbol(),SYMBOL_VOLUME_STEP);\r\n\r\n   int ratio=(int)MathRound(volume/volume_step);\r\n   if(MathAbs(ratio*volume_step-volume)>0.0000001)\r\n     {\r\n      Verbose(StringFormat(\"Volume is not a multiple of the minimal step SYMBOL_VOLUME_STEP=%.2f, the closest correct volume is %.2f\",\r\n                               volume_step,ratio*volume_step));\r\n      return(false);\r\n     }\r\n   return(true);\r\n  }";

    public static String generateMT4SourceCode(String string, String string2, String string3, String string4, String string5) throws Exception {
        Log.info("Generating MT4 source code for MQL market...");
        return MQLMarketConverter.generateMTSourceCode(string, false, string2, string3, string4, string5);
    }

    public static String generateMT5SourceCode(String string, String string2, String string3, String string4, String string5) throws Exception {
        Log.info("Generating MT5 source code for MQL market...");
        return MQLMarketConverter.generateMTSourceCode(string, true, string2, string3, string4, string5);
    }

    private static String generateMTSourceCode(String string, boolean bl, String string2, String string3, String string4, String string5) throws Exception {
        String string6;
        int n;
        int n2 = string.indexOf("#property");
        if (n2 < 0) {
            n2 = 0;
        }
        string = string.replaceAll("(?m)^#property.*", "");
        String[] stringArray = new String[]{"copyright", "link", "version", "description"};
        String[] stringArray2 = new String[]{string2, string3, string4, string5};
        String string7 = "";
        for (int i = 0; i < stringArray.length; ++i) {
            string7 = string7 + "#property " + stringArray[i] + " \"" + stringArray2[i] + "\"\n";
        }
        string7 = string7 + "#property strict\n";
        string = string.substring(0, n2) + string7 + string.substring(n2);
        String string8 = bl ? "" : "extern ";
        string = string.replace(string8 + "bool sqDisplayInfoPanel = true;", "bool sqDisplayInfoPanel = false;");
        ArrayList<String> arrayList = MQLMarketConverter.getUsedIndicators(string);
        String string9 = "\n";
        int n3 = string.indexOf("#property strict") + "#property strict".length();
        if (n3 < 0) {
            throw new Exception("Cannot add resources into the EA code - #property strict line not found");
        }
        for (n = 0; n < arrayList.size(); ++n) {
            string6 = arrayList.get(n) + "." + (bl ? "ex5" : "ex4");
            string9 = string9 + "\n#resource \"" + string6 + "\"";
            string = string.replace("\"" + arrayList.get(n) + "\"", "\"::" + string6 + "\"");
        }
        n = (string = string.substring(0, n3) + string9 + string.substring(n3)).indexOf(bl ? "ulong openPosition(" : "int sqOpenOrder(");
        if (n < 0) {
            throw new Exception("Cannot find " + (bl ? "openPosition" : "sqOpenOrder") + " function");
        }
        string6 = string.substring(0, n);
        String string10 = string.substring(n);
        string6 = string6 + " bool CheckVolumeValue(double volume)\r\n  {\r\n//--- minimal allowed volume for trade operations\r\n   double min_volume=SymbolInfoDouble(Symbol(),SYMBOL_VOLUME_MIN);\r\n   if(volume<min_volume)\r\n     {\r\n      Verbose(StringFormat(\"Volume is less than the minimal allowed SYMBOL_VOLUME_MIN=%.2f\",min_volume));\r\n      return(false);\r\n     }\r\n\r\n//--- maximal allowed volume of trade operations\r\n   double max_volume=SymbolInfoDouble(Symbol(),SYMBOL_VOLUME_MAX);\r\n   if(volume>max_volume)\r\n     {\r\n      Verbose(StringFormat(\"Volume is greater than the maximal allowed SYMBOL_VOLUME_MAX=%.2f\",max_volume));\r\n      return(false);\r\n     }\r\n\r\n//--- get minimal step of volume changing\r\n   double volume_step=SymbolInfoDouble(Symbol(),SYMBOL_VOLUME_STEP);\r\n\r\n   int ratio=(int)MathRound(volume/volume_step);\r\n   if(MathAbs(ratio*volume_step-volume)>0.0000001)\r\n     {\r\n      Verbose(StringFormat(\"Volume is not a multiple of the minimal step SYMBOL_VOLUME_STEP=%.2f, the closest correct volume is %.2f\",\r\n                               volume_step,ratio*volume_step));\r\n      return(false);\r\n     }\r\n   return(true);\r\n  }\n";
        string10 = bl ? string10.replace("if(volume <= 0) return (0);", "if(volume <= 0 || !CheckVolumeValue(volume)) return (0);") : string10.replace("if(size <= 0) return (0);", "if(size <= 0 || !CheckVolumeValue(size)) return (0);");
        string = string6 + string10;
        return string;
    }

    public static String lockMT4(String string, double d, boolean bl, String string2, int n) throws Exception {
        int n2;
        if (d > 0.0) {
            n2 = string.indexOf("extern double mmLots");
            if (n2 < 0) {
                throw new Exception("mmLots setting not found");
            }
            int n3 = string.indexOf(";", n2);
            if (n3 < 0) {
                throw new Exception("Cannot find the end of mmLots line");
            }
            string = string.substring(0, n2) + "double mmLots = " + d + ";" + string.substring(n3 + 1);
        }
        if ((n2 = string.indexOf("VerboseLog(\"Starting the EA\");")) < 0) {
            throw new Exception("Lock begin position not found");
        }
        String string3 = string.substring(0, (n2 += "VerboseLog(\"Starting the EA\");".length()) + 1);
        String string4 = string.substring(n2);
        if (bl) {
            string3 = string3 + "\nif(!IsDemo()){ VerboseLog(\"This EA can trade only on demo accounts!\"); return(INIT_FAILED); }";
        }
        if (string2 != null) {
            int n4 = string3.indexOf("void OnTick() {");
            if (n4 < 0) {
                throw new Exception("OnTick function not found");
            }
            String string5 = "if(iTime(NULL, 0, 0) >= StringToTime(\"" + string2 + "\")){ Alert(\"This EA is allowed to trade only until " + string2 + "!\"); ExpertRemove(); return; }";
            string3 = string3.substring(0, n4 += "void OnTick() {".length()) + "\n" + string5 + string3.substring(n4);
        }
        if (n > 0) {
            String string6 = "if(AccountNumber() != " + n + "){ VerboseLog(\"This EA is locked to account " + n + "!\"); return(INIT_FAILED); };";
            string3 = string3 + "\n" + string6;
        }
        return string3 + string4;
    }

    public static String lockMT5(String string, double d, boolean bl, String string2, int n) throws Exception {
        int n2;
        if (d > 0.0) {
            n2 = string.indexOf("input double mmLots");
            if (n2 < 0) {
                throw new Exception("mmLots setting not found");
            }
            int n3 = string.indexOf(";", n2);
            if (n3 < 0) {
                throw new Exception("Cannot find the end of mmLots line");
            }
            string = string.substring(0, n2) + "double mmLots = " + d + ";" + string.substring(n3 + 1);
        }
        if ((n2 = string.indexOf("VerboseLog(\"Starting the EA\");")) < 0) {
            throw new Exception("Lock begin position not found");
        }
        String string3 = string.substring(0, (n2 += "VerboseLog(\"Starting the EA\");".length()) + 1);
        String string4 = string.substring(n2);
        if (bl) {
            string3 = string3 + "\nif(AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO){ VerboseLog(\"This EA can trade only on demo accounts!\"); return(INIT_FAILED); }";
        }
        if (string2 != null) {
            int n4 = string3.indexOf("void OnTick() {");
            if (n4 < 0) {
                throw new Exception("OnTick function not found");
            }
            String string5 = "if(getTime(0) >= StringToTime(\"" + string2 + "\")){ Alert(\"This EA is allowed to trade only until " + string2 + "!\"); ExpertRemove(); return; }";
            string3 = string3.substring(0, n4 += "void OnTick() {".length()) + "\n" + string5 + string3.substring(n4);
        }
        if (n > 0) {
            String string6 = "if(AccountInfoInteger(ACCOUNT_LOGIN) != " + n + "){ VerboseLog(\"This EA is locked to account " + n + "!\"); return(INIT_FAILED); };";
            string3 = string3 + "\n" + string6;
        }
        return string3 + string4;
    }

    public static void compileMT4EA(String string, String string2, String string3, String string4) throws Exception {
        MQLMarketConverter.compileEA(string, false, string2, string3, string4);
    }

    public static void compileMT5EA(String string, String string2, String string3, String string4) throws Exception {
        MQLMarketConverter.compileEA(string, true, string2, string3, string4);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private static void compileEA(String string, boolean bl, String string2, String string3, String string4) throws Exception {
        File file = null;
        Log.info("Compiling MQL Market MT4 EA..");
        Log.info(" - mtExpertsPath: " + string2);
        Log.info(" - mtInstallPath: " + string3);
        Log.info(" - eaName: " + string4);
        String string5 = bl ? "mq5" : "mq4";
        String string6 = bl ? "ex5" : "ex4";
        try {
            String string7;
            Object object;
            if (string4.endsWith("." + string6)) {
                string4 = string4.replace("." + string6, "");
            }
            if (!new File(string2).exists()) {
                throw new Exception("Selected experts path (" + string2 + ") does not exist");
            }
            file = new File(string2 + "/" + string4 + "_temp");
            if (!file.exists() && !file.mkdirs()) {
                throw new Exception("Cannot create temp folder in experts directory");
            }
            File file2 = new File(MainApp.getDataPath() + "custom_indicators/" + (bl ? "MetaTrader5" : "MetaTrader4") + "/Indicators/");
            if (!file2.exists()) {
                throw new Exception("SQ Indicators folder '" + file2.getAbsolutePath() + "' not found");
            }
            File[] fileArray = file2.listFiles();
            for (int i = 0; i < fileArray.length; ++i) {
                object = fileArray[i];
                string7 = ((File)object).getName();
                Log.info("Copying indicator " + ((File)object).getName() + "...");
                Files.copy(((File)object).toPath(), new File(file.getAbsolutePath() + "/" + string7).toPath(), new CopyOption[0]);
            }
            String string8 = file.getAbsolutePath() + "/" + string4 + "." + string5;
            SQUtils.stringToFile((String)string8, (String)string);
            object = string3 + "/metaeditor.exe";
            if (!new File((String)object).exists() && !new File((String)(object = string3 + "/metaeditor64.exe")).exists()) {
                throw new Exception("Metaeditor not found. Please check if MetaTrader installation folder path is correct");
            }
            string7 = (String)object + " /compile:\"" + string8 + "\" /log";
            Log.info("---- Running command: " + string7);
            Process process = Runtime.getRuntime().exec(string7);
            if (!process.waitFor(60L, TimeUnit.SECONDS)) {
                Log.error("Command '" + string7 + "' failed!");
                throw new Exception("MQL Generation TIMED OUT (compile command)");
            }
            File file3 = new File(file.getAbsolutePath() + "/" + string4 + "." + string6);
            if (!file3.exists()) {
                throw new Exception("EA compilation failed - target file doesn't exist");
            }
            Files.copy(file3.toPath(), new File(string2 + "/" + string4 + "." + string6).toPath(), new CopyOption[0]);
            Log.info("MQL Market EA created successfully");
        }
        finally {
            if (file != null && !SQUtils.deleteDirectory((String)file.getAbsolutePath())) {
                Log.warn("Temp directory was not fully removed");
            }
        }
    }

    private static ArrayList<String> getUsedIndicators(String string) {
        int n;
        if (string == null) {
            return null;
        }
        ArrayList<String> arrayList = new ArrayList<String>();
        int n2 = string.indexOf(iCustomStr, 0);
        while (n2 > 0 && (n = string.indexOf("(", n2)) >= 0) {
            int n3 = Math.min(n2 + 100, string.length() - 1);
            String string2 = string.substring(n, n3);
            String[] stringArray = string2.split(",");
            String string3 = stringArray[2].trim().substring(1);
            if ((n3 = string3.indexOf("\"")) < 0) break;
            if (!arrayList.contains(string3 = string3.substring(0, n3).replace("'", ""))) {
                arrayList.add(string3);
            }
            n2 = string.indexOf(iCustomStr, n2 + 1);
        }
        return arrayList;
    }
}

