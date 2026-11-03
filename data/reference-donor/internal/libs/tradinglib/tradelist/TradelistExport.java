/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  org.apache.poi.ss.usermodel.Cell
 *  org.apache.poi.ss.usermodel.CellStyle
 *  org.apache.poi.ss.usermodel.DataFormat
 *  org.apache.poi.ss.usermodel.Font
 *  org.apache.poi.ss.usermodel.IndexedColors
 *  org.apache.poi.ss.usermodel.Row
 *  org.apache.poi.xssf.usermodel.XSSFCellStyle
 *  org.apache.poi.xssf.usermodel.XSSFDataFormat
 *  org.apache.poi.xssf.usermodel.XSSFFont
 *  org.apache.poi.xssf.usermodel.XSSFSheet
 *  org.apache.poi.xssf.usermodel.XSSFWorkbook
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.tradelist;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.tradelist.TradelistTableColumnEntry;
import com.strategyquant.tradinglib.tradelist.TradelistTableView;
import com.strategyquant.tradinglib.tradelist.TradelistViewsManager;
import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.CellStyle;
import org.apache.poi.ss.usermodel.DataFormat;
import org.apache.poi.ss.usermodel.Font;
import org.apache.poi.ss.usermodel.IndexedColors;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.xssf.usermodel.XSSFCellStyle;
import org.apache.poi.xssf.usermodel.XSSFDataFormat;
import org.apache.poi.xssf.usermodel.XSSFFont;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradelistExport {
    private static final Logger Log = LoggerFactory.getLogger(TradelistExport.class);
    private HashMap<Short, CellStyle> cellStyles = new HashMap();

    public void toCsv(ArrayList<Object[]> arrayList, String string, boolean bl) {
        try {
            if (!string.toLowerCase().endsWith(".csv")) {
                string = string + ".csv";
            }
            String string2 = this.getCSVContent(arrayList, bl);
            SQUtils.stringToFile((String)string, (String)string2);
        }
        catch (Exception exception) {
            Log.error("Error while exporting tradelist to csv.", (Throwable)exception);
        }
    }

    public String toCsvCloud(ArrayList<Object[]> arrayList, boolean bl) {
        return this.getCSVContent(arrayList, bl);
    }

    private String getCSVContent(ArrayList<Object[]> arrayList, boolean bl) {
        int n;
        StringBuilder stringBuilder = new StringBuilder();
        TradelistTableView tradelistTableView = TradelistViewsManager.getInstance().getSelectedTradelistView();
        int n2 = tradelistTableView.columns.size();
        for (n = 0; n < n2; ++n) {
            stringBuilder.append("\"");
            stringBuilder.append(tradelistTableView.columns.get(n).getColumnEntryName());
            stringBuilder.append("\"");
            if (n == n2 - 1) continue;
            stringBuilder.append(";");
        }
        stringBuilder.append("\r\n");
        for (n = 0; n < arrayList.size(); ++n) {
            Object[] objectArray = arrayList.get(n);
            for (int i = 0; i < tradelistTableView.columns.size(); ++i) {
                Object object = objectArray[i];
                TradelistTableColumnEntry tradelistTableColumnEntry = tradelistTableView.columns.get(i);
                try {
                    String string = this.formatValue(tradelistTableColumnEntry, String.valueOf(object), bl);
                    stringBuilder.append("\"");
                    stringBuilder.append(string);
                    stringBuilder.append("\"");
                }
                catch (Exception exception) {
                    stringBuilder.append("\"N/A\"");
                }
                if (i == n2 - 1) continue;
                stringBuilder.append(";");
            }
            stringBuilder.append("\r\n");
        }
        return stringBuilder.toString();
    }

    public void toXlsx(ArrayList<Object[]> arrayList, String string, boolean bl) throws Exception {
        XSSFWorkbook xSSFWorkbook = null;
        try {
            xSSFWorkbook = this.createWorkBook(arrayList);
            if (!string.toLowerCase().endsWith(".xlsx")) {
                string = string + ".xlsx";
            }
            FileOutputStream fileOutputStream = new FileOutputStream(string);
            xSSFWorkbook.write((OutputStream)fileOutputStream);
            fileOutputStream.close();
        }
        catch (Exception exception) {
            Log.error("Error while exporting tradelist to xlsx.", (Throwable)exception);
            throw exception;
        }
        finally {
            try {
                if (xSSFWorkbook != null) {
                    xSSFWorkbook.close();
                }
            }
            catch (Exception exception) {
                Log.error("Cannot close workbook", (Throwable)exception);
            }
        }
    }

    public byte[] toXlsxCloud(ArrayList<Object[]> arrayList) throws Exception {
        XSSFWorkbook xSSFWorkbook = null;
        try {
            xSSFWorkbook = this.createWorkBook(arrayList);
            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
            xSSFWorkbook.write((OutputStream)byteArrayOutputStream);
            byte[] byArray = byteArrayOutputStream.toByteArray();
            return byArray;
        }
        catch (Exception exception) {
            Log.error("Error while exporting tradelist to xlsx.", (Throwable)exception);
            throw exception;
        }
        finally {
            try {
                if (xSSFWorkbook != null) {
                    xSSFWorkbook.close();
                }
            }
            catch (Exception exception) {
                Log.error("Cannot close workbook", (Throwable)exception);
            }
        }
    }

    private XSSFWorkbook createWorkBook(ArrayList<Object[]> arrayList) {
        XSSFWorkbook xSSFWorkbook = null;
        try {
            Object[] objectArray;
            int n;
            xSSFWorkbook = new XSSFWorkbook();
            XSSFSheet xSSFSheet = xSSFWorkbook.createSheet("Tradelist");
            XSSFFont xSSFFont = xSSFWorkbook.createFont();
            xSSFFont.setBold(true);
            xSSFFont.setFontHeightInPoints((short)14);
            xSSFFont.setColor(IndexedColors.RED.getIndex());
            XSSFCellStyle xSSFCellStyle = xSSFWorkbook.createCellStyle();
            xSSFCellStyle.setFont((Font)xSSFFont);
            XSSFDataFormat xSSFDataFormat = xSSFWorkbook.createDataFormat();
            TradelistTableView tradelistTableView = TradelistViewsManager.getInstance().getSelectedTradelistView();
            Row row = xSSFSheet.createRow(0);
            for (n = 0; n < tradelistTableView.columns.size(); ++n) {
                objectArray = row.createCell(n + 1);
                objectArray.setCellValue(tradelistTableView.columns.get(n).getColumnEntryName());
                objectArray.setCellStyle((CellStyle)xSSFCellStyle);
            }
            for (n = 0; n < arrayList.size(); ++n) {
                objectArray = arrayList.get(n);
                Row row2 = xSSFSheet.createRow(n + 1);
                for (int i = 0; i < tradelistTableView.columns.size(); ++i) {
                    Object object = objectArray[i];
                    TradelistTableColumnEntry tradelistTableColumnEntry = tradelistTableView.columns.get(i);
                    Cell cell = row2.createCell(i + 1);
                    this.setCellValue(tradelistTableColumnEntry, String.valueOf(object), xSSFWorkbook, cell, (DataFormat)xSSFDataFormat);
                }
            }
            for (n = 0; n < tradelistTableView.columns.size(); ++n) {
                xSSFSheet.autoSizeColumn(n);
            }
            return xSSFWorkbook;
        }
        catch (Exception exception) {
            Log.error("Error while exporting tradelist to xlsx.", (Throwable)exception);
            throw exception;
        }
    }

    private void setCellValue(TradelistTableColumnEntry tradelistTableColumnEntry, String string, XSSFWorkbook xSSFWorkbook, Cell cell, DataFormat dataFormat) {
        String string2 = "";
        short s = 0;
        try {
            String string3;
            string2 = tradelistTableColumnEntry.getColumnEntryName();
            if (string == null) {
                string = "N/A";
            }
            String string4 = tradelistTableColumnEntry.tableColumn.getType();
            if (string.equals("N/A")) {
                string4 = "Text";
            }
            switch (string4) {
                case "Decimal2": 
                case "Decimal2Pct": 
                case "Decimal2PL": 
                case "Decimal2Pips": {
                    s = dataFormat.getFormat("0.##");
                    cell.setCellValue(Double.valueOf(string).doubleValue());
                    break;
                }
                case "Decimal4": {
                    s = dataFormat.getFormat("0.####");
                    cell.setCellValue(Double.valueOf(string).doubleValue());
                    break;
                }
                case "Decimal5": {
                    s = dataFormat.getFormat("0.#####");
                    cell.setCellValue(Double.valueOf(string).doubleValue());
                    break;
                }
                case "Integer": {
                    cell.setCellValue((double)Integer.valueOf(string).intValue());
                    s = 1;
                    break;
                }
                case "Text": 
                case "Time": {
                    s = 49;
                    cell.setCellValue(string);
                    break;
                }
                default: {
                    cell.setCellValue(string);
                }
            }
            if (!this.cellStyles.containsKey(s)) {
                string3 = xSSFWorkbook.createCellStyle();
                string3.setDataFormat(s);
                this.cellStyles.put(s, (CellStyle)string3);
            }
            if ((string3 = this.cellStyles.get(s)) != null) {
                cell.setCellStyle((CellStyle)string3);
            }
        }
        catch (Exception exception) {
            Log.error(String.format("Error while writing cell value [%s = %s] to xls. Exc.", string2, string), (Throwable)exception);
            cell.setCellValue("N/A");
        }
    }

    private String formatValue(TradelistTableColumnEntry tradelistTableColumnEntry, String string, boolean bl) {
        string = SQUtils.removeHtmlTags((String)string);
        if (bl) {
            switch (tradelistTableColumnEntry.tableColumn.getType()) {
                case "Integer": 
                case "Text": 
                case "Time": {
                    return string;
                }
            }
            return string.replace('.', ',');
        }
        return string;
    }

    private ArrayList<String> getRecordKeys(Databank databank, String string) {
        if (string != null && !string.isEmpty()) {
            return new ArrayList<String>(Arrays.asList(string.split(",")));
        }
        return databank.getRecordKeys();
    }
}

