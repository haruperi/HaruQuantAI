/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.output.Format
 *  org.jdom2.output.XMLOutputter
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.customData;

import com.strategyquant.datalib.data.imports.AvailableDataFormats;
import com.strategyquant.datalib.data.imports.CustomDataFormat;
import com.strategyquant.datalib.data.imports.DataColumns;
import com.strategyquant.datalib.data.io.columns.DefaultCol;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.output.Format;
import org.jdom2.output.XMLOutputter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AvailableCustomDataFormats {
    public static final Logger Log = LoggerFactory.getLogger(AvailableDataFormats.class);
    private static final String filePath = SQPaths.settingsDirPath + "/customDataFormats.xml";
    private static AvailableCustomDataFormats instance;
    protected ArrayList<CustomDataFormat> availableFileFormats = new ArrayList();

    private AvailableCustomDataFormats() {
        this.loadPredefinedFileFormats();
        this.loadCustomFileFormats();
    }

    public ArrayList<CustomDataFormat> getAvailableFileFormats() {
        return this.availableFileFormats;
    }

    public static AvailableCustomDataFormats getInstance() {
        if (instance == null) {
            instance = new AvailableCustomDataFormats();
        }
        return instance;
    }

    public void registerFileFormats() {
        this.availableFileFormats.clear();
        this.loadPredefinedFileFormats();
    }

    public boolean formatExists(String string) {
        for (CustomDataFormat customDataFormat : this.availableFileFormats) {
            if (!customDataFormat.getName().equals(string)) continue;
            return true;
        }
        return false;
    }

    private void loadPredefinedFileFormats() {
    }

    private void loadCustomFileFormats() {
        try {
            File file = new File(filePath);
            if (!file.exists()) {
                return;
            }
            Element element = XMLUtil.fileToXmlElement((File)file);
            if (element != null) {
                for (Element element2 : element.getChildren("CustomFormat")) {
                    try {
                        CustomDataFormat customDataFormat = new CustomDataFormat();
                        customDataFormat.setName(element2.getAttributeValue("name"));
                        customDataFormat.setSeparator(element2.getAttributeValue("separator"));
                        customDataFormat.setSkipColumns(Integer.parseInt(element2.getAttributeValue("skipColumns")));
                        customDataFormat.setSkipRows(Integer.parseInt(element2.getAttributeValue("skipRows")));
                        customDataFormat.setDateFormat(element2.getAttributeValue("dateFormat"));
                        customDataFormat.setPredefined(false);
                        Element element3 = element2.getChild("Columns");
                        if (element3 != null) {
                            HashMap<Integer, DefaultCol> hashMap = new HashMap<Integer, DefaultCol>();
                            List list = element3.getChildren("Column");
                            for (int i = 0; i < list.size(); ++i) {
                                String string = ((Element)list.get(i)).getText();
                                DefaultCol defaultCol = DataColumns.getInstance().findColTypeByName(string);
                                if (defaultCol == null) continue;
                                hashMap.put(i, defaultCol);
                            }
                            customDataFormat.setColumns(hashMap);
                        }
                        this.availableFileFormats.add(customDataFormat);
                    }
                    catch (Exception exception) {
                        Log.error("Cannot load dataformat.", (Throwable)exception);
                    }
                }
            }
        }
        catch (Exception exception) {
            Log.error("Cannot load custom data formats", (Throwable)exception);
        }
    }

    public void addDataFormat(CustomDataFormat customDataFormat) {
        this.availableFileFormats.add(customDataFormat);
        this.saveFormats();
    }

    public void deleteDataFormat(String string) {
        this.remove(string, true);
    }

    private void remove(String string, boolean bl) {
        boolean bl2 = false;
        for (CustomDataFormat customDataFormat : this.availableFileFormats) {
            if (!customDataFormat.getName().equals(string)) continue;
            this.availableFileFormats.remove(customDataFormat);
            bl2 = true;
            break;
        }
        if (bl2 && bl) {
            this.saveFormats();
        }
    }

    public void updateDataFormat(CustomDataFormat customDataFormat) {
        this.remove(customDataFormat.getName(), false);
        this.availableFileFormats.add(customDataFormat);
        this.saveFormats();
    }

    private void saveFormats() {
        Element element;
        Element element2 = new Element("CustomDataFormats");
        for (CustomDataFormat object : this.availableFileFormats) {
            if (object.isPredefined()) continue;
            element = new Element("CustomFormat");
            element.setAttribute("name", object.getName());
            element.setAttribute("separator", object.getSeparator());
            element.setAttribute("skipColumns", String.valueOf(object.getSkipColumns()));
            element.setAttribute("skipRows", String.valueOf(object.getSkipRows()));
            element.setAttribute("dateFormat", object.getDateFormat());
            Element element3 = new Element("Columns");
            for (int i = 0; i < object.getColumns().size(); ++i) {
                String string = object.getColumns().get(i).getName();
                Element element4 = new Element("Column");
                element4.setText(string);
                element3.addContent((Content)element4);
            }
            element.addContent((Content)element3);
            element2.addContent((Content)element);
        }
        try {
            File file = new File(filePath);
            if (!file.exists()) {
                file.getParentFile().mkdirs();
            }
            BufferedWriter bufferedWriter = new BufferedWriter(new OutputStreamWriter((OutputStream)new FileOutputStream(file), StandardCharsets.UTF_8));
            element = new XMLOutputter(Format.getPrettyFormat());
            element.output(element2, (Writer)bufferedWriter);
            bufferedWriter.close();
        }
        catch (Exception exception) {
            Log.error("Saving settings failed.", (Throwable)exception);
        }
    }

    public CustomDataFormat findFileFormatByName(String string) {
        for (CustomDataFormat customDataFormat : this.availableFileFormats) {
            if (!customDataFormat.getName().equalsIgnoreCase(string)) continue;
            return customDataFormat;
        }
        return null;
    }
}

