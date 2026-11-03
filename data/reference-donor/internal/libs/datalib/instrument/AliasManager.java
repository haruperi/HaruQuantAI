/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.constants.SQPaths
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.instrument;

import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.instrument.InstrumentAlias;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.constants.SQPaths;
import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AliasManager {
    private static final Logger Log = LoggerFactory.getLogger((String)"AliasManager");
    private static final String filePath = SQPaths.settingsDirPath + "/aliases.txt";
    private static final String lineDelimiter = "\n";
    private static final String valueDelimiter = "#";
    private static AliasManager instance;
    private ArrayList<InstrumentAlias> aliases;

    private AliasManager() {
        this.load();
        instance = this;
    }

    private static synchronized AliasManager get() {
        return instance != null ? instance : new AliasManager();
    }

    public static ArrayList<InstrumentAlias> getAliases() {
        return AliasManager.get().aliases;
    }

    public static InstrumentAlias getAlias(String string) {
        for (int i = 0; i < AliasManager.get().aliases.size(); ++i) {
            InstrumentAlias instrumentAlias = AliasManager.get().aliases.get(i);
            if (!instrumentAlias.alias.equals(string)) continue;
            return instrumentAlias;
        }
        return null;
    }

    public static boolean checkAliasExists(String string) {
        return AliasManager.getAlias(string) != null;
    }

    public static String getAliasInstrument(String string) {
        InstrumentAlias instrumentAlias = AliasManager.getAlias(string);
        return instrumentAlias != null ? instrumentAlias.instrument : null;
    }

    public static ArrayList<InstrumentAlias> listInstrumentAliases(String string) {
        ArrayList<InstrumentAlias> arrayList = new ArrayList<InstrumentAlias>();
        for (int i = 0; i < AliasManager.get().aliases.size(); ++i) {
            InstrumentAlias instrumentAlias = AliasManager.get().aliases.get(i);
            if (!instrumentAlias.instrument.equals(string)) continue;
            arrayList.add(instrumentAlias);
        }
        return arrayList;
    }

    public static void removeInstrumentAliases(String string) {
        for (int i = AliasManager.get().aliases.size() - 1; i >= 0; --i) {
            InstrumentAlias instrumentAlias = AliasManager.get().aliases.get(i);
            if (!instrumentAlias.instrument.equals(string)) continue;
            AliasManager.get().aliases.remove(i);
        }
        AliasManager.save();
    }

    public static void addAlias(String string, String string2, String string3) throws DataException {
        if (AliasManager.checkAliasExists(string)) {
            throw new DataException(3, "DB: Alias '" + string + "' already exists.");
        }
        AliasManager.get().aliases.add(new InstrumentAlias(string, string2, string3));
        AliasManager.save();
    }

    public static void updateAlias(String string, String string2, String string3) throws DataException {
        if (!AliasManager.checkAliasExists(string2)) {
            throw new DataException(3, "Alias '" + string2 + "' doesn't exist.");
        }
        InstrumentAlias instrumentAlias = AliasManager.getAlias(string2);
        instrumentAlias.instrument = string;
        instrumentAlias.description = string3;
        AliasManager.save();
    }

    public static void removeAlias(String string) throws DataException {
        if (!AliasManager.checkAliasExists(string)) {
            throw new DataException(3, "Alias '" + string + "' doesn't exist.");
        }
        InstrumentAlias instrumentAlias = AliasManager.getAlias(string);
        AliasManager.get().aliases.remove(instrumentAlias);
        AliasManager.save();
    }

    private void load() {
        this.aliases = new ArrayList();
        File file = new File(filePath);
        if (!file.exists()) {
            AliasManager.tryCreateFile(file);
            return;
        }
        try {
            String[] stringArray = SQUtils.fileToString((File)file).split(lineDelimiter);
            for (int i = 0; i < stringArray.length; ++i) {
                String string = stringArray[i];
                try {
                    String[] stringArray2 = string.split(valueDelimiter);
                    if (stringArray2.length < 2) continue;
                    String string2 = stringArray2.length == 3 ? stringArray2[2] : "";
                    String string3 = stringArray2[0].trim();
                    String string4 = stringArray2[1].trim();
                    if (!InstrumentManager.checkInstrumentExists(string4, true)) continue;
                    this.aliases.add(new InstrumentAlias(string3, string4, string2));
                    continue;
                }
                catch (Exception exception) {
                    // empty catch block
                }
            }
        }
        catch (Exception exception) {
            Log.error("Error while loading aliases. ", (Throwable)exception);
        }
    }

    private static void save() {
        File file = new File(filePath);
        if (!file.exists()) {
            AliasManager.tryCreateFile(file);
        }
        PrintWriter printWriter = null;
        String string = "";
        try {
            printWriter = new PrintWriter(new File(filePath));
            for (int i = 0; i < AliasManager.get().aliases.size(); ++i) {
                InstrumentAlias instrumentAlias = AliasManager.get().aliases.get(i);
                string = instrumentAlias.alias + valueDelimiter + instrumentAlias.instrument + valueDelimiter + instrumentAlias.description + lineDelimiter;
                printWriter.print(string);
            }
            printWriter.flush();
            printWriter.close();
        }
        catch (Exception exception) {
            if (printWriter != null) {
                printWriter.close();
            }
            Log.error("Cannot save aliases settings.", (Throwable)exception);
        }
    }

    private static void tryCreateFile(File file) {
        File file2 = file.getParentFile();
        if (file2 != null) {
            file2.mkdirs();
            try {
                file.createNewFile();
            }
            catch (IOException iOException) {
                Log.error("Cannot create settings file '" + filePath + "'", (Throwable)iOException);
            }
        }
    }
}

