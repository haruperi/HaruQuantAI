/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.task.settings.blocks;

import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.tradinglib.blocks.random.BlockDefinition;
import com.strategyquant.tradinglib.blocks.random.BlocksConfig;
import com.strategyquant.tradinglib.generator.StrategyTemplateGenerator;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import java.util.List;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConfigVerifier {
    private static final Logger Log = LoggerFactory.getLogger(ConfigVerifier.class);

    public static void verifyConfig(Element element, BlocksConfig blocksConfig, TaskSettingsData taskSettingsData) {
        if (element == null) {
            ConfigVerifier.addError(taskSettingsData, "Invalid XML configuration - missing Settings element.");
        } else {
            ConfigVerifier.checkBlocksConfig(taskSettingsData, element, blocksConfig);
        }
    }

    private static void checkBlocksConfig(TaskSettingsData taskSettingsData, Element element, BlocksConfig blocksConfig) {
        Element element2 = element.getChild("Blocks");
        if (element2 == null) {
            ConfigVerifier.addError(taskSettingsData, "Cannot find Blocks settings.");
        } else {
            String string;
            Element element3;
            Element element4;
            Element element5 = null;
            Element element6 = element.getChild("Options");
            if (element6 != null && (element6 = element6.getChild("BuildTradingOptions")) != null) {
                element5 = element6.getChild("Params");
            }
            if ((element4 = element.getChild("WhatToBuild")) != null && (element3 = element4.getChild("StrategyType")) != null && (string = element3.getAttributeValue("type")) != null && string.equals("template")) {
                return;
            }
            boolean bl = ConfigVerifier.checkOrderTypes(taskSettingsData, element2);
            boolean bl2 = ConfigVerifier.checkExitTypes(taskSettingsData, element2, element5);
            ConfigVerifier.checkBlocks(taskSettingsData, element2, blocksConfig, bl, bl2, element);
        }
    }

    private static boolean checkExitTypes(TaskSettingsData taskSettingsData, Element element, Element element2) {
        boolean bl = false;
        Element element3 = element.getChild("ExitTypes");
        if (element3 == null) {
            ConfigVerifier.addError(taskSettingsData, "Cannot find Exit types settings.");
            return false;
        }
        if (ConfigVerifier.getUsedBlocksCount(element3.getChildren("Block")) == 0) {
            if (!ConfigVerifier.checkExitOnDayFridayIsUsed(element2)) {
                ConfigVerifier.addError(taskSettingsData, "You have to choose at least one of the Exit Types!");
                return false;
            }
            return true;
        }
        for (Element element4 : element3.getChildren("Block")) {
            boolean bl2 = false;
            int n = 0;
            String string = element4.getAttributeValue("use");
            if (string != null && string.equals("false") || element4.getAttributeValue("type") == null || !element4.getAttributeValue("type").equals("formula")) continue;
            for (Element element5 : element4.getChildren("Value")) {
                bl2 = true;
                if (!element5.getAttributeValue("use").equals("true")) continue;
                ++n;
                String string2 = element5.getAttributeValue("key");
                if (!string2.contains(".PriceLevel")) continue;
                bl = true;
            }
            if (!bl2 || n != 0) continue;
            ConfigVerifier.addError(taskSettingsData, String.format("You have chosen Exit type '%s' to be used, but you didn't select any of its options!", element4.getAttributeValue("key")));
        }
        return bl;
    }

    private static boolean checkExitOnDayFridayIsUsed(Element element) {
        if (element == null) {
            return false;
        }
        List list = element.getChildren("Param");
        boolean bl = false;
        for (int i = 0; i < list.size(); ++i) {
            String string;
            Element element2 = (Element)list.get(i);
            String string2 = element2.getAttributeValue("key");
            if ((string2.equals("ExitAtEndOfDay") || string2.equals("ExitOnFriday")) && (string = element2.getText()) != null && string.equals("true")) {
                return true;
            }
            if (string2.equals("LimitTimeRange") && (string = element2.getText()) != null && string.equals("true")) {
                bl = true;
            }
            if (!string2.equals("ExitAtEndOfRange") || !bl || (string = element2.getText()) == null || !string.equals("true")) continue;
            return true;
        }
        return false;
    }

    private static int getUsedBlocksCount(List<Element> list) {
        int n = 0;
        for (Element element : list) {
            String string = element.getAttributeValue("use");
            if (string == null || !string.equals("true")) continue;
            ++n;
        }
        return n;
    }

    private static boolean checkOrderTypes(TaskSettingsData taskSettingsData, Element element) {
        Element element2 = element.getChild("OrderTypes");
        if (element2 == null) {
            ConfigVerifier.addError(taskSettingsData, "Cannot find Order types settings.");
        }
        boolean bl = false;
        boolean bl2 = false;
        for (Element element3 : element2.getChildren("Block")) {
            if (!element3.getAttributeValue("use").equals("true")) continue;
            bl = true;
            for (Element element4 : element3.getChild("Generated").getChildren("Param")) {
                if (!element4.getAttributeValue("key").equals("#Price#")) continue;
                bl2 = true;
            }
        }
        if (!bl) {
            ConfigVerifier.addError(taskSettingsData, "You have to choose at least one of Order Type blocks!");
        }
        return bl2;
    }

    private static void checkBlocks(TaskSettingsData taskSettingsData, Element element, BlocksConfig blocksConfig, boolean bl, boolean bl2, Element element2) {
        Element element3 = element.getChild("BuildingBlocks");
        if (element3 == null) {
            ConfigVerifier.addError(taskSettingsData, "Cannot find Building blocks settings.");
        } else {
            BlocksExists blocksExists = new BlocksExists();
            ConfigVerifier.checkStandardBlocks(blocksExists, element3, taskSettingsData, blocksConfig);
            ConfigVerifier.checkCustomDataBlocks(blocksExists, element);
            ConfigVerifier.checkRandomBlockGroups(blocksExists, taskSettingsData, blocksConfig, element2);
            if (!blocksExists.blocksFound) {
                ConfigVerifier.addError(taskSettingsData, "You have to choose at least one building block!");
            }
            if (!blocksExists.booleanBlockFound && !blocksExists.valueBlockFound) {
                ConfigVerifier.addError(taskSettingsData, "You have to choose at least one signal or indicator block!");
            }
            if (blocksExists.valueBlockFound && !blocksExists.comparisonBlocksFound) {
                ConfigVerifier.addError(taskSettingsData, "You have chosen some indicators or price values, but no comparison operators!\nEither choose some operators or deselect all indicator / price blocks.");
            }
            if (!blocksExists.valueBlockFound && blocksExists.comparisonBlocksFound) {
                ConfigVerifier.addError(taskSettingsData, "You have chosen some operators (<, >, Is rising, etc.) blocks, but no price / indicators blocks to compare!\nEither choose some price or indicator blocks, or deselect all operators.");
            }
            if (bl) {
                if (!blocksExists.priceLevelFound) {
                    ConfigVerifier.addError(taskSettingsData, "You use Enter at Stop or Limit, you have to choose some Price Level blocks!");
                }
                if (!blocksExists.priceRangeFound) {
                    // empty if block
                }
            }
            if (bl2) {
                if (!blocksExists.priceLevelFound) {
                    ConfigVerifier.addError(taskSettingsData, "You use Indicators in exits (Stop Loss or Profit Target, Trailing Stop etc.), you have to choose some Price Level blocks!");
                }
                if (!blocksExists.priceRangeFound) {
                    // empty if block
                }
            }
            if (!(blocksExists.priceLevelFound && blocksExists.priceRangeFound || !ConfigVerifier.usesIndicatorLevelsForExits(element))) {
                ConfigVerifier.addError(taskSettingsData, "You use Indicator levels in some of the exit types (Stop Loss, Profit Target or Trailing stop), but you haven't chosen any Price or Price Range block!");
            }
        }
    }

    private static void checkRandomBlockGroups(BlocksExists blocksExists, TaskSettingsData taskSettingsData, BlocksConfig blocksConfig, Element element) {
        Element element2;
        Element element3 = element.getChild("WhatToBuild");
        String string = element3.getChild("StrategyType").getAttributeValue("type");
        if (!string.equals("template")) {
            return;
        }
        try {
            element2 = StrategyTemplateGenerator.getConfiguredTemplate(element, null);
            if (element2 == null) {
                return;
            }
        }
        catch (Exception exception) {
            Log.error("Cannot get template", (Throwable)exception);
            return;
        }
        Element element4 = element2.getChild("Strategy").getChild("RandomGroups");
        if (element4 == null) {
            return;
        }
        for (Element element5 : element4.getChildren("Group")) {
            String string2 = element5.getAttributeValue("id");
            for (Element element6 : element5.getChildren("Item")) {
                String string3 = element6.getAttributeValue("key");
                if (string3 == null || string3.equals("")) {
                    ConfigVerifier.addError(taskSettingsData, "Some block element in Random group doesn't contain 'key' attribute!");
                    continue;
                }
                ConfigVerifier.checkBlockRandomGroup(blocksExists, string3, taskSettingsData, blocksConfig, element2, element4, string2);
            }
        }
    }

    private static void checkStandardBlocks(BlocksExists blocksExists, Element element, TaskSettingsData taskSettingsData, BlocksConfig blocksConfig) {
        for (Element element2 : element.getChildren("Block")) {
            String string = element2.getAttributeValue("use");
            if (string.equals("false")) continue;
            blocksExists.blocksFound = true;
            String string2 = element2.getAttributeValue("key");
            if (string2 == null || string2.equals("")) {
                ConfigVerifier.addError(taskSettingsData, "Some block element doesn't contain 'key' attribute!");
                continue;
            }
            if (!ConfigVerifier.checkBlock(blocksExists, string2, taskSettingsData, blocksConfig)) continue;
            Element element3 = element2.getChild("Generated");
            if (element3 == null) {
                ConfigVerifier.addError(taskSettingsData, String.format("Block '%s' doesn't contain <Generated> child!", string2));
                continue;
            }
            String string3 = element3.getAttributeValue("weight");
            if (string3 == null) {
                ConfigVerifier.addError(taskSettingsData, String.format("Block '%s' doesn't contain weight attribute in its <Generated> child!", string2));
                continue;
            }
            if (!string3.equals("0")) {
                // empty if block
            }
            if (element2.getChild("Predefined") == null) continue;
            for (Element element4 : element2.getChild("Predefined").getChildren()) {
                String string4 = element4.getAttributeValue("weight");
                if (string4 != null && string4.equals("0")) continue;
            }
        }
    }

    private static boolean checkBlock(BlocksExists blocksExists, String string, TaskSettingsData taskSettingsData, BlocksConfig blocksConfig) {
        BlockDefinition blockDefinition;
        if (string.equals("RandomlyGeneratedPatterns")) {
            return false;
        }
        if (string.equalsIgnoreCase("AND") || string.equalsIgnoreCase("OR")) {
            return false;
        }
        String string2 = string;
        if (string.contains(".")) {
            string = string.substring(string.indexOf(".") + 1);
        }
        if ((blockDefinition = blocksConfig.getBlock(string)) == null) {
            ConfigVerifier.addError(taskSettingsData, String.format("Cannot find Building block with key '%s'.", string));
        } else {
            if (blockDefinition.superType == 2) {
                blocksExists.comparisonBlocksFound = true;
            }
            if (blockDefinition.superType == 1) {
                blocksExists.comparisonBlocksFound = true;
            }
            if (blockDefinition.superType == 2 || blockDefinition.superType == 3 || blockDefinition.superType == 1) {
                blocksExists.booleanBlockFound = true;
            }
            if (blockDefinition.superType == 4 && !string2.contains("Stop/Limit Price Range") && !string2.contains("Stop/Limit Price Level")) {
                blocksExists.valueBlockFound = true;
            }
            if (blockDefinition.returnType == 7 && string2.contains("Stop/Limit Price Range")) {
                blocksExists.priceRangeFound = true;
            }
            if (blockDefinition.returnType == 2 && string2.contains("Stop/Limit Price Level")) {
                blocksExists.priceLevelFound = true;
            }
        }
        return true;
    }

    private static boolean checkBlockRandomGroup(BlocksExists blocksExists, String string, TaskSettingsData taskSettingsData, BlocksConfig blocksConfig, Element element, Element element2, String string2) {
        BlockDefinition blockDefinition;
        if (string.equals("RandomlyGeneratedPatterns")) {
            return false;
        }
        if (string.equalsIgnoreCase("AND") || string.equalsIgnoreCase("OR")) {
            return false;
        }
        if (string.contains(".")) {
            string = string.substring(string.indexOf(".") + 1);
        }
        if ((blockDefinition = blocksConfig.getBlock(string)) == null) {
            ConfigVerifier.addError(taskSettingsData, String.format("Cannot find Building block with key '%s'.", string));
        } else {
            if (blockDefinition.superType == 2) {
                blocksExists.comparisonBlocksFound = true;
            }
            if (blockDefinition.superType == 2 || blockDefinition.superType == 3 || blockDefinition.superType == 1) {
                blocksExists.booleanBlockFound = true;
            }
            if (blockDefinition.superType == 4) {
                if (ConfigVerifier.randomGroupUsedInPrice(string2, element)) {
                    blocksExists.priceRangeFound = true;
                    blocksExists.priceLevelFound = true;
                } else {
                    blocksExists.valueBlockFound = true;
                }
            }
        }
        return true;
    }

    private static boolean randomGroupUsedInPrice(String string, Element element) {
        Element element2;
        String string2;
        Object object;
        if (element.getName().equals("Param") && (object = element.getAttributeValue("key")) != null && ((String)object).equals("#Group#") && (string2 = element.getText()).equals(string)) {
            element2 = element.getParentElement();
            for (int i = 0; i < 6; ++i) {
                String string3 = element2.getAttributeValue("key");
                if (string3 != null && string3.equals("#Price#")) {
                    return true;
                }
                element2 = element2.getParentElement();
            }
        }
        if ((object = element.getChildren()) != null && object.size() > 0) {
            for (int i = 0; i < object.size(); ++i) {
                element2 = (Element)object.get(i);
                if (!ConfigVerifier.randomGroupUsedInPrice(string, element2)) continue;
                return true;
            }
        }
        return false;
    }

    private static void checkCustomDataBlocks(BlocksExists blocksExists, Element element) {
        Element element2 = element.getChild("CustomData");
        if (element2 != null) {
            for (Element element3 : element2.getChildren("Data")) {
                String string = element3.getAttributeValue("use");
                if (string == null || !string.equals("true")) continue;
                String string2 = element3.getAttributeValue("name");
                CustomDataInfo customDataInfo = CustomDataManager.getDataInfo((String)string2);
                if (customDataInfo == null) {
                    Log.info("Cannot find custom data indicator '{}', ignoring!", (Object)string2);
                    continue;
                }
                switch (customDataInfo.dataType) {
                    case 1: {
                        blocksExists.priceLevelFound = true;
                        blocksExists.valueBlockFound = true;
                        break;
                    }
                    case 2: {
                        blocksExists.valueBlockFound = true;
                        break;
                    }
                    case 3: {
                        blocksExists.priceRangeFound = true;
                        break;
                    }
                    case 10: 
                    case 11: {
                        blocksExists.booleanBlockFound = true;
                    }
                }
            }
        }
    }

    private static boolean usesIndicatorLevelsForExits(Element element) {
        Element element2 = element.getChild("ExitTypes");
        if (element2 == null) {
            return false;
        }
        if (ConfigVerifier.getUsedBlocksCount(element2.getChildren("Block")) == 0) {
            return false;
        }
        for (Element element3 : element2.getChildren("Block")) {
            if (element3.getAttributeValue("type") == null || !element3.getAttributeValue("type").equals("formula") || !element3.getAttributeValue("key").equals("true")) continue;
            for (Element element4 : element3.getChildren("Value")) {
                if (!element4.getAttributeValue("use").equals("true") || !element4.getAttributeValue("key").contains("PriceLevel")) continue;
                return true;
            }
        }
        return false;
    }

    private static void addError(TaskSettingsData taskSettingsData, String string) {
        taskSettingsData.addError("Blocks", null, string);
    }

    private static class BlocksExists {
        boolean booleanBlockFound = false;
        boolean priceRangeFound = false;
        boolean priceLevelFound = false;
        boolean blocksFound = false;
        boolean valueBlockFound = false;
        boolean comparisonBlocksFound = false;

        private BlocksExists() {
        }
    }
}

