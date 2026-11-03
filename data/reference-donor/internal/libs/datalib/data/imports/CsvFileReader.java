/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.datalib.data.imports;

import com.strategyquant.datalib.data.imports.Separators;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.lib.L;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.regex.PatternSyntaxException;

public class CsvFileReader {
    private ImportDataInfo importInfo;

    public CsvFileReader(ImportDataInfo importDataInfo) {
        this.importInfo = importDataInfo;
    }

    public int getDigitsCount(String string) {
        int n = 0;
        for (char c : string.toCharArray()) {
            if (!Character.isDigit(c)) continue;
            ++n;
        }
        return n;
    }

    public int getAlphabeticsCount(String string) {
        int n = 0;
        for (char c : string.toCharArray()) {
            if (Character.isDigit(c)) continue;
            ++n;
        }
        return n;
    }

    /*
     * Loose catch block
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    public String[][] read(Boolean bl) throws Exception {
        this.importInfo.resetLastAskBid();
        BufferedReader bufferedReader = null;
        String string = null;
        String[][] stringArray = null;
        String[] stringArray2 = null;
        boolean bl2 = true;
        int n = 0;
        int n2 = 0;
        String[] stringArray3 = new String[this.importInfo.rowCount];
        try {
            File file = new File(this.importInfo.filePath);
            bufferedReader = new BufferedReader(new FileReader(file));
        }
        catch (FileNotFoundException fileNotFoundException) {
            throw new Exception("File not found: " + this.importInfo.filePath);
        }
        try {
            while ((string = bufferedReader.readLine()) != null) {
                string = string.replaceAll("( +)", " ").trim();
                if (bl.booleanValue() && this.getDigitsCount(string) < this.getAlphabeticsCount(string) && n2 == 0) {
                    ++this.importInfo.skipRows;
                }
                if (n < this.importInfo.skipRows) {
                    ++n;
                    continue;
                }
                if (n2 >= this.importInfo.rowCount) break;
                stringArray3[n2] = string;
                ++n2;
            }
            if (bl.booleanValue()) {
                this.importInfo.separator = CsvFileReader.findSeparator(stringArray3, this.importInfo.skipRows);
            }
            n2 = 0;
            for (int i = 0; i < stringArray3.length && (string = stringArray3[i]) != null; ++i) {
                stringArray2 = string.split(this.importInfo.separator);
                if (this.importInfo.isMT5TickImport() && (stringArray2 = this.importInfo.correctMT5TickData(stringArray2)) == null) continue;
                if (stringArray2.length > this.importInfo.skipCols) {
                    int n3;
                    if (bl2) {
                        if (stringArray2.length - this.importInfo.skipCols <= 0) {
                            throw new Exception();
                        }
                        n3 = 0;
                        for (int j = 0; j < stringArray3.length && stringArray3[j] != null; ++n3, ++j) {
                        }
                        stringArray = new String[n3][stringArray2.length - this.importInfo.skipCols];
                        bl2 = false;
                    }
                    for (n3 = this.importInfo.skipCols; n3 < stringArray2.length; ++n3) {
                        stringArray[n2][n3 - this.importInfo.skipCols] = stringArray2[n3];
                    }
                    ++n2;
                    continue;
                }
                break;
            }
        }
        catch (PatternSyntaxException patternSyntaxException) {
            try {
                throw patternSyntaxException;
                catch (Exception exception) {
                    if (string != null && string.length() > 100) {
                        string = string.substring(0, 100) + "...";
                    }
                    throw new Exception(L.t((String)"Error parsing on line %d. Incorrect file format?\nLine contents: %s", (Object[])new Object[]{this.importInfo.skipRows + n2, string}));
                }
            }
            catch (Throwable throwable) {
                try {
                    if (bufferedReader == null) throw throwable;
                    bufferedReader.close();
                    throw throwable;
                }
                catch (IOException iOException) {
                    throw new Exception(L.t((String)"Cannot close file :%s", (Object[])new Object[]{this.importInfo.filePath}));
                }
            }
        }
        try {
            if (bufferedReader == null) return stringArray;
            bufferedReader.close();
            return stringArray;
        }
        catch (IOException iOException) {
            throw new Exception(L.t((String)"Cannot close file :%s", (Object[])new Object[]{this.importInfo.filePath}));
        }
    }

    public static String findSeparator(String[] stringArray, int n) throws Exception {
        String[] stringArray2 = Separators.listValues();
        String string = null;
        String string2 = null;
        int n2 = 0;
        int n3 = 0;
        try {
            for (n3 = 0; n3 < stringArray.length && (string = stringArray[n3]) != null; ++n3) {
                for (int i = 0; i < stringArray2.length; ++i) {
                    if (string.split(stringArray2[i]).length <= n2) continue;
                    n2 = string.split(stringArray2[i]).length;
                    string2 = stringArray2[i];
                }
            }
            if (string2 == null) {
                string2 = stringArray2[0];
            }
            return string2;
        }
        catch (PatternSyntaxException patternSyntaxException) {
            if (string != null && string.length() > 100) {
                string = string.substring(0, 100) + "...";
            }
            throw new Exception(L.t((String)"Error parsing on line %d. Incorrect file format?\nLine contents: %s", (Object[])new Object[]{n + n3, string}));
        }
    }

    public String getSeparator() {
        return this.importInfo.separator;
    }

    public String getDateFormat() {
        return this.importInfo.dateFormat;
    }
}

