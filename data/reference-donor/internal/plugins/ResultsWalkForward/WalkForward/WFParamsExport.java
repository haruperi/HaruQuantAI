/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.WalkForwardPeriod
 *  com.strategyquant.tradinglib.WalkForwardResult
 *  com.strategyquant.tradinglib.databank.DatabankTableColumnEntry
 *  com.strategyquant.tradinglib.databank.DatabankTableView
 *  org.apache.poi.ss.usermodel.Cell
 *  org.apache.poi.ss.usermodel.CellStyle
 *  org.apache.poi.ss.usermodel.Font
 *  org.apache.poi.ss.usermodel.IndexedColors
 *  org.apache.poi.ss.usermodel.Row
 *  org.apache.poi.ss.usermodel.Sheet
 *  org.apache.poi.xssf.usermodel.XSSFWorkbook
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.WalkForward;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.WalkForwardPeriod;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.util.ArrayList;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.CellStyle;
import org.apache.poi.ss.usermodel.Font;
import org.apache.poi.ss.usermodel.IndexedColors;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WFParamsExport {
    private static final Logger Log = LoggerFactory.getLogger(WFParamsExport.class);

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void toXlsx(String path, boolean useComma, WalkForwardResult wfResult, DatabankTableView view) {
        XSSFWorkbook workbook = null;
        try {
            int i;
            workbook = new XSSFWorkbook();
            Sheet sheet = workbook.createSheet("Tradelist");
            Font headerFont = workbook.createFont();
            headerFont.setBold(true);
            headerFont.setFontHeightInPoints((short)14);
            headerFont.setColor(IndexedColors.RED.getIndex());
            CellStyle headerCellStyle = workbook.createCellStyle();
            headerCellStyle.setFont(headerFont);
            Row headerRow = sheet.createRow(0);
            Cell cell = headerRow.createCell(1);
            cell.setCellValue("Period IS");
            cell.setCellStyle(headerCellStyle);
            cell = headerRow.createCell(2);
            cell.setCellValue("Period OOS");
            cell.setCellStyle(headerCellStyle);
            cell = headerRow.createCell(3);
            cell.setCellValue("Days IS");
            cell.setCellStyle(headerCellStyle);
            cell = headerRow.createCell(4);
            cell.setCellValue("Days OOS");
            cell.setCellStyle(headerCellStyle);
            for (i = 0; i < view.columns.size(); ++i) {
                cell = headerRow.createCell(i + 5);
                cell.setCellValue(((DatabankTableColumnEntry)view.columns.get(i)).getColumnEntryName());
                cell.setCellStyle(headerCellStyle);
            }
            cell = headerRow.createCell(i + 5);
            cell.setCellValue("Parameters");
            cell.setCellStyle(headerCellStyle);
            ArrayList periods = wfResult.wfPeriods;
            for (i = 0; i < periods.size(); ++i) {
                int columnIndex;
                Row row = sheet.createRow(i + 1);
                WalkForwardPeriod period = (WalkForwardPeriod)periods.get(i);
                cell = row.createCell(1);
                cell.setCellValue(SQTime.toDateString((long)period.optimizeFrom) + " - " + SQTime.toDateString((long)period.optimizeTo));
                cell = row.createCell(2);
                if (i == periods.size() - 1) {
                    cell.setCellValue(SQTime.toDateString((long)period.runFrom) + " - " + SQTime.toDateString((long)period.runTo) + " (future)");
                } else {
                    cell.setCellValue(SQTime.toDateString((long)period.runFrom) + " - " + SQTime.toDateString((long)period.runTo));
                }
                cell = row.createCell(3);
                cell.setCellValue((double)SQTime.getDaysBetween((long)period.optimizeFrom, (long)period.optimizeTo));
                cell = row.createCell(4);
                cell.setCellValue((double)SQTime.getDaysBetween((long)period.runFrom, (long)period.runTo));
                ArrayList columns = view.columns;
                for (columnIndex = 0; columnIndex < columns.size(); ++columnIndex) {
                    DatabankTableColumnEntry columnEntry = (DatabankTableColumnEntry)columns.get(columnIndex);
                    DatabankColumn column = columnEntry.tableColumn;
                    cell = row.createCell(columnIndex + 5);
                    try {
                        String value = columnEntry.sampleType == 10 ? column.printValue(period.optimizationStatData) : column.printValue(period.runStatData);
                        String formattedValue = this.formatValue(columnEntry, value, useComma);
                        cell.setCellValue(formattedValue);
                        continue;
                    }
                    catch (Exception e) {
                        cell.setCellValue("N/A");
                    }
                }
                cell = row.createCell(columnIndex + 5);
                cell.setCellValue(period.testParameters);
            }
            for (i = 0; i < view.columns.size(); ++i) {
                sheet.autoSizeColumn(i);
            }
            if (!path.toLowerCase().endsWith(".xlsx")) {
                path = path + ".xlsx";
            }
            FileOutputStream fileOut = new FileOutputStream(path);
            workbook.write((OutputStream)fileOut);
            fileOut.close();
        }
        catch (Exception e) {
            Log.error("Error while exporting WF params to xlsx.", (Throwable)e);
        }
        finally {
            try {
                if (workbook != null) {
                    workbook.close();
                }
            }
            catch (Exception e) {
                Log.error("Cannot close workbook", (Throwable)e);
            }
        }
    }

    public void toCsv(String path, boolean useComma, WalkForwardResult wfResult, DatabankTableView view) {
        try {
            if (!path.toLowerCase().endsWith(".csv")) {
                path = path + ".csv";
            }
            PrintWriter writer = new PrintWriter(path);
            writer.print("\"Period IS\";");
            writer.print("\"Period OOS\";");
            writer.print("\"Days IS\";");
            writer.print("\"Days OOS\";");
            int columnsCount = view.columns.size();
            for (int i = 0; i < columnsCount; ++i) {
                writer.print("\"" + ((DatabankTableColumnEntry)view.columns.get(i)).getColumnEntryName() + "\";");
            }
            writer.print("\"Parameters\"");
            writer.println();
            ArrayList periods = wfResult.wfPeriods;
            for (int i = 0; i < periods.size(); ++i) {
                WalkForwardPeriod period = (WalkForwardPeriod)periods.get(i);
                writer.print("\"" + SQTime.toDateString((long)period.optimizeFrom) + " - " + SQTime.toDateString((long)period.optimizeTo) + "\";");
                if (i == periods.size() - 1) {
                    writer.print("\"" + SQTime.toDateString((long)period.runFrom) + " - " + SQTime.toDateString((long)period.runTo) + " (future)\";");
                } else {
                    writer.print("\"" + SQTime.toDateString((long)period.runFrom) + " - " + SQTime.toDateString((long)period.runTo) + "\";");
                }
                writer.print("\"" + SQTime.getDaysBetween((long)period.optimizeFrom, (long)period.optimizeTo) + "\";");
                writer.print("\"" + SQTime.getDaysBetween((long)period.runFrom, (long)period.runTo) + "\";");
                ArrayList columns = view.columns;
                for (int columnIndex = 0; columnIndex < columns.size(); ++columnIndex) {
                    DatabankTableColumnEntry columnEntry = (DatabankTableColumnEntry)columns.get(columnIndex);
                    DatabankColumn column = columnEntry.tableColumn;
                    try {
                        String value = columnEntry.sampleType == 10 ? column.printValue(period.optimizationStatData) : column.printValue(period.runStatData);
                        String formattedValue = this.formatValue(columnEntry, value, useComma);
                        writer.print("\"" + formattedValue + "\";");
                        continue;
                    }
                    catch (Exception e) {
                        writer.print("\"N/A\";");
                    }
                }
                writer.print("\"" + period.testParameters + "\"");
                writer.println();
            }
            writer.flush();
            writer.close();
        }
        catch (Exception e) {
            Log.error("Error while exporting WF params to csv.", (Throwable)e);
        }
    }

    private String formatValue(DatabankTableColumnEntry column, String value, boolean useComma) {
        value = SQUtils.removeHtmlTags((String)value);
        if (useComma) {
            switch (column.tableColumn.getType()) {
                case "Integer": 
                case "Text": 
                case "Time": {
                    return value;
                }
            }
            return value.replace('.', ',');
        }
        return value;
    }
}

