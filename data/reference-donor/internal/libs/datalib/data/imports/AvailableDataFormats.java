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
package com.strategyquant.datalib.data.imports;

import com.strategyquant.datalib.data.imports.CustomDataFormat;
import com.strategyquant.datalib.data.imports.DataColumns;
import com.strategyquant.datalib.data.io.columns.AskCol;
import com.strategyquant.datalib.data.io.columns.BidCol;
import com.strategyquant.datalib.data.io.columns.CloseCol;
import com.strategyquant.datalib.data.io.columns.DateCol;
import com.strategyquant.datalib.data.io.columns.DateTimeCol;
import com.strategyquant.datalib.data.io.columns.DefaultCol;
import com.strategyquant.datalib.data.io.columns.HighCol;
import com.strategyquant.datalib.data.io.columns.LowCol;
import com.strategyquant.datalib.data.io.columns.OpenCol;
import com.strategyquant.datalib.data.io.columns.TimeCol;
import com.strategyquant.datalib.data.io.columns.UnusedCol;
import com.strategyquant.datalib.data.io.columns.VolumeCol;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.output.Format;
import org.jdom2.output.XMLOutputter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AvailableDataFormats {
    public static final Logger Log = LoggerFactory.getLogger(AvailableDataFormats.class);
    private static final String filePath = SQPaths.settingsDirPath + "/dataFormats.xml";
    public static final String MT5TickData = "MetaTrader5 Tick Data";
    private static AvailableDataFormats instance;
    protected ArrayList<CustomDataFormat> availableFileFormats = new ArrayList();

    private AvailableDataFormats() {
        this.loadPredefinedFileFormats();
        this.sortByOrderAndName(this.availableFileFormats);
        this.loadCustomFileFormats();
    }

    public ArrayList<CustomDataFormat> getAvailableFileFormats() {
        return this.availableFileFormats;
    }

    public static AvailableDataFormats getInstance() {
        if (instance == null) {
            instance = new AvailableDataFormats();
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
        CustomDataFormat customDataFormat = new CustomDataFormat();
        customDataFormat.setName("MetaTrader4");
        customDataFormat.setSeparator(",");
        customDataFormat.setDateFormat("yyyy.MM.dd");
        customDataFormat.setSkipRows(0);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        HashMap<Integer, DefaultCol> hashMap = new HashMap<Integer, DefaultCol>();
        hashMap.put(0, new DateCol());
        hashMap.put(1, new TimeCol());
        hashMap.put(2, new OpenCol());
        hashMap.put(3, new HighCol());
        hashMap.put(4, new LowCol());
        hashMap.put(5, new CloseCol());
        hashMap.put(6, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("MetaTrader5");
        customDataFormat.setSeparator("\t");
        customDataFormat.setDateFormat("yyyy.MM.dd");
        customDataFormat.setSkipRows(1);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateCol());
        hashMap.put(1, new TimeCol());
        hashMap.put(2, new OpenCol());
        hashMap.put(3, new HighCol());
        hashMap.put(4, new LowCol());
        hashMap.put(5, new CloseCol());
        hashMap.put(6, new VolumeCol());
        hashMap.put(7, new UnusedCol());
        hashMap.put(8, new UnusedCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName(MT5TickData);
        customDataFormat.setSeparator("\t");
        customDataFormat.setDateFormat("yyyy.MM.dd");
        customDataFormat.setTimeFormat("HH:mm:ss.SSS");
        customDataFormat.setSkipRows(1);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        customDataFormat.setOrder(100);
        hashMap = new HashMap();
        hashMap.put(0, new DateCol());
        hashMap.put(1, new TimeCol());
        hashMap.put(2, new BidCol());
        hashMap.put(3, new AskCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("SQ Tick Downloader");
        customDataFormat.setSeparator(",");
        customDataFormat.setDateFormat("yyyy.MM.dd HH:mm:ss.SSS");
        customDataFormat.setSkipRows(1);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateTimeCol());
        hashMap.put(1, new BidCol());
        hashMap.put(2, new AskCol());
        hashMap.put(3, new VolumeCol());
        hashMap.put(4, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("SQ3 Tick Export");
        customDataFormat.setSeparator(",");
        customDataFormat.setDateFormat("dd.MM.yyyy HH:mm:ss");
        customDataFormat.setSkipRows(0);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateTimeCol());
        hashMap.put(1, new AskCol());
        hashMap.put(2, new BidCol());
        hashMap.put(3, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("DukasCopy Tick Data");
        customDataFormat.setSeparator(",");
        customDataFormat.setDateFormat("dd.MM.yyyy HH:mm:ss");
        customDataFormat.setSkipRows(1);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateTimeCol());
        hashMap.put(1, new AskCol());
        hashMap.put(2, new BidCol());
        hashMap.put(3, new VolumeCol());
        hashMap.put(4, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("MetaTrader4 tick export");
        customDataFormat.setSeparator(",");
        customDataFormat.setDateFormat("yyyy.MM.dd HH:mm:ss");
        customDataFormat.setSkipRows(1);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateTimeCol());
        hashMap.put(1, new AskCol());
        hashMap.put(2, new BidCol());
        hashMap.put(3, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("NinjaTrader data");
        customDataFormat.setSeparator(";");
        customDataFormat.setDateFormat("yyyyMMdd");
        customDataFormat.setSkipRows(0);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateCol());
        hashMap.put(1, new OpenCol());
        hashMap.put(2, new HighCol());
        hashMap.put(3, new LowCol());
        hashMap.put(4, new CloseCol());
        hashMap.put(5, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("NinjaTrader data (sqDataExport)");
        customDataFormat.setSeparator(";");
        customDataFormat.setDateFormat("MM/dd/yyyy HH:mm");
        customDataFormat.setSkipRows(1);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateCol());
        hashMap.put(1, new TimeCol());
        hashMap.put(2, new OpenCol());
        hashMap.put(3, new HighCol());
        hashMap.put(4, new LowCol());
        hashMap.put(5, new CloseCol());
        hashMap.put(6, new UnusedCol());
        hashMap.put(7, new UnusedCol());
        hashMap.put(8, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("AZ-Invest Range/Renko data");
        customDataFormat.setSeparator(",");
        customDataFormat.setDateFormat("yyyy.MM.dd HH:mm:ss");
        customDataFormat.setSkipRows(1);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateTimeCol());
        hashMap.put(1, new OpenCol());
        hashMap.put(2, new HighCol());
        hashMap.put(3, new LowCol());
        hashMap.put(4, new CloseCol());
        hashMap.put(5, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("Tradestation");
        customDataFormat.setSeparator(",");
        customDataFormat.setDateFormat("MM/dd/yyyy HH:mm");
        customDataFormat.setSkipRows(1);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateCol());
        hashMap.put(1, new TimeCol());
        hashMap.put(2, new OpenCol());
        hashMap.put(3, new HighCol());
        hashMap.put(4, new LowCol());
        hashMap.put(5, new CloseCol());
        hashMap.put(6, new VolumeCol());
        hashMap.put(7, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("MultiCharts");
        customDataFormat.setSeparator(",");
        customDataFormat.setDateFormat("MM/dd/yyyy");
        customDataFormat.setSkipRows(1);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateCol());
        hashMap.put(1, new TimeCol());
        hashMap.put(2, new OpenCol());
        hashMap.put(3, new HighCol());
        hashMap.put(4, new LowCol());
        hashMap.put(5, new CloseCol());
        hashMap.put(6, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("Kibot daily data");
        customDataFormat.setSeparator(",");
        customDataFormat.setDateFormat("MM/dd/yyyy");
        customDataFormat.setSkipRows(0);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateCol());
        hashMap.put(1, new OpenCol());
        hashMap.put(2, new HighCol());
        hashMap.put(3, new LowCol());
        hashMap.put(4, new CloseCol());
        hashMap.put(5, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("Kibot intraday data");
        customDataFormat.setSeparator(",");
        customDataFormat.setDateFormat("MM/dd/yyyy");
        customDataFormat.setSkipRows(0);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateCol());
        hashMap.put(1, new TimeCol());
        hashMap.put(2, new OpenCol());
        hashMap.put(3, new HighCol());
        hashMap.put(4, new LowCol());
        hashMap.put(5, new CloseCol());
        hashMap.put(6, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
        customDataFormat = new CustomDataFormat();
        customDataFormat.setName("Kibot tick data");
        customDataFormat.setSeparator(",");
        customDataFormat.setDateFormat("MM/dd/yyyy");
        customDataFormat.setSkipRows(0);
        customDataFormat.setSkipColumns(0);
        customDataFormat.setPredefined(true);
        hashMap = new HashMap();
        hashMap.put(0, new DateCol());
        hashMap.put(1, new TimeCol());
        hashMap.put(2, new UnusedCol());
        hashMap.put(3, new BidCol());
        hashMap.put(4, new AskCol());
        hashMap.put(5, new VolumeCol());
        customDataFormat.setColumns(hashMap);
        this.availableFileFormats.add(customDataFormat);
    }

    private void loadCustomFileFormats() {
        LinkedList<CustomDataFormat> linkedList = new LinkedList<CustomDataFormat>();
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
                        linkedList.add(customDataFormat);
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
        this.sortByOrderAndName(linkedList);
        this.availableFileFormats.addAll(linkedList);
    }

    private void sortByOrderAndName(List<CustomDataFormat> list) {
        list.sort(new Comparator<CustomDataFormat>(){

            @Override
            public int compare(CustomDataFormat customDataFormat, CustomDataFormat customDataFormat2) {
                int n = Integer.compare(customDataFormat.getOrder(), customDataFormat2.getOrder());
                return n != 0 ? n : customDataFormat.getName().compareTo(customDataFormat2.getName());
            }
        });
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
            BufferedWriter bufferedWriter = new BufferedWriter(new OutputStreamWriter((OutputStream)new FileOutputStream(file), "UTF8"));
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

