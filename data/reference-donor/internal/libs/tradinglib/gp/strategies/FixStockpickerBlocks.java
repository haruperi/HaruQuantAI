/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlockParameter;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.generator.GenerateException;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.IEvolutionaryOperator;
import com.strategyquant.tradinglib.gp.strategies.Node;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FixStockpickerBlocks
implements IEvolutionaryOperator<Node> {
    private static final Logger Log = LoggerFactory.getLogger((String)"FixStockpickerBlocks");
    private BlocksConfig _blocksConfig;

    public FixStockpickerBlocks() throws GenerateException {
        try {
            this._blocksConfig = BlocksConfig.getConfig();
        }
        catch (Exception exception) {
            throw new GenerateException("Cannot initialize blocks config!", exception);
        }
    }

    @Override
    public List<Node> apply(List<Node> list, IRandomGenerator iRandomGenerator, AbstractFactory<Node> abstractFactory, int n, int n2) throws Exception {
        for (int i = 0; i < list.size(); ++i) {
            Node node = list.get(i);
            FixStockpickerBlocks.fixSPStrategy(node.getStrategy(), this._blocksConfig);
        }
        return list;
    }

    public static void fixSPStrategy(Element element, BlocksConfig blocksConfig) throws GenerateException {
        Element element2 = element.getChild("Strategy");
        String string = element2.getAttributeValue("engine");
        if (string != null && !string.equals("Stockpicker") && !string.equals("Single-asset cloud strategy")) {
            return;
        }
        FixStockpickerBlocks.fixSPParamIssues(element, blocksConfig);
    }

    private static void fixSPParamIssues(Element element, BlocksConfig blocksConfig) {
        List list;
        if (element.getName().equals("Item")) {
            FixStockpickerBlocks.fixSPParamIssuesOnItem(element, blocksConfig);
        }
        if ((list = element.getChildren()) != null && list.size() > 0) {
            for (int i = 0; i < list.size(); ++i) {
                Element element2 = (Element)list.get(i);
                FixStockpickerBlocks.fixSPParamIssues(element2, blocksConfig);
            }
        }
    }

    private static void fixSPParamIssuesOnItem(Element element, BlocksConfig blocksConfig) {
        String string = element.getAttributeValue("key");
        if (string == null) {
            return;
        }
        if (string.startsWith("talib_")) {
            FixStockpickerBlocks.fixTALibParams(string, element, blocksConfig);
        } else {
            FixStockpickerBlocks.fixDWMBlockShift(string, element);
        }
    }

    private static void fixDWMBlockShift(String string, Element element) {
        Object object;
        if (!(string.endsWith("D") || string.endsWith("W") || string.endsWith("M") || string.startsWith("Open") || string.endsWith("High") || string.endsWith("Low") || string.endsWith("Close"))) {
            return;
        }
        if ((string.endsWith("Open") || string.endsWith("High") || string.endsWith("Low") || string.endsWith("Close")) && ((object = element.getAttributeValue("generated")) == null || ((String)object).equals("none"))) {
            return;
        }
        object = element.getChildren("Param");
        for (int i = 0; i < object.size(); ++i) {
            String string2;
            Element element2 = (Element)object.get(i);
            String string3 = element2.getAttributeValue("key");
            if (string3 == null || !string3.equals("#Shift#") || (string2 = element2.getText()) == null || !string2.equals("0")) continue;
            element2.setText("1");
            if (!Log.isDebugEnabled()) continue;
            Log.debug("Corrected Shift value 0->1, for {}", (Object)string2, (Object)string);
        }
    }

    private static void fixTALibParams(String string, Element element, BlocksConfig blocksConfig) {
        BlockDefinition blockDefinition = blocksConfig.getBlock(string);
        if (blockDefinition == null) {
            return;
        }
        List list = element.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            String string2;
            BlockParameter blockParameter;
            Element element2 = (Element)list.get(i);
            String string3 = element2.getAttributeValue("key");
            if (string3 == null || (blockParameter = blockDefinition.getParamByKey(string3)) == null || FixStockpickerBlocks.isCustomParamReference(element2)) continue;
            if (blockParameter.paramType != null) {
                double d;
                if (blockParameter.paramType.equals("period")) {
                    double d2;
                    string2 = element2.getText();
                    if (string2 == null || !((d2 = Double.parseDouble(string2)) < 2.0)) continue;
                    if (Log.isDebugEnabled()) {
                        Log.debug("Corrected period value from {} to 2, param: {}", (Object)string2, (Object)XMLUtil.elementToString((Element)element2));
                    }
                    element2.setText("2");
                    continue;
                }
                if (!blockParameter.paramType.equals("shift") || (string2 = element2.getText()) == null || !((d = Double.parseDouble(string2)) < 0.0)) continue;
                if (Log.isDebugEnabled()) {
                    Log.debug("Corrected shift value from {} to 1 (min), param: {}", (Object)string2, (Object)XMLUtil.elementToString((Element)element2));
                }
                element2.setText("1");
                continue;
            }
            if (blockParameter.controlType == null || !blockParameter.controlType.equals("combo") || blockParameter.values == null || (string2 = element2.getText()) == null) continue;
            String[] stringArray = blockParameter.values.split(",");
            boolean bl = false;
            String string4 = null;
            for (int j = 0; j < stringArray.length; ++j) {
                String[] stringArray2 = stringArray[j].split("=");
                String string5 = stringArray2[1];
                if (j == 0) {
                    string4 = string5;
                }
                if (!string2.equals(string5)) continue;
                bl = true;
                break;
            }
            if (bl) continue;
            if (Log.isDebugEnabled()) {
                Log.debug("Corrected value outside range from {}, param: {}", (Object)string2, (Object)XMLUtil.elementToString((Element)element2));
            }
            if (blockParameter.defaultValue != null) {
                element2.setText(blockParameter.defaultValue);
                continue;
            }
            element2.setText(string4);
        }
    }

    private static boolean isCustomParamReference(Element element) {
        if ("true".equals(element.getAttributeValue("customParam"))) {
            return true;
        }
        String string = element.getText();
        return string != null && string.length() >= 2 && string.startsWith("#") && string.endsWith("#");
    }
}

