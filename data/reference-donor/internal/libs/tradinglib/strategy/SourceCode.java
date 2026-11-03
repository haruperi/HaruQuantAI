/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerator
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerators
 *  com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.sourcecode.SourceCodeGenerator;
import com.strategyquant.lib.sourcecode.SourceCodeGenerators;
import com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.project.StrategyXMLModifier;
import com.strategyquant.tradinglib.strategy.xml.StrategyFixer;
import java.io.File;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SourceCode {
    private static final Logger Log = LoggerFactory.getLogger(SourceCode.class);

    public void generate(String string, String string2, String string3) throws Exception {
        SourceCodeGenerator sourceCodeGenerator;
        if (string == null || string2 == null || string3 == null) {
            if (string == null) {
                throw new Exception("generatorName cannot be null");
            }
            if (string2 == null) {
                throw new Exception("inputFileName cannot be null");
            }
            if (string3 == null) {
                throw new Exception("outputFileName cannot be null");
            }
        }
        if ((sourceCodeGenerator = SourceCodeGenerators.getInstance().getGeneratorFromName(SourceCode.getGeneratorName(string))) != null) {
            Log.info("Generating " + string + " code...");
            try {
                ResultsGroup resultsGroup;
                IProgram iProgram;
                File file = new File(string2);
                String string4 = file.getName();
                String string5 = null;
                if (string4.toLowerCase().endsWith(".sqx")) {
                    iProgram = Program.get((String)"Loader");
                    resultsGroup = (ResultsGroup)iProgram.call("loadFile", new Object[]{file.getAbsolutePath(), false});
                    string5 = XMLUtil.elementToString((Element)StrategyXMLModifier.getUpdatedStrategyXML(resultsGroup));
                } else {
                    string5 = SQUtils.fileToString((File)file);
                }
                iProgram = StrategyFixer.fixStrategy(string5);
                iProgram.setAttribute("hasHeikenAshi", string5.contains("HeikenAshi") ? "true" : "false");
                iProgram.setAttribute("isBrazilianVersion", sourceCodeGenerator.isBrazilianVersion() ? "true" : "false");
                resultsGroup = iProgram.getChild("Strategy");
                resultsGroup.setAttribute("Engine", string);
                StrategyXMLModifier.addOptions((Element)iProgram, string4, file.getAbsolutePath());
                XMLIndicatorsAnalyzer.init();
                XMLIndicatorsAnalyzer.fixItemAttributes((Element)resultsGroup);
                CustomDataManager.init((String)SQPaths.customDataDirPath);
                CustomDataManager.addCDataIndySourceCodes((Element)iProgram);
                CustomBlocks.addCBlockSourceCodes((Element)iProgram);
                String string6 = sourceCodeGenerator.getSource(SQUtils.stripExtension((String)string4), (Element)iProgram);
                SQUtils.stringToFile((File)new File(string3), (String)string6);
                Log.info("Source code generated");
            }
            catch (Exception exception) {
                Log.error("Generation failed", (Throwable)exception);
                throw new Exception("Generation failed - " + exception.getMessage(), exception);
            }
        } else {
            Log.error("Generator '" + string + "' not found");
            throw new Exception("Generator '" + string + "' not found");
        }
    }

    private static String getGeneratorName(String string) {
        switch (string) {
            case "MetaTrader4": {
                return SourceCodeGenerator.MetaTrader4;
            }
            case "MetaTrader5": {
                return SourceCodeGenerator.MetaTrader5;
            }
            case "EasyLanguage": {
                return SourceCodeGenerator.EasyLanguage;
            }
            case "PseudoCode": {
                return SourceCodeGenerator.PseudoCode;
            }
        }
        return string;
    }
}

