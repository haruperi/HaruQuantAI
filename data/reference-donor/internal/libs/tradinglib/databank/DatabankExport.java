/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  org.apache.poi.ss.usermodel.Cell
 *  org.apache.poi.ss.usermodel.CellStyle
 *  org.apache.poi.ss.usermodel.Font
 *  org.apache.poi.ss.usermodel.IndexedColors
 *  org.apache.poi.ss.usermodel.Row
 *  org.apache.poi.ss.usermodel.Sheet
 *  org.apache.poi.ss.usermodel.Workbook
 *  org.apache.poi.xssf.usermodel.XSSFWorkbook
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import com.strategyquant.tradinglib.databank.DatabankViewsManager;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Arrays;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.CellStyle;
import org.apache.poi.ss.usermodel.Font;
import org.apache.poi.ss.usermodel.IndexedColors;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DatabankExport {
    private static final Logger Log = LoggerFactory.getLogger(DatabankExport.class);

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public int toCsv(Databank databank, String string, String string2, boolean bl, String string3, String string4) throws Exception {
        int n = 0;
        try {
            File file;
            if (!string.toLowerCase().endsWith(".csv") && !string.toLowerCase().endsWith(".txt")) {
                string = string + ".csv";
            }
            if (!(file = new File(string).getParentFile()).exists()) {
                file.mkdirs();
            }
            PrintWriter printWriter = new PrintWriter(string);
            DatabankTableView databankTableView = databank.getView();
            if (string3 != null) {
                databankTableView = DatabankViewsManager.getInstance().getView(string3);
            }
            int n2 = databankTableView.columns.size();
            printWriter.print(this.enclose(string4, "Strategy Name", true));
            String string5 = databank.getProject();
            if (!string5.equals("Builder") && !string5.equals("PortfolioMaster")) {
                printWriter.print(this.enclose(string4, "Filters result", true));
            }
            if (string5.equals("Optimizer")) {
                printWriter.print(this.enclose(string4, "Parameters", true));
                printWriter.print(this.enclose(string4, "Best WF", true));
            }
            for (int i = 0; i < n2; ++i) {
                printWriter.print(this.enclose(string4, databankTableView.columns.get(i).getColumnEntryName(), i != n2 - 1));
            }
            printWriter.println();
            ArrayList<String> arrayList = this.getRecordKeys(databank, string2);
            for (int i = 0; i < arrayList.size(); ++i) {
                ResultsGroup resultsGroup = null;
                try {
                    resultsGroup = databank.getLocked(arrayList.get(i), "DatabankExport");
                }
                catch (Exception exception) {
                    continue;
                }
                try {
                    Object object;
                    Object object2;
                    printWriter.print(this.enclose(string4, resultsGroup.getName(), true));
                    if (!string5.equals("Builder") && !string5.equals("PortfolioMaster")) {
                        try {
                            object2 = (DatabankColumn)DatabankColumns.get().findClassByName("FiltersResult");
                            object = ((DatabankColumn)object2).exportValue(resultsGroup, null, (byte)0, (byte)10, (byte)127);
                            printWriter.print(this.enclose(string4, (String)object, true));
                        }
                        catch (Exception exception) {
                            printWriter.print(this.enclose(string4, "N/A", true));
                        }
                    }
                    if (string5.equals("Optimizer")) {
                        try {
                            object2 = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
                            object = ((WalkForwardMatrixResult)object2).getWFResult(resultsGroup.getBestWFResultKey(), true);
                            String string6 = bl ? ((WalkForwardResult)object).testParams.replace(',', '/').replace('.', ',') : ((WalkForwardResult)object).testParams;
                            printWriter.print(this.enclose(string4, string6, true));
                            printWriter.print(this.enclose(string4, ((WalkForwardResult)object).toString(((WalkForwardMatrixResult)object2).periodType), true));
                        }
                        catch (Exception exception) {
                            object = "N/A";
                            try {
                                object = resultsGroup.getParams();
                                object = bl ? ((String)object).replace(',', '/').replace('.', ',') : object;
                            }
                            catch (Exception exception2) {
                                // empty catch block
                            }
                            printWriter.print(this.enclose(string4, (String)object, true));
                            printWriter.print(this.enclose(string4, "N/A", true));
                        }
                    }
                    for (int j = 0; j < databankTableView.columns.size(); ++j) {
                        object = databankTableView.columns.get(j);
                        try {
                            printWriter.print(this.enclose(string4, "" + this.formatValue((DatabankTableColumnEntry)object, resultsGroup, bl), false));
                        }
                        catch (Exception exception) {
                            printWriter.print(this.enclose(string4, "N/A", false));
                        }
                        if (j == n2 - 1) continue;
                        printWriter.print(string4);
                    }
                    printWriter.println();
                    ++n;
                    continue;
                }
                finally {
                    if (resultsGroup != null) {
                        resultsGroup.releaseLock("DatabankExport");
                    }
                }
            }
            printWriter.flush();
            printWriter.close();
        }
        catch (Exception exception) {
            Log.error("Error while exporting databank '" + databank.getName() + "' to csv.", (Throwable)exception);
            throw new Exception(L.t((String)"Error while exporting databank '%s' to xlsx.", (Object[])new Object[]{databank.getName()}), exception);
        }
        return n;
    }

    private String enclose(String string, String string2, boolean bl) {
        String string3 = "";
        if (!string.equals("\t")) {
            string3 = "\"";
        }
        return string3 + string2 + string3 + (bl ? string : "");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void toXlsx(Databank databank, String string, String string2, boolean bl, String string3) throws Exception {
        XSSFWorkbook xSSFWorkbook = null;
        try {
            File file;
            Object object;
            int n;
            xSSFWorkbook = new XSSFWorkbook();
            Sheet sheet = xSSFWorkbook.createSheet(databank.getName() + " databank");
            Font font = xSSFWorkbook.createFont();
            font.setBold(true);
            font.setFontHeightInPoints((short)14);
            font.setColor(IndexedColors.RED.getIndex());
            CellStyle cellStyle = xSSFWorkbook.createCellStyle();
            cellStyle.setFont(font);
            CellStyle cellStyle2 = xSSFWorkbook.createCellStyle();
            cellStyle2.setDataFormat((short)1);
            CellStyle cellStyle3 = xSSFWorkbook.createCellStyle();
            cellStyle3.setDataFormat((short)2);
            DatabankTableView databankTableView = databank.getView();
            if (string3 != null) {
                databankTableView = DatabankViewsManager.getInstance().getView(string3);
            }
            String string4 = databank.getProject();
            int n2 = 0;
            Row row = sheet.createRow(0);
            Cell cell = row.createCell(n2++);
            cell.setCellValue("Strategy name");
            cell.setCellStyle(cellStyle);
            if (!string4.equals("Builder") && !string4.equals("PortfolioMaster")) {
                cell = row.createCell(n2++);
                cell.setCellValue("Filters result");
                cell.setCellStyle(cellStyle);
            }
            if (string4.equals("Optimizer")) {
                cell = row.createCell(n2++);
                cell.setCellValue("Parameters");
                cell.setCellStyle(cellStyle);
                cell = row.createCell(n2++);
                cell.setCellValue("Best WF");
                cell.setCellStyle(cellStyle);
            }
            for (int i = 0; i < databankTableView.columns.size(); ++i) {
                cell = row.createCell(i + n2);
                cell.setCellValue(databankTableView.columns.get(i).getColumnEntryName());
                cell.setCellStyle(cellStyle);
            }
            ArrayList<String> arrayList = this.getRecordKeys(databank, string2);
            CellStyle cellStyle4 = xSSFWorkbook.createCellStyle();
            cellStyle4.setDataFormat((short)1);
            for (n = 0; n < arrayList.size(); ++n) {
                object = null;
                try {
                    object = databank.getLocked(arrayList.get(n), "DatabankExport");
                }
                catch (Exception exception) {
                    continue;
                }
                try {
                    Object object2;
                    Object object3;
                    Row row2 = sheet.createRow(n + 1);
                    n2 = 0;
                    cell = row2.createCell(n2++);
                    cell.setCellValue(((ResultsGroup)object).getName());
                    if (!string4.equals("Builder") && !string4.equals("PortfolioMaster")) {
                        cell = row2.createCell(n2++);
                        try {
                            object3 = (DatabankColumn)DatabankColumns.get().findClassByName("FiltersResult");
                            object2 = ((DatabankColumn)object3).exportValue((ResultsGroup)object, null, (byte)0, (byte)10, (byte)127);
                            cell.setCellValue((String)object2);
                        }
                        catch (Exception exception) {
                            cell.setCellValue("N/A");
                        }
                    }
                    if (string4.equals("Optimizer")) {
                        try {
                            object3 = (WalkForwardMatrixResult)((ResultsGroup)object).mainResult().get("WalkForwardResult");
                            object2 = ((WalkForwardMatrixResult)object3).getWFResult(((ResultsGroup)object).getBestWFResultKey(), true);
                            String string5 = bl ? ((WalkForwardResult)object2).testParams.replace(',', '/').replace('.', ',') : ((WalkForwardResult)object2).testParams;
                            cell = row2.createCell(n2++);
                            cell.setCellValue(string5);
                            cell = row2.createCell(n2++);
                            cell.setCellValue(((WalkForwardResult)object2).toString(((WalkForwardMatrixResult)object3).periodType));
                        }
                        catch (Exception exception) {
                            object2 = "N/A";
                            try {
                                object2 = ((ResultsGroup)object).getParams();
                                object2 = bl ? ((String)object2).replace(',', '/').replace('.', ',') : object2;
                            }
                            catch (Exception exception2) {
                                // empty catch block
                            }
                            cell = row2.createCell(n2++);
                            cell.setCellValue((String)object2);
                            cell = row2.createCell(n2++);
                            cell.setCellValue("N/A");
                        }
                        cell = row.createCell(2);
                        cell.setCellValue("Parameters");
                        cell.setCellStyle(cellStyle);
                        cell = row.createCell(3);
                        cell.setCellValue("Best WF");
                        cell.setCellStyle(cellStyle);
                    }
                    for (int i = 0; i < databankTableView.columns.size(); ++i) {
                        cell = row2.createCell(i + n2);
                        object2 = databankTableView.columns.get(i);
                        try {
                            this.setFormatedCellValue(cell, (DatabankTableColumnEntry)object2, (ResultsGroup)object, (Workbook)xSSFWorkbook, cellStyle2, cellStyle3);
                            continue;
                        }
                        catch (Exception exception) {
                            cell.setCellValue("N/A");
                        }
                    }
                    continue;
                }
                finally {
                    if (object != null) {
                        ((ResultsGroup)object).releaseLock("DatabankExport");
                    }
                }
            }
            for (n = 0; n < databankTableView.columns.size(); ++n) {
                sheet.autoSizeColumn(n);
            }
            if (!string.toLowerCase().endsWith(".xlsx")) {
                string = string + ".xlsx";
            }
            if (!(file = new File(string).getParentFile()).exists()) {
                file.mkdirs();
            }
            object = new FileOutputStream(string);
            xSSFWorkbook.write((OutputStream)object);
            ((FileOutputStream)object).close();
        }
        catch (Exception exception) {
            Log.error("Error while exporting databank '" + databank.getProject() + "/" + databank.getName() + "' to MS Office XLSX." + exception.getMessage(), (Throwable)exception);
            throw new Exception(L.t((String)"Error while exporting databank '%s/%s' to MS Office XLSX - %s", (Object[])new Object[]{databank.getProject(), databank.getName(), exception.getMessage()}), exception);
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

    private void setFormatedCellValue(Cell cell, DatabankTableColumnEntry databankTableColumnEntry, ResultsGroup resultsGroup, Workbook workbook, CellStyle cellStyle, CellStyle cellStyle2) {
        String string = databankTableColumnEntry.exportValue(resultsGroup);
        switch (databankTableColumnEntry.tableColumn.getType()) {
            case "Text": 
            case "Time": {
                cell.setCellValue(string);
                break;
            }
            case "Integer": {
                if (string == null || string.equals("")) {
                    cell.setCellValue(string);
                    break;
                }
                cell.setCellStyle(cellStyle);
                try {
                    cell.setCellValue((double)Integer.parseInt(string));
                }
                catch (NumberFormatException numberFormatException) {
                    cell.setCellValue((double)((int)Double.parseDouble(string)));
                }
                break;
            }
            default: {
                if (string == null || string.equals("")) {
                    cell.setCellValue(string);
                    break;
                }
                cell.setCellStyle(cellStyle2);
                cell.setCellValue(Double.parseDouble(string));
            }
        }
    }

    private String formatValue(DatabankTableColumnEntry databankTableColumnEntry, ResultsGroup resultsGroup, boolean bl) {
        String string = databankTableColumnEntry.exportValue(resultsGroup);
        if (bl) {
            switch (databankTableColumnEntry.tableColumn.getType()) {
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
        if (string != null) {
            if (string == "none") {
                return new ArrayList<String>();
            }
            if (!string.isEmpty()) {
                return new ArrayList<String>(Arrays.asList(string.split(",")));
            }
        }
        return databank.getRecordKeys();
    }
}

