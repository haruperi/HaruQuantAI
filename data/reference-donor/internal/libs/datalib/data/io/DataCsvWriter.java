/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.time.SQTimeOld
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.time.SQTimeOld;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;

public class DataCsvWriter {
    protected PrintWriter writer;
    protected String fileName;
    protected String timeframe;

    public DataCsvWriter(String string, String string2) {
        this.fileName = string2;
        this.timeframe = string;
    }

    public void openFile() throws Exception {
        try {
            File file = new File(this.fileName);
            if (!file.getParentFile().exists()) {
                file.getParentFile().mkdirs();
                file.createNewFile();
            }
            this.writer = new PrintWriter(new BufferedWriter(new FileWriter(file, StandardCharsets.UTF_8)));
        }
        catch (FileNotFoundException fileNotFoundException) {
            throw new Exception("File not found: " + this.fileName);
        }
    }

    public void closeFile() {
        this.writer.close();
    }

    public void write(VersatileData versatileData) throws IOException {
        if (versatileData.type == 1) {
            this.writeTickData(versatileData);
        } else {
            this.writeOHLCData(versatileData);
        }
    }

    private void writeOHLCData(VersatileData versatileData) {
        SQTimeOld sQTimeOld = new SQTimeOld(versatileData.time);
        this.writer.println(sQTimeOld.formatDate() + "," + sQTimeOld.formatTime() + "," + versatileData.open + "," + versatileData.high + "," + versatileData.low + "," + versatileData.close + "," + versatileData.volume);
    }

    private void writeTickData(VersatileData versatileData) {
        SQTimeOld sQTimeOld = new SQTimeOld(versatileData.time);
        this.writer.println(sQTimeOld.toString() + "," + versatileData.ask + "," + versatileData.bid + "," + versatileData.volume);
    }
}

