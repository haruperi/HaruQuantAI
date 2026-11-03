/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Document
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.jdom2.input.SAXBuilder
 */
package com.strategyquant.gridlib.config;

import com.strategyquant.gridlib.config.Config;
import com.strategyquant.gridlib.config.SingleFolderConfig;
import com.strategyquant.gridlib.message.sync.FolderConfigs;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.UnsupportedEncodingException;
import java.nio.file.Files;
import java.util.LinkedList;
import java.util.List;
import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.jdom2.input.SAXBuilder;

public class Parser {
    public Config parse(File file) throws UnsupportedEncodingException, IOException, JDOMException {
        SAXBuilder sAXBuilder = new SAXBuilder();
        sAXBuilder.setIgnoringElementContentWhitespace(true);
        sAXBuilder.setIgnoringBoundaryWhitespace(true);
        String string = new String(Files.readAllBytes(file.toPath()), "UTF-8");
        string = string.replaceAll(">\\s*<", "><");
        ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(string.getBytes("UTF-8"));
        Document document = sAXBuilder.build((InputStream)byteArrayInputStream);
        Element element = document.getRootElement();
        Config config = new Config();
        config.setCompressData(Parser.getBoolean(element, "compressData", true));
        config.setUseAffinity(Parser.getBoolean(element, "useAffinity", true));
        config.setUseJavaSerialization(Parser.getBoolean(element, "useJavaSerialization", true));
        config.setServerLocation(Parser.getString(element, "serverLocation", null));
        config.setFoldersWithJars(this.getFoldersWithJars(element));
        config.setFolderConfigs(this.getFolderConfigs(element));
        return config;
    }

    private FolderConfigs getFolderConfigs(Element element) {
        FolderConfigs folderConfigs = new FolderConfigs();
        folderConfigs.setFolderConfig(new LinkedList<SingleFolderConfig>());
        Element element2 = element.getChild("syncFolders");
        if (element2 != null) {
            folderConfigs.setDataFolderRoot(element2.getAttributeValue("path"));
            List list = element2.getChildren();
            for (Element element3 : list) {
                if (!element3.getName().equalsIgnoreCase("folder")) continue;
                SingleFolderConfig singleFolderConfig = new SingleFolderConfig();
                singleFolderConfig.setFolder(element3.getAttributeValue("name"));
                singleFolderConfig.setSolidFolder("true".equalsIgnoreCase(element3.getAttributeValue("solid")));
                folderConfigs.getFolderConfig().add(singleFolderConfig);
            }
        }
        return folderConfigs;
    }

    private String[] getFoldersWithJars(Element element) {
        LinkedList<String> linkedList = new LinkedList<String>();
        Element element2 = element.getChild("libraryFolders");
        if (element2 != null) {
            List list = element2.getChildren();
            for (Element element3 : list) {
                if (!element3.getName().equalsIgnoreCase("library")) continue;
                linkedList.add(element3.getValue());
            }
        }
        return linkedList.toArray(new String[0]);
    }

    private static String getString(Element element, String string, String string2) {
        Element element2 = element.getChild(string);
        if (element2 == null) {
            return string2;
        }
        return element2.getValue();
    }

    private static boolean getBoolean(Element element, String string, boolean bl) {
        Element element2 = element.getChild(string);
        if (element2 == null) {
            return bl;
        }
        return Boolean.parseBoolean(element2.getValue());
    }
}

