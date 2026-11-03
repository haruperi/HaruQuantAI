/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 *  org.apache.commons.codec.digest.DigestUtils
 *  org.apache.commons.io.FileUtils
 */
package com.strategyquant.gridlib.sync.updater;

import com.strategyquant.gridlib.FileHelper;
import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.sync.updater.AbstractFolderUpdater;
import com.strategyquant.gridlib.sync.updater.HandleHashResult;
import java.io.File;
import java.io.IOException;
import javax.jms.JMSException;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.commons.io.FileUtils;

public class SolidFolderUpdater
extends AbstractFolderUpdater {
    private String hash;

    public SolidFolderUpdater(String string, String string2, JmsConnectionInfo jmsConnectionInfo) throws IOException, JMSException {
        super(string, string2, jmsConnectionInfo);
    }

    @Override
    public void updateHash() throws IOException {
        this.hash = FileHelper.countHash(this.getFolder());
        this.hash = DigestUtils.md5Hex((String)this.hash);
    }

    @Override
    public HandleHashResult hashChanged(String string) {
        boolean bl;
        boolean bl2 = bl = !string.equals(this.hash);
        if (bl) {
            this.setDirty(true);
        }
        return new HandleHashResult(bl, null);
    }

    @Override
    protected void prepareForNewData() throws IOException {
        super.prepareForNewData();
        FileUtils.cleanDirectory((File)new File(this.getFolder()));
    }
}

