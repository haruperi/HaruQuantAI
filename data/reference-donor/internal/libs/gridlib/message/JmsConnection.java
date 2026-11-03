/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.Connection
 *  javax.jms.JMSException
 *  javax.jms.Session
 *  javax.jms.Topic
 *  org.apache.activemq.artemis.api.jms.ActiveMQJMSClient
 *  org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.message;

import com.strategyquant.gridlib.message.JmsConnectionInfo;
import javax.jms.Connection;
import javax.jms.JMSException;
import javax.jms.Session;
import javax.jms.Topic;
import org.apache.activemq.artemis.api.jms.ActiveMQJMSClient;
import org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class JmsConnection {
    private static final Logger LOGGER = LoggerFactory.getLogger(JmsConnection.class);
    private String ident;
    private Connection connection;
    private ActiveMQConnectionFactory factory;
    private String target;

    public JmsConnection(JmsConnectionInfo jmsConnectionInfo) throws JMSException {
        this.ident = jmsConnectionInfo.getIdent();
        this.target = jmsConnectionInfo.getTarget();
        this.initClient();
    }

    public Session createSession(boolean bl) throws JMSException {
        return this.connection.createSession(bl, 1);
    }

    protected String getIdent() {
        return this.ident;
    }

    private void initClient() throws JMSException {
        int n = 102400;
        if (!this.target.startsWith("tcp") && !this.target.startsWith("vm")) {
            this.target = "tcp://" + this.target;
        }
        LOGGER.debug("Connecting to ActiveMQ engine (" + this.target + ")...");
        this.factory = new ActiveMQConnectionFactory(this.target);
        this.factory.setMinLargeMessageSize(n);
        this.connection = this.factory.createConnection();
        this.connection.start();
        LOGGER.debug("ActiveMQ connected");
    }

    public Topic createTopic(String string) {
        return ActiveMQJMSClient.createTopic((String)string);
    }

    public void close() throws JMSException {
        if (this.connection != null) {
            LOGGER.debug("Closing JMS connection...");
            this.connection.close();
            LOGGER.debug("JMS connection closed");
        }
        if (this.factory != null) {
            LOGGER.debug("Closing JMS factory...");
            this.factory.close();
            LOGGER.debug("JMS factory closed...");
        }
    }
}

