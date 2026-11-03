/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.tradinglib.data.AppDataImporter
 */
package com.strategyquant.plugin.DataSource.impl.Files.job;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.tradinglib.data.AppDataImporter;

public class DataAppImporterJob
extends GridJob<Void> {
    private AppDataImporter importer;

    public DataAppImporterJob(String jobId, String path, String license) {
        super(jobId, 0, null);
        this.importer = new AppDataImporter(path, license);
    }

    public Void call() throws Exception {
        this.importer.start();
        return null;
    }

    public String validate() {
        return this.importer.validate();
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

