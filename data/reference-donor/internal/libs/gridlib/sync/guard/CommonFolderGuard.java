/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 *  javax.jms.Message
 *  javax.jms.MessageListener
 *  javax.jms.ObjectMessage
 *  org.apache.commons.codec.digest.DigestUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.sync.guard;

import com.strategyquant.gridlib.FileHelper;
import com.strategyquant.gridlib.TopicIdent;
import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.message.JmsPerformer;
import com.strategyquant.gridlib.message.MessageKind;
import com.strategyquant.gridlib.message.MessageProperties;
import com.strategyquant.gridlib.sync.guard.IFolderGuard;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import javax.jms.JMSException;
import javax.jms.Message;
import javax.jms.MessageListener;
import javax.jms.ObjectMessage;
import org.apache.commons.codec.digest.DigestUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CommonFolderGuard
implements IFolderGuard {
    private static final Logger LOGGER = LoggerFactory.getLogger(CommonFolderGuard.class);
    private String folderIdent;
    private String folder;
    private String hash;
    private boolean solid;
    private JmsPerformer sender;
    private JmsPerformer reciever;

    public CommonFolderGuard(String string, String string2, JmsConnectionInfo jmsConnectionInfo, boolean bl) throws IOException, JMSException {
        this.folderIdent = string;
        this.folder = string2;
        this.sender = new JmsPerformer(TopicIdent.dataFilesTopic, jmsConnectionInfo);
        this.reciever = new JmsPerformer(TopicIdent.dataFilesTopic, jmsConnectionInfo);
        this.solid = bl;
        this.updateHash(false);
        this.prepareJMS();
        this.sendStatus(null);
    }

    private void prepareJMS() throws JMSException {
        String string = MessageProperties.folder.name() + "='" + this.folderIdent + "'";
        this.reciever.prepareMessageClient(new MessageListener(){

            public void onMessage(Message message) {
                try {
                    MessageKind messageKind = CommonFolderGuard.this.reciever.getMessageKind(message);
                    CommonFolderGuard.this.handleMessage(message, messageKind);
                }
                catch (IOException | JMSException throwable) {
                    throwable.printStackTrace();
                }
            }
        }, string);
    }

    private void handleMessage(Message message, MessageKind messageKind) throws JMSException, IOException {
        switch (messageKind) {
            case needFileData: {
                this.sendFiles(message.getStringProperty(MessageProperties.senderIdent.name()), (List)((Object)((ObjectMessage)message).getObject()));
                break;
            }
            case checkFileDataStatus: {
                this.sendStatus(message.getStringProperty(MessageProperties.senderIdent.name()));
                break;
            }
        }
    }

    private void sendFiles(String string, List<String> list) throws JMSException, IOException {
        LOGGER.debug("Sending file for folder:" + this.folderIdent);
        File file = this.zipFiles(list);
        this.sender.sendMessageFile(file, string, this.folderIdent);
        file.delete();
    }

    private void sendStatus(String string) throws FileNotFoundException, JMSException {
        LOGGER.debug("Sending status for folder:" + this.folderIdent);
        HashMap<MessageProperties, String> hashMap = new HashMap<MessageProperties, String>();
        hashMap.put(MessageProperties.dataVersion, this.hash);
        hashMap.put(MessageProperties.folder, this.folderIdent);
        this.sender.sendSimpleMessage(MessageKind.dataStatus, string, hashMap);
    }

    @Override
    public String getFolder() {
        return this.folder;
    }

    @Override
    public void updateHash() throws IOException, JMSException {
        this.updateHash(true);
    }

    private void updateHash(boolean bl) throws IOException, JMSException {
        this.hash = FileHelper.countHash(this.folder);
        if (this.solid) {
            this.hash = DigestUtils.md5Hex((String)this.hash);
        }
        if (bl) {
            this.sendStatus(null);
        }
    }

    private File zipFiles(List<String> list) throws IOException {
        return this.solid ? FileHelper.zip(this.folder) : FileHelper.zip(this.folder, list);
    }

    @Override
    public void close() throws JMSException {
        this.sender.close();
        this.reciever.close();
    }
}

