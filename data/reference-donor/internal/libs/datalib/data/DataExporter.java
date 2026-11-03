/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.app.MainApp
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 */
package com.strategyquant.datalib.data;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.app.MainApp;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.FileAttribute;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;

public class DataExporter {
    private static final DateTimeFormatter formaterDate = DateTimeFormat.forPattern((String)"yyyy_MM_dd");
    private long fromDate;
    private long toDate;
    private DataBinReaderNew reader;
    private String folder;
    private String symbol;
    private int dateType;
    private DataInfo info;
    private String tmpFolder;

    public void exportTick(String string, long l, long l2, String string2) throws Exception {
        DataInfo dataInfo = DataManager.getDataInfo("History", string);
        this.folder = string2 + "//" + dataInfo.instrument;
        this.symbol = string;
        File file = new File(this.folder);
        file.mkdirs();
        this.fromDate = l > 0L ? SQTime.correctDayStart((long)l) : 0L;
        this.toDate = l2 > 0L ? SQTime.correctDayEnd((long)l2) : 0L;
        this.prepareReader(string, "TICK");
        this.performExport();
    }

    public void exportM1(String string, long l, long l2, String string2) throws Exception {
        DataInfo dataInfo = DataManager.getDataInfo("History", string);
        this.folder = string2 + "//" + dataInfo.instrument;
        this.symbol = string;
        File file = new File(this.folder);
        file.mkdirs();
        this.fromDate = l > 0L ? SQTime.correctDayStart((long)l) : 0L;
        this.toDate = l2 > 0L ? SQTime.correctDayEnd((long)l2) : 0L;
        this.prepareReader(string, "M1");
        this.performExport();
    }

    private void performExport() throws Exception {
        Path path = Files.createTempDirectory("sq4_export", new FileAttribute[0]);
        this.tmpFolder = path.toString();
        DataBinWriterNew dataBinWriterNew = null;
        int n = -1;
        while (this.reader.readData()) {
            VersatileData versatileData = this.reader.tickData;
            long l = versatileData.time;
            if (this.toDate > 0L && l > this.toDate) break;
            if (this.fromDate != 0L && l < this.fromDate) continue;
            int n2 = SQTime.getDayOfYear((long)l);
            if (n2 != n) {
                if (dataBinWriterNew != null && dataBinWriterNew != null) {
                    this.close(dataBinWriterNew);
                }
                dataBinWriterNew = this.prepareWriter(formaterDate.print(l) + ".dat", this.dateType);
                n = n2;
            }
            dataBinWriterNew.writeData(versatileData);
        }
        if (dataBinWriterNew != null) {
            this.close(dataBinWriterNew);
        }
        this.reader.closeFile();
        this.deleteFolder(path.toFile());
    }

    private void deleteFolder(File file) {
        String[] stringArray;
        for (String string : stringArray = file.list()) {
            File file2 = new File(file.getPath(), string);
            file2.delete();
        }
        file.delete();
    }

    private void close(DataBinWriterNew dataBinWriterNew) throws Exception {
        int n;
        dataBinWriterNew.close();
        String string = dataBinWriterNew.getFileName();
        String string2 = new File(string).getName();
        int n2 = string2.length();
        string2 = string2.substring(0, n2 - 4);
        FileOutputStream fileOutputStream = new FileOutputStream(this.folder + "//" + string2 + ".zip");
        ZipOutputStream zipOutputStream = new ZipOutputStream(fileOutputStream);
        ZipEntry zipEntry = new ZipEntry(string2 + ".dat");
        zipOutputStream.putNextEntry(zipEntry);
        FileInputStream fileInputStream = new FileInputStream(string);
        byte[] byArray = new byte[2048];
        while ((n = fileInputStream.read(byArray)) > 0) {
            zipOutputStream.write(byArray, 0, n);
        }
        fileInputStream.close();
        zipOutputStream.closeEntry();
        zipOutputStream.close();
    }

    private DataBinWriterNew prepareWriter(String string, int n) throws Exception {
        DataBinWriterNew dataBinWriterNew = DataBinWriterNew.getInstance(n, MainApp.getDataPath(), this.info.symbolInfo);
        dataBinWriterNew.setFileName(this.tmpFolder + "/" + string);
        dataBinWriterNew.open();
        return dataBinWriterNew;
    }

    private void prepareReader(String string, String string2) throws Exception {
        String string3 = DataManager.getDataFileName("History", string, string2, "No Session");
        this.dateType = string2.equals("TICK") ? 2 : 1;
        this.info = DataManager.getDataInfo("History", string);
        this.reader = DataBinReaderNew.getInstance(this.dateType, this.info.symbolInfo);
        this.reader.setFileName(string3);
        this.reader.openFile();
        DataManager.checkDataExport(this.reader, this.info.source);
    }
}

