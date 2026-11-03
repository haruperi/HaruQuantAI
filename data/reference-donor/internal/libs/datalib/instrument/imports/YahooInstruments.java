/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.instrument.imports;

import com.strategyquant.datalib.instrument.InstrumentManager;
import java.io.BufferedReader;
import java.io.FileReader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class YahooInstruments {
    public static final Logger Log = LoggerFactory.getLogger(YahooInstruments.class);

    public void checkData(String string) throws Exception {
        BufferedReader bufferedReader = null;
        String string2 = "";
        try {
            bufferedReader = new BufferedReader(new FileReader(string));
            while ((string2 = bufferedReader.readLine()) != null) {
                String[] stringArray = string2.split(",", -1);
                String string3 = stringArray[0].replaceAll("\\\"", "");
                String string4 = stringArray[1].replaceAll("\\\"", "");
                String string5 = stringArray[2].replaceAll("\\\"", "");
            }
        }
        catch (Exception exception) {
            throw new Exception("File contains incorrect data. Line: " + string2);
        }
        finally {
            if (bufferedReader != null) {
                try {
                    bufferedReader.close();
                }
                catch (Exception exception) {
                    Log.error("Exc.", (Throwable)exception);
                }
            }
        }
    }

    public void importData(byte by, String string) throws Exception {
        BufferedReader bufferedReader = null;
        String string2 = "";
        try {
            bufferedReader = new BufferedReader(new FileReader(string));
            bufferedReader.readLine();
            while ((string2 = bufferedReader.readLine()) != null) {
                String[] stringArray = string2.split(",", -1);
                String string3 = stringArray[0].replaceAll("\\\"", "").trim();
                String string4 = stringArray[1].replaceAll("\\\"", "").trim();
                String string5 = stringArray[2].replaceAll("\\\"", "").trim();
                if (InstrumentManager.checkInstrumentExists(string3)) continue;
                InstrumentManager.addInstrument(string3, string4, 1.0, 0.01, 0.01, 0.0, 0.0, "<Method type=\"None\" use=\"true\"><Params/></Method>", by, string5, null, null, null, 1.0, 0.0);
                Log.info("Added instrument " + string3 + " | " + string4 + " | " + string5);
            }
        }
        catch (Exception exception) {
            throw exception;
        }
        finally {
            if (bufferedReader != null) {
                try {
                    bufferedReader.close();
                }
                catch (Exception exception) {
                    Log.error("Exc.", (Throwable)exception);
                }
            }
        }
    }
}

