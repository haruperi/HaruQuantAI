/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.WebSocketPublisher;
import java.util.concurrent.locks.StampedLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class SynchronizedWebSocketPublisher
implements WebSocketPublisher {
    private static final Logger Log = LoggerFactory.getLogger(SynchronizedWebSocketPublisher.class);
    private DataToSend dataToSend;
    private boolean dataPulled = false;
    private StampedLock lock = new StampedLock();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public final DataToSend getDataToSend() throws Exception {
        long l = this.lock.readLock();
        try {
            if (!this.dataPulled) {
                this.dataPulled = true;
                try {
                    this.dataToSend = this.getData();
                }
                catch (Exception exception) {
                    Log.error("Cannot get data from publisher '" + this.getClass().getSimpleName() + "'", (Throwable)exception);
                    this.dataToSend = null;
                }
            }
            DataToSend dataToSend = this.dataToSend;
            return dataToSend;
        }
        finally {
            this.lock.unlock(l);
        }
    }

    @Override
    public final void confirmBroadcast() {
        long l = this.lock.writeLock();
        try {
            this.handleConfirmBroadcast();
        }
        finally {
            this.lock.unlock(l);
        }
    }

    protected void handleConfirmBroadcast() {
        this.dataPulled = false;
    }

    protected abstract DataToSend getData();
}

