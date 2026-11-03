/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.client;

import com.strategyquant.gridlib.client.Compute;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.compute.JobResult;
import com.strategyquant.gridlib.compute.common.ExecuteOptions;
import com.strategyquant.gridlib.config.Config;
import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.sync.guard.FolderGuards;
import com.strategyquant.gridlib.topology.GridTopology;
import java.io.IOException;
import java.util.LinkedList;
import java.util.List;
import javax.jms.JMSException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GridClient
implements AutoCloseable {
    private static final Logger LOGGER = LoggerFactory.getLogger(GridClient.class);
    private FolderGuards guards;
    private Compute compute;
    private Config config;

    protected GridClient(Config config, boolean bl) throws JMSException, IOException {
        this.config = config;
        JmsConnectionInfo jmsConnectionInfo = new JmsConnectionInfo(config.getServerLocation());
        LOGGER.debug("Jms ident:" + jmsConnectionInfo.getIdent());
        this.compute = new Compute(jmsConnectionInfo, config, bl);
        if (!this.compute.isLocalMode()) {
            this.guards = new FolderGuards(config.getFolderConfigs().getDataFolderRoot(), jmsConnectionInfo);
            this.prepareGuards();
        }
    }

    public GridClient(Config config) throws JMSException, IOException {
        this(config, false);
    }

    public Config getConfig() {
        return this.config;
    }

    protected void jobFinished(String string, String string2, JobResult<?> jobResult) {
        this.compute.jobFinished(string, string2, jobResult);
    }

    public GridTopology getGridTopology() {
        return this.compute.getGridTopology();
    }

    public String getGridDescriptions() {
        return this.compute.getGridDescriptions();
    }

    private void prepareGuards() throws IOException, JMSException {
        LOGGER.debug("Preparing guards");
        this.guards.create("libs", false);
        this.guards.create("data", false);
        this.guards.create("extends", true);
    }

    public void dataChanged() throws JMSException, IOException {
        LOGGER.debug("Current data version changed");
        if (this.guards != null) {
            this.guards.updateHash();
        }
    }

    @Override
    public void close() throws Exception {
        LOGGER.debug("Disposing gridClient.");
        this.compute.close();
        if (this.guards != null) {
            this.guards.close();
        }
    }

    public void executeOnGrid(String string, List<? extends GridJob<?>> list) throws Exception {
        this.executeOnGrid(string, list, null);
    }

    public void executeOnGrid(String string, GridJob<?> gridJob) throws Exception {
        LinkedList linkedList = new LinkedList();
        linkedList.add(gridJob);
        this.executeOnGrid(string, linkedList, null);
    }

    public void executeOnGrid(String string, List<? extends GridJob<?>> list, ExecuteOptions executeOptions) throws Exception {
        this.compute.execute(string, list, executeOptions);
    }

    public long countRunningJobs(String string, boolean bl) {
        long l = bl ? this.compute.getExecutedUndeliveredJobsCount(string) : this.compute.getRunningJobsCount(string);
        return l;
    }

    public long countRunningJobs(String string) {
        return this.countRunningJobs(string, true);
    }

    public long countWaitingJobs(String string) {
        return this.compute.getWaitingJobsCount(string);
    }

    public long countAllJobs(String string, boolean bl) {
        long l = bl ? this.compute.getExecutedUndeliveredJobsCount(string) : this.compute.getRunningJobsCount(string);
        long l2 = this.compute.getWaitingJobsCount(string);
        return l + l2;
    }

    public long countAllJobs(String string) {
        return this.countAllJobs(string, true);
    }

    public int getRunningThreads() {
        return this.getGridTopology().getRunningThreads();
    }

    public int getComputedThreads() {
        return this.compute.getComputedThread();
    }

    public int getUsedComputedThreads() {
        return this.compute.getUsedComputedThreads();
    }

    public void setUsedComputedThreads(int n) {
        this.compute.setUsedComputedThreads(n);
    }

    public void pause(String string) {
        this.compute.pause(string);
    }

    public void restart(String string) {
        this.compute.restart(string);
    }

    public void stop(String string) {
        this.compute.stop(string);
    }

    public void stop(String string, String string2) {
        this.compute.stop(string, string2);
    }

    public void pause(String string, String string2) {
        this.compute.pause(string, string2);
    }

    public void restart(String string, String string2) {
        this.compute.restart(string, string2);
    }

    public void registerMessageListener(String string, IGridMessageListener iGridMessageListener) {
        this.compute.registerMessageListener(string, iGridMessageListener);
    }

    public boolean isRegisteredMessageListener(String string) {
        return this.compute.isRegisteredMessageListener(string);
    }

    public void removeMessageListener(String string) {
        this.compute.removeMessageListener(string);
    }

    public boolean sendMessage(String string, String string2, GridMessage gridMessage) throws Exception {
        if (string2 == null) {
            return this.compute.sendMessageToListener(string, gridMessage);
        }
        return this.compute.sendMessageToJob(string2, string, gridMessage);
    }

    protected Compute getCompute() {
        return this.compute;
    }

    public void sendProgress(String string, String string2, int n) {
        this.compute.setProgress(string, string2, n);
    }

    public void waitForFinish(Object object, String string, String string2, String string3) throws InterruptedException {
        this.compute.waitForFinish(object, string, string2, string3);
    }

    public void setGroupRestrictions(String string, int n) {
        this.compute.setGroupRestrictions(string, n);
    }

    public int getRecommendedBatchSize() {
        int n = 2 * this.getGridTopology().getTotalCores();
        if (n < 5) {
            n = 5;
        }
        return n;
    }

    public void check() {
        this.compute.check();
    }

    public void waitForAllTaskFinished() throws InterruptedException {
        this.compute.waitForAllTaskFinished();
    }
}

