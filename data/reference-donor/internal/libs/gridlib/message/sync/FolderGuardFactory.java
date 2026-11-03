/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 */
package com.strategyquant.gridlib.message.sync;

import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.sync.guard.CommonFolderGuard;
import com.strategyquant.gridlib.sync.guard.IFolderGuard;
import com.strategyquant.gridlib.sync.updater.IFolderUpdater;
import com.strategyquant.gridlib.sync.updater.SingleFolderUpdater;
import com.strategyquant.gridlib.sync.updater.SolidFolderUpdater;
import java.io.IOException;
import javax.jms.JMSException;

public class FolderGuardFactory {
    public static IFolderGuard getGuard(String string, String string2, boolean bl, JmsConnectionInfo jmsConnectionInfo) throws IOException, JMSException {
        return new CommonFolderGuard(string, string2, jmsConnectionInfo, bl);
    }

    public static IFolderUpdater getUpdater(String string, String string2, boolean bl, JmsConnectionInfo jmsConnectionInfo) throws IOException, JMSException {
        return bl ? new SolidFolderUpdater(string, string2, jmsConnectionInfo) : new SingleFolderUpdater(string, string2, jmsConnectionInfo);
    }
}

