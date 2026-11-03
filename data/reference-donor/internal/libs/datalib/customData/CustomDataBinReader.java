/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.customData;

import com.strategyquant.datalib.customData.CustomData;
import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import java.io.DataInputStream;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;

public class CustomDataBinReader {
    DataInputStream reader = null;
    private String fileName;
    public CustomData loadedData;

    public CustomDataBinReader(CustomDataInfo customDataInfo) {
        this.loadedData = new CustomData(customDataInfo.values);
        this.fileName = CustomDataManager.getDataFileName(customDataInfo.name);
    }

    public void open() throws Exception {
        try {
            this.reader = new DataInputStream(new FileInputStream(this.fileName));
        }
        catch (FileNotFoundException fileNotFoundException) {
            throw new Exception("File not found: " + this.fileName);
        }
    }

    public void close() throws Exception {
        try {
            if (this.reader != null) {
                this.reader.close();
                this.reader = null;
            }
        }
        catch (IOException iOException) {
            throw new Exception("Cannot close file");
        }
    }

    public boolean hasNextData() throws Exception {
        if (this.reader == null) {
            throw new Exception("You have to call CustomDataBinReader.open() method first!");
        }
        return this.reader.available() > 0;
    }

    public void loadData() throws Exception {
        this.loadedData.time = this.reader.readLong();
        for (int i = 0; i < this.loadedData.values.length; ++i) {
            this.loadedData.values[i] = this.reader.readDouble();
        }
    }
}

