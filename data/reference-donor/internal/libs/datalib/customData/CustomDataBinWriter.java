/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.customData;

import com.strategyquant.datalib.customData.CustomData;
import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;

public class CustomDataBinWriter {
    protected DataOutputStream writer = null;
    private String fileName;

    public void setFileName(String string) {
        this.fileName = string;
    }

    public String getFileName() {
        return this.fileName;
    }

    public void open() throws Exception {
        try {
            File file = new File(this.fileName);
            if (!file.exists()) {
                file.getParentFile().mkdirs();
            }
            this.writer = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(this.fileName)));
        }
        catch (FileNotFoundException fileNotFoundException) {
            throw new Exception("File not found: " + this.fileName);
        }
    }

    public void close() throws Exception {
        try {
            if (this.writer != null) {
                this.writer.flush();
                this.writer.close();
                this.writer = null;
            }
        }
        catch (IOException iOException) {
            throw new Exception("Cannot close file");
        }
    }

    public void writeData(CustomData customData) throws Exception {
        if (this.writer == null) {
            throw new Exception("You have to call CustomDataBinWriter.open() method first!");
        }
        this.writer.writeLong(customData.time);
        for (int i = 0; i < customData.values.length; ++i) {
            this.writer.writeDouble(customData.values[i]);
        }
    }
}

