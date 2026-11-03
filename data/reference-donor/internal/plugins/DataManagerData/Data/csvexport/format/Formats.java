/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.output.Format
 *  org.jdom2.output.XMLOutputter
 *  org.json.JSONArray
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.format;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.format.Format;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.output.XMLOutputter;
import org.json.JSONArray;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Formats {
    public static final Logger Log = LoggerFactory.getLogger(Formats.class);
    private static final String FilePath = SQPaths.settingsDirPath + "/ExportCsvFileFormats.xml";
    public static final String FORMAT_GENERIC_TICK_COMMA = "Generic tick format (comma delimited)";
    public static final String FORMAT_GENERIC_TICK_DATE_FORMAT = "yyyyMMdd HH:mm:ss.SSS";
    public static final String FORMAT_GENERIC_BAR_COMMA = "Generic bar format (comma delimited)";
    public static final String FORMAT_GENERIC_BAR_DATE_FORMAT = "yyyyMMdd";
    private static Formats instance;
    public List<Format> available = new ArrayList<Format>();

    public static Formats get() {
        if (instance == null) {
            instance = new Formats();
        }
        return instance;
    }

    private Formats() {
        this.loadPredefinedFormats();
        this.loadCustomFormats();
    }

    private void loadPredefinedFormats() {
        this.addFormat(FORMAT_GENERIC_TICK_COMMA, ",", new String[]{"DateTime", "Bid", "Ask", "Volume"}, new String[]{AbstractItem.format("DateTime", FORMAT_GENERIC_TICK_DATE_FORMAT), "Bid", "Ask", "Volume"}, true, true);
        this.addFormat(FORMAT_GENERIC_BAR_COMMA, ",", new String[]{"Date", "Time", "Open", "High", "Low", "Close", "Volume"}, (String[])new String[]{AbstractItem.format("Date", FORMAT_GENERIC_BAR_DATE_FORMAT), AbstractItem.format("Time", "HH:mm:ss"), "Open", "High", "Low", "Close", "Volume"}.clone(), true, true);
        this.addFormat("Generic tick format (tab delimited)", "[Tab]", new String[]{"DateTime", "Bid", "Ask", "Volume"}, new String[]{AbstractItem.format("DateTime", FORMAT_GENERIC_TICK_DATE_FORMAT), "Bid", "Ask", "Volume"}, true, true);
        this.addFormat("Generic bar format (tab delimited)", "[Tab]", new String[]{"Date", "Time", "Open", "High", "Low", "Close", "Volume"}, (String[])new String[]{AbstractItem.format("Date", FORMAT_GENERIC_BAR_DATE_FORMAT), AbstractItem.format("Time", "HH:mm:ss"), "Open", "High", "Low", "Close", "Volume"}.clone(), true, true);
        this.addFormat("MetaTrader4 tick format", ",", new String[]{"DateTime", "Bid", "Ask", "Volume", "Volume"}, new String[]{AbstractItem.format("DateTime", "yyyy.MM.dd HH:mm:ss.SSS"), "Bid", "Ask", "Volume", "0"}, false, true);
        this.addFormat("MetaTrader4 bar format", ",", new String[]{"Date", "Time", "Open", "High", "Low", "Close", "Volume"}, new String[]{AbstractItem.format("Date", "yyyy.MM.dd"), AbstractItem.format("Time", "HH:mm"), "Open", "High", "Low", "Close", "Volume"}, false, true);
        this.addFormat("Amibroker bar (aqi) format", ",", new String[]{"Date", "Time", "Open", "High", "Low", "Close", "Volume"}, new String[]{AbstractItem.format("Date", FORMAT_GENERIC_BAR_DATE_FORMAT), AbstractItem.format("Time", "HHmmss"), "Open", "High", "Low", "Close", "Volume"}, false, true);
        this.addFormat("Amibroker tick (aqi) format", ",", new String[]{"Date", "Time", "Open", "High", "Low", "Close", "Volume"}, new String[]{AbstractItem.format("Date", FORMAT_GENERIC_BAR_DATE_FORMAT), AbstractItem.format("Time", "HHmmss"), "Bid", "Bid", "Bid", "Bid", "Volume"}, false, true);
        this.addFormat("Birt's CSV2FXT format", ",", new String[]{"DateTime", "Bid", "Ask", "Volume", "Volume"}, new String[]{AbstractItem.format("DateTime", "yyyy.MM.dd HH:mm:ss.SSS"), "Bid", "Ask", "Volume", "Volume"}, true, true);
        this.addFormat("Forex Tester bar format", ",", new String[]{"<TICKER>", "<DTYYYYMMDD>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<VOL>"}, new String[]{"Symbol", AbstractItem.format("Date", FORMAT_GENERIC_BAR_DATE_FORMAT), AbstractItem.format("Time", "HHmmss"), "Open", "High", "Low", "Close", "Volume"}, true, true);
        this.addFormat("Forex SB bar format", ",", new String[]{"Date", "Time", "Open", "High", "Low", "Close", "Volume"}, new String[]{AbstractItem.format("Date", "yyyy-MM-dd"), AbstractItem.format("Time", "HH:mm"), "Open", "High", "Low", "Close", "Volume"}, false, true);
        this.addFormat("Ninja Trader tick format", ";", new String[]{"DateTime", "Bid", "Volume"}, new String[]{AbstractItem.format("DateTime", "yyyyMMdd HHmmss SSS0000"), "Bid", "Volume"}, false, true);
        this.addFormat("Ninja Trader bar format", ";", new String[]{"DateTime", "Open", "High", "Low", "Close", "Volume"}, new String[]{AbstractItem.format("DateTime", "yyyyMMdd HHmmss"), "Open", "High", "Low", "Close", "Volume"}, false, true);
        this.addFormat("Neuroshell Trader format", ",", new String[]{"Date", "Time", "Open", "High", "Low", "Close"}, new String[]{AbstractItem.format("Date", FORMAT_GENERIC_BAR_DATE_FORMAT), AbstractItem.format("Time", "HHmmss"), "Open", "High", "Low", "Close"}, true, true);
        this.addFormat("Tradestation bar format", ",", new String[]{"Date", "Time", "Open", "High", "Low", "Close", "Volume", "Volume"}, new String[]{AbstractItem.format("Date", "MM/dd/yyyy"), AbstractItem.format("Time", "HH:mm"), "Open", "High", "Low", "Close", "Volume", "Volume"}, true, true);
    }

    public JSONArray toJson() {
        JSONArray formats = new JSONArray();
        for (Format format : this.available) {
            formats.put((Object)format.toJson());
        }
        return formats;
    }

    private void addFormat(String name, String separator, String[] header, String[] items, boolean includeHeader, boolean predefined) {
        try {
            this.available.add(new Format(name, separator, header, items, includeHeader, predefined));
        }
        catch (Exception e) {
            Log.error(String.format("Cannot add format with name '%s'. Exc.", name), (Throwable)e);
        }
    }

    public Format findByName(String name) {
        for (int i = 0; i < this.available.size(); ++i) {
            if (!name.equals(this.available.get((int)i).name)) continue;
            return this.available.get(i);
        }
        return null;
    }

    public static Format parseCustomFormat(String name, String header, String items, boolean includeHeader) throws Exception {
        String separator = ",";
        int size = Formats.split(items, ",").length;
        if (size < Formats.split(items, ";").length) {
            separator = ";";
            size = Formats.split(items, ";").length;
        }
        if (size < Formats.split(items, "[Tab]").length) {
            separator = "[Tab]";
            size = Formats.split(items, "[Tab]").length;
        }
        return new Format(name, separator, Formats.split(header, separator), Formats.split(items, separator), includeHeader, false);
    }

    private static String[] split(String str, String separator) {
        return str.split(Pattern.quote(separator));
    }

    public void updateFormat(String fileFormat, String header, String items, boolean includeHeader) throws Exception {
        Format oldFormat = Formats.get().findByName(fileFormat);
        if (oldFormat == null) {
            throw new Exception(L.t((String)"Format with name '%s' doesn't exist.", (Object[])new Object[]{fileFormat}));
        }
        Format newFormat = Formats.parseCustomFormat(fileFormat, header, items, includeHeader);
        this.available.remove(oldFormat);
        this.available.add(newFormat);
        this.saveCustomFormats();
    }

    public void addFormat(String name, String header, String items, boolean includeHeader) throws Exception {
        Format format = Formats.parseCustomFormat(name, header, items, includeHeader);
        this.available.add(format);
        this.saveCustomFormats();
    }

    private void saveCustomFormats() {
        Element customFormatsElem = new Element("CustomFormats");
        for (Format format : this.available) {
            if (format.predefined) continue;
            Element customFormatElem = new Element("CustomFormat");
            customFormatElem.addContent((Content)new Element("Name").setText(format.name));
            customFormatElem.addContent((Content)new Element("Separator").setText(format.separator));
            customFormatElem.addContent((Content)new Element("IncludeHeader").setText(format.includeHeader + ""));
            customFormatElem.addContent((Content)new Element("Header").setText(format.header));
            customFormatElem.addContent((Content)new Element("Items").setText(format.items));
            customFormatsElem.addContent((Content)customFormatElem);
        }
        try {
            File settingsFile = new File(FilePath);
            if (!settingsFile.exists()) {
                settingsFile.getParentFile().mkdirs();
            }
            BufferedWriter outputStream = new BufferedWriter(new OutputStreamWriter((OutputStream)new FileOutputStream(settingsFile), "UTF8"));
            XMLOutputter outputter = new XMLOutputter(org.jdom2.output.Format.getPrettyFormat());
            outputter.output(customFormatsElem, (Writer)outputStream);
            outputStream.close();
        }
        catch (Exception e) {
            Log.error("Cannot save custom formats.", (Throwable)e);
        }
    }

    private void loadCustomFormats() {
        try {
            File formatsFile = new File(FilePath);
            if (!formatsFile.exists()) {
                return;
            }
            Element formatsElem = XMLUtil.fileToXmlElement((File)formatsFile);
            if (formatsElem != null) {
                for (Element formatElem : formatsElem.getChildren("CustomFormat")) {
                    try {
                        String name = formatElem.getChildText("Name");
                        String header = formatElem.getChildText("Header");
                        String items = formatElem.getChildText("Items");
                        boolean includeHeader = Boolean.valueOf(formatElem.getChildText("IncludeHeader"));
                        Format format = Formats.parseCustomFormat(name, header, items, includeHeader);
                        this.available.add(format);
                    }
                    catch (Exception e) {
                        Log.error("Cannot load custom format.", (Throwable)e);
                    }
                }
            }
        }
        catch (Exception e) {
            Log.error("Cannot load custom formats", (Throwable)e);
        }
    }

    public void deleteFormat(String fileFormat) throws Exception {
        Format format = Formats.get().findByName(fileFormat);
        if (format == null) {
            throw new Exception(L.t((String)"Format with name '%s' doesn't exist.", (Object[])new Object[]{fileFormat}));
        }
        if (format.predefined) {
            throw new Exception(L.t((String)"Format with name '%s' is predefined.", (Object[])new Object[]{fileFormat}));
        }
        this.available.remove(format);
        this.saveCustomFormats();
    }
}

