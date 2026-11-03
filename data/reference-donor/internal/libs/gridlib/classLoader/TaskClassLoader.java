/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.gridlib.classLoader;

import com.strategyquant.gridlib.compute.performer.JmsJobInfo;
import java.io.File;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TaskClassLoader {
    private static final Logger LOGGER = LoggerFactory.getLogger(TaskClassLoader.class);
    private ClassLoader classLoader = TaskClassLoader.class.getClassLoader();

    public void loadJarsAndClasses(String ... stringArray) {
        List<URL> list = this.getUrls(stringArray);
        URL[] uRLArray = list.toArray(new URL[0]);
        LOGGER.debug("Registering JARs: " + list);
        this.classLoader = new URLClassLoader(uRLArray, TaskClassLoader.class.getClassLoader());
    }

    private void addFileUrl(List<URL> list, File file) {
        try {
            list.add(file.toURI().toURL());
        }
        catch (MalformedURLException malformedURLException) {
            LOGGER.error("", (Throwable)malformedURLException);
        }
    }

    private List<URL> getUrl(File file) {
        LinkedList<URL> linkedList = new LinkedList<URL>();
        File[] fileArray = file.listFiles();
        if (fileArray == null) {
            return linkedList;
        }
        for (File file2 : fileArray) {
            if (file2.isDirectory()) {
                linkedList.addAll(this.getUrl(file2));
                continue;
            }
            if (!file2.getName().toLowerCase().endsWith(".jar")) continue;
            this.addFileUrl(linkedList, file2);
        }
        return linkedList;
    }

    private List<URL> getUrls(String ... stringArray) {
        LinkedList<URL> linkedList = new LinkedList<URL>();
        for (String string : stringArray) {
            linkedList.addAll(this.getUrl(new File(string)));
        }
        return linkedList;
    }

    public <T> T createInstance(String string, JmsJobInfo jmsJobInfo) throws ClassNotFoundException, InstantiationException, IllegalAccessException, IllegalArgumentException, InvocationTargetException, NoSuchMethodException, SecurityException {
        Class<?> clazz = this.classLoader.loadClass(jmsJobInfo.getClassName());
        Constructor<?> constructor = clazz.getDeclaredConstructor(String.class, Integer.TYPE, Map.class);
        Object obj = constructor.newInstance(string, jmsJobInfo.getFlag(), jmsJobInfo.getParams());
        return (T)obj;
    }
}

