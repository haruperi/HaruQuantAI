/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.MassImportDataInfo
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Files.job;

import com.strategyquant.datalib.data.io.MassImportDataInfo;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.plugin.DataSource.impl.Files.job.DataMassImporter;
import java.io.File;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataMassImporterChildrenJob
extends GridJob<String> {
    public static final Logger Log = LoggerFactory.getLogger(DataMassImporterChildrenJob.class);
    private static final long serialVersionUID = 1L;
    private DataMassImporter importer;
    private File file;

    public DataMassImporterChildrenJob(String jobId, File file, MassImportDataInfo importInfo, Set<String> existingSymbols) {
        super(jobId, 0, null);
        this.file = file;
        this.importer = new DataMassImporter(importInfo, file, existingSymbols);
    }

    public String call() throws Exception {
        try {
            return this.importer.performImport();
        }
        catch (Exception e) {
            Log.error("Error while importing file: " + this.file.getName(), (Throwable)e);
            throw e;
        }
    }

    public void messageReceived(GridMessage message) {
        super.messageReceived(message);
        switch (message.getMessageID()) {
            case 4: {
                this.importer.cancel();
            }
        }
    }
}

