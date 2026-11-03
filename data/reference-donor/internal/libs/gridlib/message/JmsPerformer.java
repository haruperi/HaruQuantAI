/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.BytesMessage
 *  javax.jms.Destination
 *  javax.jms.JMSException
 *  javax.jms.Message
 *  javax.jms.MessageConsumer
 *  javax.jms.MessageListener
 *  javax.jms.MessageProducer
 *  javax.jms.ObjectMessage
 *  javax.jms.Session
 *  javax.jms.TextMessage
 *  javax.jms.Topic
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.message;

import com.strategyquant.gridlib.TopicIdent;
import com.strategyquant.gridlib.message.JmsConnection;
import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.message.MessageKind;
import com.strategyquant.gridlib.message.MessageProperties;
import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.Serializable;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import javax.jms.BytesMessage;
import javax.jms.Destination;
import javax.jms.JMSException;
import javax.jms.Message;
import javax.jms.MessageConsumer;
import javax.jms.MessageListener;
import javax.jms.MessageProducer;
import javax.jms.ObjectMessage;
import javax.jms.Session;
import javax.jms.TextMessage;
import javax.jms.Topic;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class JmsPerformer
implements AutoCloseable {
    private static final Logger LOGGER = LoggerFactory.getLogger(JmsPerformer.class);
    private List<MessageConsumer> consumers = new LinkedList<MessageConsumer>();
    private MessageProducer producer;
    private JmsConnection connection;
    private Session session;
    private Topic topic;

    public JmsPerformer(TopicIdent topicIdent, JmsConnectionInfo jmsConnectionInfo) throws JMSException {
        this(false, topicIdent, jmsConnectionInfo);
    }

    public JmsPerformer(boolean bl, TopicIdent topicIdent, JmsConnectionInfo jmsConnectionInfo) throws JMSException {
        this.connection = new JmsConnection(jmsConnectionInfo);
        this.session = this.connection.createSession(bl);
        this.topic = this.connection.createTopic(topicIdent.name());
    }

    public MessageKind getMessageKind(Message message) throws JMSException {
        String string = message.getStringProperty(MessageProperties.messageKind.name());
        return MessageKind.valueOf(string);
    }

    @Override
    public void close() throws JMSException {
        for (MessageConsumer messageConsumer : this.consumers) {
            messageConsumer.close();
        }
        if (this.session != null) {
            this.session.close();
        }
        this.connection.close();
    }

    public void prepareMessageClient(MessageListener messageListener, MessageKind messageKind) throws JMSException {
        this.prepareMessageClient(messageListener, MessageProperties.messageKind.name() + "='" + messageKind.name() + "'");
    }

    public void prepareMessageClient(MessageListener messageListener, String string) throws JMSException {
        String string2;
        LOGGER.debug("Preparing ArtemisMQ consumer...");
        String string3 = string2 = MessageProperties.targetIdent.name() + " is null OR " + MessageProperties.targetIdent.name() + "='" + this.connection.getIdent() + "'";
        if (string != null && !string.isEmpty()) {
            string3 = "(" + string3 + ") AND (" + string + ")";
        }
        LOGGER.debug("selector:" + string3);
        MessageConsumer messageConsumer = this.session.createConsumer((Destination)this.topic, string3);
        messageConsumer.setMessageListener(messageListener);
        LOGGER.debug("ArtemisMQ reciever consumer");
        this.consumers.add(messageConsumer);
    }

    private void ensureProducer(Topic topic) throws JMSException {
        if (this.producer == null) {
            LOGGER.debug("Preparing producer...");
            this.producer = this.session.createProducer((Destination)topic);
            this.producer.setDisableMessageID(true);
            this.producer.setDisableMessageTimestamp(true);
            this.producer.setDeliveryMode(1);
            LOGGER.debug("Producer prepared");
        }
    }

    private void fillProperties(Message message, Map<MessageProperties, String> map) throws JMSException {
        for (MessageProperties messageProperties : map.keySet()) {
            String string = map.get((Object)messageProperties);
            message.setStringProperty(messageProperties.name(), string);
        }
    }

    public void sendMessageFile(File file, String string, String string2) throws JMSException, IOException {
        BytesMessage bytesMessage = this.session.createBytesMessage();
        FileInputStream fileInputStream = new FileInputStream(file);
        BufferedInputStream bufferedInputStream = new BufferedInputStream(fileInputStream);
        bytesMessage.setObjectProperty("JMS_AMQ_InputStream", (Object)bufferedInputStream);
        bytesMessage.setStringProperty(MessageProperties.folder.name(), string2);
        this.sendMessage((Message)bytesMessage, string, MessageKind.sendingFileData);
        bufferedInputStream.close();
    }

    public void sendLargeMessage(InputStream inputStream, String string, Map<MessageProperties, String> map, MessageKind messageKind) throws JMSException, IOException {
        BytesMessage bytesMessage = this.session.createBytesMessage();
        BufferedInputStream bufferedInputStream = new BufferedInputStream(inputStream);
        bytesMessage.setObjectProperty("JMS_AMQ_InputStream", (Object)bufferedInputStream);
        this.fillProperties((Message)bytesMessage, map);
        this.sendMessage((Message)bytesMessage, string, messageKind);
        bufferedInputStream.close();
    }

    private synchronized void sendMessage(Message message, String string, MessageKind messageKind) throws JMSException {
        this.ensureProducer(this.topic);
        LOGGER.debug("Sending message " + (Object)((Object)messageKind) + " for target:" + string + "... ");
        if (string != null) {
            message.setStringProperty(MessageProperties.targetIdent.name(), string);
        }
        message.setStringProperty(MessageProperties.messageKind.name(), messageKind.name());
        message.setStringProperty(MessageProperties.senderIdent.name(), this.connection.getIdent());
        this.producer.send(message);
        LOGGER.debug("Message sent");
    }

    public void sendSimpleMessage(MessageKind messageKind, String string, Map<MessageProperties, String> map) throws JMSException {
        TextMessage textMessage = this.session.createTextMessage();
        this.fillProperties((Message)textMessage, map);
        this.sendMessage((Message)textMessage, string, messageKind);
    }

    public void sendTextMessage(MessageKind messageKind, String string, String string2) throws JMSException {
        TextMessage textMessage = this.session.createTextMessage();
        textMessage.setText(string2);
        this.sendMessage((Message)textMessage, string, messageKind);
    }

    public void sendObjectMessage(MessageKind messageKind, String string, Map<MessageProperties, String> map, Serializable serializable) throws JMSException {
        ObjectMessage objectMessage = this.session.createObjectMessage(serializable);
        this.fillProperties((Message)objectMessage, map);
        this.sendMessage((Message)objectMessage, string, messageKind);
    }

    public void commit() throws JMSException {
        this.session.commit();
    }
}

