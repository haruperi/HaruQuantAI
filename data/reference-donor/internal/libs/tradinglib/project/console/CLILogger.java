/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.console;

import com.strategyquant.lib.SQTime;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.io.Writer;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CLILogger {
    private static final Logger Log = LoggerFactory.getLogger(CLILogger.class);
    public static final String Separator = "--------------------------------------------------";
    private PrintWriter writer;
    private static CLILogger instance;
    public static String lastCommandOutput;

    public static CLILogger getInstance() {
        if (instance == null) {
            instance = new CLILogger();
        }
        return instance;
    }

    public static void redirectOutputToFile(String string) throws Exception {
        CLILogger cLILogger = CLILogger.getInstance();
        if (string == null) {
            CLILogger.closeFile();
            return;
        }
        try {
            File file = new File(string);
            if (file.getParentFile() != null && !file.getParentFile().exists()) {
                file.getParentFile().mkdirs();
            }
            cLILogger.writer = new PrintWriter((Writer)new BufferedWriter(new FileWriter(file, true)), true);
        }
        catch (Exception exception) {
            Log.error(String.format("Cannot redirect output to file. Reason: %s", exception.getMessage()));
            throw new Exception(String.format("Cannot redirect output to file. Reason: %s", exception.getMessage()));
        }
    }

    public static void closeFile() {
        CLILogger cLILogger = CLILogger.getInstance();
        if (cLILogger.writer == null) {
            return;
        }
        try {
            cLILogger.writer.flush();
            cLILogger.writer.close();
        }
        catch (Exception exception) {
            // empty catch block
        }
        cLILogger.writer = null;
    }

    public static void log(String string, String string2, int n) {
        StringBuilder stringBuilder = new StringBuilder();
        int n2 = n - string.length() - string2.length();
        stringBuilder.append(string);
        for (int i = 0; i < n2; ++i) {
            stringBuilder.append(" ");
        }
        stringBuilder.append(string2);
        CLILogger.log(stringBuilder.toString(), false);
    }

    public static void log(String string, boolean bl) {
        if (string.equals("{}") || string.trim().isEmpty()) {
            return;
        }
        string = string.replaceAll(Pattern.quote("<br>"), "\n");
        CLILogger cLILogger = CLILogger.getInstance();
        if (bl) {
            string = SQTime.getLogTime((boolean)false, (boolean)false) + " " + string + "\n" + Separator;
        }
        lastCommandOutput = lastCommandOutput + string + "\n";
        if (cLILogger.writer != null) {
            cLILogger.writer.println(string);
        } else {
            Log.info(string);
        }
    }

    public static void log(String string) {
        CLILogger.log(string, false);
    }
}

