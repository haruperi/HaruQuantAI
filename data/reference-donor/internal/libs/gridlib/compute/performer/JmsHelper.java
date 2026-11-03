/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.jms.JMSException
 *  javax.jms.Message
 *  org.nustaq.serialization.FSTConfiguration
 */
package com.strategyquant.gridlib.compute.performer;

import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.message.JmsPerformer;
import com.strategyquant.gridlib.message.MessageKind;
import com.strategyquant.gridlib.message.MessageProperties;
import com.strategyquant.gridlib.utils.BeanUtils;
import com.strategyquant.gridlib.utils.CompressionUtils;
import java.io.BufferedOutputStream;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.Serializable;
import java.util.HashMap;
import java.util.zip.DataFormatException;
import javax.jms.JMSException;
import javax.jms.Message;
import org.nustaq.serialization.FSTConfiguration;

public class JmsHelper {
    private static final FSTConfiguration fstConf = FSTConfiguration.createDefaultConfiguration();

    public static byte[] serializeAndCompress(Serializable serializable, boolean bl, boolean bl2) throws IOException {
        byte[] byArray = bl ? BeanUtils.serialize(serializable) : fstConf.asByteArray((Object)serializable);
        if (bl2) {
            byArray = CompressionUtils.compress(byArray);
        }
        return byArray;
    }

    public static Serializable handleBytesMessage(Message message, boolean bl, boolean bl2) throws IOException, JMSException, ClassNotFoundException, DataFormatException {
        try (ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();){
            Serializable serializable;
            try (BufferedOutputStream bufferedOutputStream = new BufferedOutputStream(byteArrayOutputStream);){
                Serializable serializable2;
                message.setObjectProperty("JMS_AMQ_SaveStream", (Object)bufferedOutputStream);
                byte[] byArray = byteArrayOutputStream.toByteArray();
                serializable = serializable2 = JmsHelper.decompressAndDeserialize(byArray, bl, bl2);
            }
            return serializable;
        }
    }

    public static Serializable decompressAndDeserialize(byte[] byArray, boolean bl, boolean bl2) throws ClassNotFoundException, IOException, DataFormatException {
        if (bl2) {
            byArray = CompressionUtils.decompress(byArray);
        }
        if (bl) {
            return BeanUtils.deserializeObject(byArray);
        }
        Serializable serializable = (Serializable)fstConf.asObject(byArray);
        return serializable;
    }

    public static void pause(JmsPerformer jmsPerformer, String string) throws JMSException {
        HashMap<MessageProperties, String> hashMap = new HashMap<MessageProperties, String>();
        hashMap.put(MessageProperties.jobGroupId, string);
        jmsPerformer.sendSimpleMessage(MessageKind.pauseTasks, null, hashMap);
    }

    public static void stop(JmsPerformer jmsPerformer, String string) throws JMSException {
        HashMap<MessageProperties, String> hashMap = new HashMap<MessageProperties, String>();
        hashMap.put(MessageProperties.jobGroupId, string);
        jmsPerformer.sendSimpleMessage(MessageKind.stopTasks, null, hashMap);
    }

    public static void restart(JmsPerformer jmsPerformer, String string) throws JMSException {
        HashMap<MessageProperties, String> hashMap = new HashMap<MessageProperties, String>();
        hashMap.put(MessageProperties.jobGroupId, string);
        jmsPerformer.sendSimpleMessage(MessageKind.restartTasks, null, hashMap);
    }

    public static void sendMessageToJob(JmsPerformer jmsPerformer, String string, String string2, String string3, boolean bl, boolean bl2, GridMessage gridMessage) throws JMSException, IOException {
        byte[] byArray = JmsHelper.serializeAndCompress(gridMessage, bl, bl2);
        JmsHelper.sendMessageToJob(jmsPerformer, string, string2, string3, bl, bl2, byArray);
    }

    public static void sendMessageToJob(JmsPerformer jmsPerformer, String string, String string2, String string3, boolean bl, boolean bl2, byte[] byArray) throws JMSException, IOException {
        HashMap<MessageProperties, String> hashMap = new HashMap<MessageProperties, String>();
        hashMap.put(MessageProperties.jobId, string2);
        hashMap.put(MessageProperties.jobGroupId, string3);
        hashMap.put(MessageProperties.zippedContent, String.valueOf(bl2));
        hashMap.put(MessageProperties.jvmSerialization, String.valueOf(bl));
        jmsPerformer.sendLargeMessage(new ByteArrayInputStream(byArray), string, hashMap, MessageKind.sendCustomJobMessage);
    }
}

