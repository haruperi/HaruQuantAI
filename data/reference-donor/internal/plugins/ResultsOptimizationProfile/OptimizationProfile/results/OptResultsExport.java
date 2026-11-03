/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.DatabankTableColumnEntry
 *  com.strategyquant.tradinglib.databank.DatabankTableView
 *  com.strategyquant.tradinglib.optimization.OptimizationProfile
 *  com.strategyquant.tradinglib.optimization.OptimizationTestResult
 *  it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
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
package com.strategyquant.plugin.Results.impl.OptimizationProfile.results;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.OptimizationTestResult;
import it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
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

public class OptResultsExport {
    private static final Logger Log = LoggerFactory.getLogger(OptResultsExport.class);

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void toXlsx(String path, boolean useComma, ResultsGroup rg, String xaxis, String yaxis, String zaxis, String type, String chartType, DatabankTableView view) {
        XSSFWorkbook workbook = null;
        try {
            Cell cell;
            int i;
            workbook = new XSSFWorkbook();
            Sheet sheet = workbook.createSheet("OptResults");
            Font headerFont = workbook.createFont();
            headerFont.setBold(true);
            headerFont.setFontHeightInPoints((short)14);
            headerFont.setColor(IndexedColors.RED.getIndex());
            CellStyle headerCellStyle = workbook.createCellStyle();
            headerCellStyle.setFont(headerFont);
            Row headerRow = sheet.createRow(0);
            for (i = 0; i < view.columns.size(); ++i) {
                cell = headerRow.createCell(i);
                cell.setCellValue(((DatabankTableColumnEntry)view.columns.get(i)).getColumnEntryName());
                cell.setCellStyle(headerCellStyle);
            }
            if (chartType.equals("3D")) {
                cell = headerRow.createCell(i);
                cell.setCellValue(xaxis);
                cell.setCellStyle(headerCellStyle);
                cell = headerRow.createCell(i + 1);
                cell.setCellValue(yaxis);
                cell.setCellStyle(headerCellStyle);
            } else if (chartType.equals("2D")) {
                cell = headerRow.createCell(i);
                cell.setCellValue(xaxis);
                cell.setCellStyle(headerCellStyle);
            }
            OptimizationProfile optimizationProfile = rg.getOptimizationProfile();
            ObjectArrayList localOptimizations = optimizationProfile.getOptimizations().clone();
            for (i = 0; i < localOptimizations.size(); ++i) {
                int columnIndex;
                OptimizationTestResult result = (OptimizationTestResult)localOptimizations.get(i);
                Int2DoubleOpenHashMap params = result.parseParams();
                Row row = sheet.createRow(i + 1);
                ArrayList columns = view.columns;
                for (columnIndex = 0; columnIndex < columns.size(); ++columnIndex) {
                    DatabankTableColumnEntry columnEntry = (DatabankTableColumnEntry)columns.get(columnIndex);
                    DatabankColumn column = columnEntry.tableColumn;
                    cell = row.createCell(columnIndex);
                    try {
                        String value = column.printValue(result.stats);
                        String formattedValue = this.formatValue(columnEntry, value, useComma);
                        cell.setCellValue(formattedValue);
                        continue;
                    }
                    catch (Exception e) {
                        cell.setCellValue("N/A");
                    }
                }
                if (chartType.equals("3D")) {
                    if (params.containsKey(xaxis.hashCode())) {
                        double xValue = params.get(xaxis.hashCode());
                        cell = row.createCell(columnIndex);
                        cell.setCellValue(xValue);
                    } else {
                        cell = row.createCell(columnIndex);
                        cell.setCellValue("N/A");
                    }
                    if (params.containsKey(yaxis.hashCode())) {
                        double yValue = params.get(yaxis.hashCode());
                        cell = row.createCell(columnIndex + 1);
                        cell.setCellValue(yValue);
                        continue;
                    }
                    cell = row.createCell(columnIndex + 1);
                    cell.setCellValue("N/A");
                    continue;
                }
                if (!chartType.equals("2D")) continue;
                if (params.containsKey(xaxis.hashCode())) {
                    double xValue = params.get(xaxis.hashCode());
                    cell = row.createCell(columnIndex);
                    cell.setCellValue(xValue);
                    continue;
                }
                cell = row.createCell(columnIndex);
                cell.setCellValue("N/A");
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
            Log.error("Error while exporting Optimization Results to xlsx.", (Throwable)e);
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

    public void toCsv(String path, boolean useComma, ResultsGroup rg, String xaxis, String yaxis, String zaxis, String type, String chartType, DatabankTableView view) {
        try {
            if (!path.toLowerCase().endsWith(".csv")) {
                path = path + ".csv";
            }
            PrintWriter writer = new PrintWriter(path);
            int columnsCount = view.columns.size();
            for (int i = 0; i < columnsCount; ++i) {
                writer.print("\"" + ((DatabankTableColumnEntry)view.columns.get(i)).getColumnEntryName() + "\";");
            }
            if (chartType.equals("3D")) {
                writer.print("\"" + xaxis + "\";");
                writer.print("\"" + yaxis + "\"");
            } else if (chartType.equals("2D")) {
                writer.print("\"" + xaxis + "\"");
            }
            writer.println();
            OptimizationProfile optimizationProfile = rg.getOptimizationProfile();
            ObjectArrayList localOptimizations = optimizationProfile.getOptimizations().clone();
            for (int i = 0; i < localOptimizations.size(); ++i) {
                OptimizationTestResult result = (OptimizationTestResult)localOptimizations.get(i);
                Int2DoubleOpenHashMap params = result.parseParams();
                ArrayList columns = view.columns;
                for (int columnIndex = 0; columnIndex < columns.size(); ++columnIndex) {
                    DatabankTableColumnEntry columnEntry = (DatabankTableColumnEntry)columns.get(columnIndex);
                    DatabankColumn column = columnEntry.tableColumn;
                    try {
                        String value = column.printValue(result.stats);
                        String formattedValue = this.formatValue(columnEntry, value, useComma);
                        writer.print("\"" + formattedValue + "\";");
                        continue;
                    }
                    catch (Exception e) {
                        writer.print("\"N/A\";");
                    }
                }
                if (chartType.equals("3D")) {
                    if (params.containsKey(xaxis.hashCode())) {
                        double xValue = params.get(xaxis.hashCode());
                        writer.print("\"" + xValue + "\";");
                    } else {
                        writer.print("\"N/A\";");
                    }
                    if (params.containsKey(yaxis.hashCode())) {
                        double yValue = params.get(yaxis.hashCode());
                        writer.print("\"" + yValue + "\"");
                    } else {
                        writer.print("\"N/A\"");
                    }
                } else if (chartType.equals("2D")) {
                    if (params.containsKey(xaxis.hashCode())) {
                        double xValue = params.get(xaxis.hashCode());
                        writer.print("\"" + xValue + "\"");
                    } else {
                        writer.print("\"N/A\"");
                    }
                }
                writer.println();
            }
            writer.flush();
            writer.close();
        }
        catch (Exception e) {
            Log.error("Error while exporting Optimization Results to csv.", (Throwable)e);
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

