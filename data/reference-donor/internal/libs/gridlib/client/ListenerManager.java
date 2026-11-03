/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 *  javax.jms.Message
 *  javax.jms.MessageListener
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.client;

import com.strategyquant.gridlib.TopicIdent;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.message.JmsConnectionInfo;
import com.strategyquant.gridlib.message.JmsPerformer;
import com.strategyquant.gridlib.message.MessageKind;
import com.strategyquant.gridlib.message.MessageProperties;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantReadWriteLock;
import javax.jms.JMSException;
import javax.jms.Message;
import javax.jms.MessageListener;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ListenerManager
implements AutoCloseable {
    private static final Logger LOGGER = LoggerFactory.getLogger(ListenerManager.class);
    private ReentrantReadWriteLock lock = new ReentrantReadWriteLock();
    private Map<String, IGridMessageListener> listeners = new HashMap<String, IGridMessageListener>();
    private JmsPerformer sender;
    private JmsPerformer reciever;
    private ConcurrentMap<String, Boolean> resultMap = new ConcurrentHashMap<String, Boolean>();

    public ListenerManager(JmsConnectionInfo jmsConnectionInfo, boolean bl) throws JMSException {
        if (!bl) {
            this.prepareListener(jmsConnectionInfo);
        }
    }

    private void prepareListener(JmsConnectionInfo jmsConnectionInfo) throws JMSException {
        this.sender = new JmsPerformer(TopicIdent.listenerTopic, jmsConnectionInfo);
        this.reciever = new JmsPerformer(TopicIdent.listenerTopic, jmsConnectionInfo);
        this.reciever.prepareMessageClient(new MessageListener(){

            public void onMessage(Message message) {
                try {
                    String string = message.getStringProperty(MessageProperties.jobGroupId.name());
                    boolean bl = message.getBooleanProperty(MessageProperties.registerResult.name());
                    ListenerManager.this.resultMap.put(string, bl);
                }
                catch (JMSException jMSException) {
                    LOGGER.error("", (Throwable)jMSException);
                }
            }
        }, MessageKind.registerListenerResult);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void registerMessageListener(String string, IGridMessageListener iGridMessageListener) {
        block10: {
            try {
                if (!this.lock.writeLock().tryLock(200L, TimeUnit.MILLISECONDS)) break block10;
                try {
                    if (this.listeners.containsKey(string)) {
                        throw new IllegalArgumentException("Listener for group: " + string + " is already registered!");
                    }
                    this.listeners.put(string, iGridMessageListener);
                    if (this.sender == null) break block10;
                    HashMap<MessageProperties, String> hashMap = new HashMap<MessageProperties, String>();
                    hashMap.put(MessageProperties.jobGroupId, string);
                    try {
                        this.sender.sendSimpleMessage(MessageKind.registerListener, null, hashMap);
                    }
                    catch (JMSException jMSException) {
                        LOGGER.error("", (Throwable)jMSException);
                        throw new IllegalArgumentException("Checking unique of listener failed!");
                    }
                    while (!this.resultMap.containsKey(string)) {
                    }
                    Boolean bl = (Boolean)this.resultMap.get(string);
                    this.resultMap.remove(string);
                    if (!bl.booleanValue()) {
                        throw new IllegalArgumentException("Listener for group: " + string + " is already registered on another node!");
                    }
                }
                finally {
                    this.lock.writeLock().unlock();
                }
            }
            catch (InterruptedException interruptedException) {
                LOGGER.error("", (Throwable)interruptedException);
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void removeMessageListener(String string) {
        block7: {
            try {
                if (!this.lock.writeLock().tryLock(100L, TimeUnit.MILLISECONDS)) break block7;
                try {
                    this.listeners.remove(string);
                    if (this.sender == null) break block7;
                    HashMap<MessageProperties, String> hashMap = new HashMap<MessageProperties, String>();
                    hashMap.put(MessageProperties.jobGroupId, string);
                    try {
                        this.sender.sendSimpleMessage(MessageKind.unregisterListener, null, hashMap);
                    }
                    catch (JMSException jMSException) {
                        LOGGER.error("", (Throwable)jMSException);
                        throw new IllegalArgumentException("Checking unique of listener failed!");
                    }
                }
                finally {
                    this.lock.writeLock().unlock();
                }
            }
            catch (InterruptedException interruptedException) {
                LOGGER.error("Interrupted wait for lock", (Throwable)interruptedException);
            }
        }
    }

    public boolean isRegisteredMessageListener(String string) {
        this.lock.readLock().lock();
        try {
            boolean bl = this.listeners.containsKey(string);
            return bl;
        }
        finally {
            this.lock.readLock().unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public boolean sendToListener(String string, GridMessage gridMessage) {
        block10: {
            boolean bl = gridMessage.getMessageID() != 6;
            try {
                boolean bl2;
                if (bl) {
                    this.lock.writeLock().lock();
                    bl2 = true;
                } else {
                    bl2 = this.lock.writeLock().tryLock(100L, TimeUnit.MILLISECONDS);
                }
                if (!bl2) break block10;
                IGridMessageListener iGridMessageListener = null;
                try {
                    iGridMessageListener = this.listeners.get(string);
                }
                finally {
                    this.lock.writeLock().unlock();
                }
                if (iGridMessageListener != null) {
                    try {
                        iGridMessageListener.messageReceived(gridMessage);
                    }
                    catch (Exception exception) {
                        LOGGER.error("Error while handling finish message", (Throwable)exception);
                    }
                }
                return iGridMessageListener != null;
            }
            catch (InterruptedException interruptedException) {
                LOGGER.error("", (Throwable)interruptedException);
            }
        }
        return false;
    }

    @Override
    public void close() throws Exception {
        if (this.sender != null) {
            this.sender.close();
        }
        if (this.reciever != null) {
            this.reciever.close();
        }
        this.lock.writeLock().lock();
        try {
            this.listeners.clear();
        }
        finally {
            this.lock.writeLock().unlock();
        }
    }
}

