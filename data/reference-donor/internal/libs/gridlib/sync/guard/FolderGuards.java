/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 */
package com.strategyquant.gridlib.sync.guard;

import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.message.sync.FolderGuardFactory;
import com.strategyquant.gridlib.sync.guard.IFolderGuard;
import java.io.IOException;
import java.util.LinkedList;
import java.util.List;
import javax.jms.JMSException;

public class FolderGuards
implements AutoCloseable {
    private List<IFolderGuard> guards = new LinkedList<IFolderGuard>();
    private String path;
    private JmsConnectionInfo connection;

    public FolderGuards(String string, JmsConnectionInfo jmsConnectionInfo) throws JMSException {
        this.path = string;
        this.connection = jmsConnectionInfo;
    }

    @Override
    public void close() throws Exception {
        for (IFolderGuard iFolderGuard : this.guards) {
            iFolderGuard.close();
        }
    }

    public void create(String string, boolean bl) throws IOException, JMSException {
        this.guards.add(FolderGuardFactory.getGuard(string, this.path + "/" + string, bl, this.connection));
    }

    public void updateHash() throws IOException, JMSException {
        for (IFolderGuard iFolderGuard : this.guards) {
            iFolderGuard.updateHash();
        }
    }
}

