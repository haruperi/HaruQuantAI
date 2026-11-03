/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.BytesMessage
 *  javax.jms.JMSException
 *  javax.jms.Message
 *  javax.jms.MessageListener
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.sync.updater;

import com.strategyquant.gridlib.FileHelper;
import com.strategyquant.gridlib.TopicIdent;
import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.message.JmsPerformer;
import com.strategyquant.gridlib.message.MessageKind;
import com.strategyquant.gridlib.message.MessageProperties;
import com.strategyquant.gridlib.sync.updater.HandleHashResult;
import com.strategyquant.gridlib.sync.updater.IFolderUpdatedListener;
import com.strategyquant.gridlib.sync.updater.IFolderUpdater;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import javax.jms.BytesMessage;
import javax.jms.JMSException;
import javax.jms.Message;
import javax.jms.MessageListener;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class AbstractFolderUpdater
implements IFolderUpdater {
    private static final Logger LOGGER = LoggerFactory.getLogger(AbstractFolderUpdater.class);
    private String folder;
    private boolean dirty = true;
    protected String hash;
    private String folderIdent;
    private JmsPerformer sender;
    private JmsPerformer reciever;
    private List<IFolderUpdatedListener> listeners = new LinkedList<IFolderUpdatedListener>();

    public AbstractFolderUpdater(String string, String string2, JmsConnectionInfo jmsConnectionInfo) throws IOException, JMSException {
        this.folder = string2;
        this.folderIdent = string;
        this.sender = new JmsPerformer(TopicIdent.dataFilesTopic, jmsConnectionInfo);
        this.reciever = new JmsPerformer(TopicIdent.dataFilesTopic, jmsConnectionInfo);
        this.updateHash();
        this.prepareJMS();
        this.checkVersions();
    }

    @Override
    public void addFolderUpdatedListener(IFolderUpdatedListener iFolderUpdatedListener) {
        this.listeners.add(iFolderUpdatedListener);
    }

    private void checkVersions() throws JMSException {
        this.setDirty(true);
        HashMap<MessageProperties, String> hashMap = new HashMap<MessageProperties, String>();
        hashMap.put(MessageProperties.folder, this.folderIdent);
        LOGGER.debug("Send request for version for folder:" + this.folderIdent);
        this.sender.sendSimpleMessage(MessageKind.checkFileDataStatus, null, hashMap);
    }

    protected void setDirty(boolean bl) {
        this.dirty = bl;
        if (!bl) {
            this.notifyListeners();
        }
    }

    private void notifyListeners() {
        for (IFolderUpdatedListener iFolderUpdatedListener : this.listeners) {
            iFolderUpdatedListener.onUpdated();
        }
    }

    @Override
    public boolean isDirty() {
        return this.dirty;
    }

    @Override
    public String getFolder() {
        return this.folder;
    }

    private void prepareJMS() throws JMSException {
        String string = MessageProperties.folder.name() + "='" + this.folderIdent + "'";
        this.reciever.prepareMessageClient(new MessageListener(){

            public void onMessage(Message message) {
                try {
                    MessageKind messageKind = AbstractFolderUpdater.this.reciever.getMessageKind(message);
                    AbstractFolderUpdater.this.handleMessage(message, messageKind);
                }
                catch (IOException | JMSException throwable) {
                    throwable.printStackTrace();
                }
            }
        }, string);
    }

    @Override
    public void close() throws JMSException {
        this.sender.close();
        this.reciever.close();
    }

    private void downloadData(BytesMessage bytesMessage) throws JMSException, IOException {
        this.setDirty(true);
        File file = File.createTempFile("strategyquant", ".zip");
        FileOutputStream fileOutputStream = new FileOutputStream(file);
        BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(fileOutputStream);
        bytesMessage.setObjectProperty("JMS_AMQ_SaveStream", (Object)bufferedOutputStream);
        bufferedOutputStream.close();
        this.prepareForNewData();
        FileHelper.unzip(this.getFolder(), file);
        this.updateHash();
        this.setDirty(false);
        file.delete();
    }

    protected void prepareForNewData() throws IOException {
    }

    private void handleNewHash(String string, String string2) throws FileNotFoundException, JMSException {
        HandleHashResult handleHashResult = this.hashChanged(string2);
        if (handleHashResult.isNeedUpdate()) {
            LOGGER.debug("Node's data is different that client's - need to update:" + string);
            this.setDirty(true);
            HashMap<MessageProperties, String> hashMap = new HashMap<MessageProperties, String>();
            hashMap.put(MessageProperties.folder, string);
            this.sender.sendObjectMessage(MessageKind.needFileData, null, hashMap, handleHashResult.getFilesToUpdate());
        } else {
            this.setDirty(false);
            LOGGER.debug("Node's data is same as client's ones:" + string);
        }
    }

    protected abstract HandleHashResult hashChanged(String var1);

    private void handleMessage(Message message, MessageKind messageKind) throws JMSException, IOException {
        switch (messageKind) {
            case sendingFileData: {
                LOGGER.debug("Got data message");
                this.downloadData((BytesMessage)message);
                break;
            }
            case dataStatus: {
                String string = message.getStringProperty(MessageProperties.dataVersion.name());
                String string2 = message.getStringProperty(MessageProperties.folder.name());
                LOGGER.debug("Got a version info for folder:" + string2);
                this.handleNewHash(string2, string);
                break;
            }
        }
    }
}

