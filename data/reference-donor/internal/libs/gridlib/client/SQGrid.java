/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 */
package com.strategyquant.gridlib.client;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.config.Config;
import java.io.IOException;
import javax.jms.JMSException;

public class SQGrid {
    private static SQGrid instance;
    private GridClient gridClient;

    public static void init(Config config) throws Exception {
        SQGrid.init(new GridClient(config));
    }

    public static void init(GridClient gridClient) throws Exception {
        if (instance != null) {
            throw new Exception("SQGrid.init() called more than once!");
        }
        instance = new SQGrid(gridClient);
    }

    private SQGrid(GridClient gridClient) throws JMSException, IOException {
        this.gridClient = gridClient;
    }

    public static GridClient getGridClient() {
        if (instance == null) {
            throw new RuntimeException("You have to call SQGrid.init() on program startup!");
        }
        return SQGrid.instance.gridClient;
    }

    public static boolean started() {
        return instance != null;
    }

    public static void close() throws Exception {
        SQGrid.instance.gridClient.close();
        instance = null;
    }
}

