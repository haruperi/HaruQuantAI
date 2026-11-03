/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.BytesMessage
 *  javax.jms.JMSException
 *  javax.jms.Message
 *  javax.jms.MessageListener
 *  javax.jms.ObjectMessage
 *  org.apache.commons.lang3.exception.ExceptionUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.compute.performer;

import com.strategyquant.gridlib.TopicIdent;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.compute.JobResult;
import com.strategyquant.gridlib.compute.common.ExecuteOptions;
import com.strategyquant.gridlib.compute.performer.IComputePerformer;
import com.strategyquant.gridlib.compute.performer.IJobStatusChangedHandler;
import com.strategyquant.gridlib.compute.performer.JmsHelper;
import com.strategyquant.gridlib.compute.performer.JmsJobInfo;
import com.strategyquant.gridlib.config.Config;
import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.message.JmsPerformer;
import com.strategyquant.gridlib.message.MessageKind;
import com.strategyquant.gridlib.message.MessageProperties;
import com.strategyquant.gridlib.topology.GridTopology;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.Serializable;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.zip.DataFormatException;
import javax.jms.BytesMessage;
import javax.jms.JMSException;
import javax.jms.Message;
import javax.jms.MessageListener;
import javax.jms.ObjectMessage;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class JmsComputePerformer
implements IComputePerformer {
    private static final Logger LOGGER = LoggerFactory.getLogger(JmsComputePerformer.class);
    private JmsPerformer statisticsReciever;
    private JmsPerformer jobSender;
    private JmsPerformer messageSender;
    private JmsPerformer reciever;
    private List<IJobStatusChangedHandler> handlers = new LinkedList<IJobStatusChangedHandler>();
    private Config config;
    private GridTopology gridTopology;
    protected String serverTarget;

    public JmsComputePerformer(JmsConnectionInfo jmsConnectionInfo, Config config) throws JMSException {
        this.config = config;
        this.gridTopology = new GridTopology();
        this.jobSender = new JmsPerformer(true, TopicIdent.registerTaskTopic, jmsConnectionInfo);
        this.messageSender = new JmsPerformer(TopicIdent.messagesTopic, jmsConnectionInfo);
        this.reciever = new JmsPerformer(TopicIdent.taskResultsTopic, jmsConnectionInfo);
        this.statisticsReciever = new JmsPerformer(TopicIdent.statisticsTopic, jmsConnectionInfo);
        this.initListeners();
        this.statisticsReciever.sendSimpleMessage(MessageKind.refreshTopology, null, new HashMap<MessageProperties, String>());
    }

    private void initListeners() throws JMSException {
        this.reciever.prepareMessageClient(new MessageListener(){

            public void onMessage(Message message) {
                try {
                    JmsComputePerformer.this.handleTaskComputedMessage(message);
                }
                catch (Throwable throwable) {
                    LOGGER.error("", throwable);
                }
            }
        }, MessageKind.resultOfTask);
        this.statisticsReciever.prepareMessageClient(new MessageListener(){

            public void onMessage(Message message) {
                try {
                    JmsComputePerformer.this.serverTarget = message.getStringProperty(MessageProperties.senderIdent.name());
                    ObjectMessage objectMessage = (ObjectMessage)message;
                    JmsComputePerformer.this.gridTopology = (GridTopology)objectMessage.getObject();
                    LOGGER.debug("Got grid topology changed. Nodes:" + JmsComputePerformer.this.gridTopology.getNodes().size() + ". Total cores:" + JmsComputePerformer.this.gridTopology.getTotalCores());
                }
                catch (JMSException jMSException) {
                    LOGGER.error("", (Throwable)jMSException);
                }
            }
        }, MessageKind.sendingTopology);
    }

    @Override
    public void execute(GridJob<?> gridJob, String string, ExecuteOptions executeOptions) throws JMSException, IOException {
        JmsJobInfo jmsJobInfo = new JmsJobInfo(gridJob.getClass().getName(), gridJob.getParameters(), gridJob.getFlags());
        byte[] byArray = JmsHelper.serializeAndCompress(jmsJobInfo, this.config.isUseJavaSerialization(), this.config.isCompressData());
        HashMap<MessageProperties, String> hashMap = new HashMap<MessageProperties, String>();
        hashMap.put(MessageProperties.jobId, gridJob.getJobId());
        hashMap.put(MessageProperties.jobGroupId, string);
        hashMap.put(MessageProperties.zippedContent, String.valueOf(this.config.isCompressData()));
        hashMap.put(MessageProperties.jvmSerialization, String.valueOf(this.config.isUseJavaSerialization()));
        this.jobSender.sendLargeMessage(new ByteArrayInputStream(byArray), this.serverTarget, hashMap, MessageKind.registerTask);
    }

    private void handleTaskComputedMessage(Message message) throws JMSException, InterruptedException, IOException, ClassNotFoundException, DataFormatException {
        String string = message.getStringProperty(MessageProperties.jobId.name());
        String string2 = message.getStringProperty(MessageProperties.jobGroupId.name());
        boolean bl = Boolean.parseBoolean(message.getStringProperty(MessageProperties.jvmSerialization.name()));
        boolean bl2 = Boolean.parseBoolean(message.getStringProperty(MessageProperties.zippedContent.name()));
        if (string == null) {
            LOGGER.debug("Message without jobId");
            return;
        }
        JobResult jobResult = null;
        try {
            if (!(message instanceof BytesMessage)) {
                LOGGER.debug("Unexpected message format");
                return;
            }
            jobResult = (JobResult)JmsHelper.handleBytesMessage(message, bl, bl2);
        }
        catch (Throwable throwable) {
            jobResult = new JobResult();
            jobResult.setSuccess(false);
            jobResult.setErrorMessage(ExceptionUtils.getStackTrace((Throwable)throwable));
        }
        this.callHandler(string, string2, jobResult);
    }

    private void callHandler(String string, String string2, JobResult<Serializable> jobResult) {
        for (IJobStatusChangedHandler iJobStatusChangedHandler : this.handlers) {
            iJobStatusChangedHandler.onJobFinished(string, string2, jobResult);
        }
    }

    @Override
    public void close() throws JMSException {
        this.jobSender.close();
        this.statisticsReciever.close();
        this.reciever.close();
        this.messageSender.close();
        this.handlers.clear();
    }

    @Override
    public void addJobFinishedHandler(IJobStatusChangedHandler iJobStatusChangedHandler) {
        this.handlers.add(iJobStatusChangedHandler);
    }

    @Override
    public void commit() throws JMSException {
        this.jobSender.commit();
    }

    @Override
    public void pause(String string) throws JMSException {
        JmsHelper.pause(this.messageSender, string);
    }

    @Override
    public void stop(String string) throws JMSException {
        JmsHelper.stop(this.messageSender, string);
    }

    @Override
    public void restart(String string) throws JMSException {
        JmsHelper.restart(this.messageSender, string);
    }

    @Override
    public boolean sendMessageToJob(String string, String string2, GridMessage gridMessage) throws JMSException, IOException {
        JmsHelper.sendMessageToJob(this.messageSender, this.serverTarget, string, string2, this.config.isUseJavaSerialization(), this.config.isCompressData(), gridMessage);
        return true;
    }

    @Override
    public GridTopology getGridTopology() {
        return this.gridTopology;
    }

    @Override
    public String getGridDescriptions() {
        return null;
    }

    @Override
    public void setProgress(String string, String string2, int n) {
    }

    @Override
    public void setGroupRestrictions(String string, int n) {
    }

    @Override
    public void check() {
    }

    @Override
    public void setJobWaiting(String string, String string2, boolean bl) {
    }

    @Override
    public int getComputedThread() {
        return 0;
    }

    @Override
    public int getUsedComputedThreads() {
        return 0;
    }

    @Override
    public void setUsedComputedThreads(int n) {
    }

    @Override
    public void pause(String string, String string2) throws Exception {
    }

    @Override
    public void stop(String string, String string2) throws Exception {
    }

    @Override
    public void restart(String string, String string2) throws Exception {
    }
}

