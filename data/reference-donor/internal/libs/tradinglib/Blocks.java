/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.snippets.CustomClassesLoader
 *  com.strategyquant.lib.snippets.CustomClassesReg
 *  com.strategyquant.lib.snippets.ICustomClasses
 *  com.strategyquant.lib.snippets.SnippetsCompiler
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntIterator
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.snippets.CustomClassesLoader;
import com.strategyquant.lib.snippets.CustomClassesReg;
import com.strategyquant.lib.snippets.ICustomClasses;
import com.strategyquant.lib.snippets.SnippetsCompiler;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.BuildingBlock;
import com.strategyquant.tradinglib.CategoryOrder;
import com.strategyquant.tradinglib.ExitMethod;
import com.strategyquant.tradinglib.ForEngine;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.IgnoreInBuilder;
import com.strategyquant.tradinglib.Indicator;
import com.strategyquant.tradinglib.MT5ExtendedTemplate;
import com.strategyquant.tradinglib.NotFirstValue;
import com.strategyquant.tradinglib.OppositeBlock;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.ParameterSet;
import com.strategyquant.tradinglib.ReturnTypes;
import com.strategyquant.tradinglib.SortOrder;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.blocks.AnnotationProcessor;
import com.strategyquant.tradinglib.blocks.BlockCategoryInfo;
import com.strategyquant.tradinglib.blocks.BlockComparatorByOrder;
import com.strategyquant.tradinglib.blocks.CategoryComparatorByOrder;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.blocks.OppositeBlocksConfig;
import com.strategyquant.tradinglib.blocks.OutputAnnotationHandler;
import com.strategyquant.tradinglib.blocks.annotations.ParameterSets;
import com.strategyquant.tradinglib.exit.ExitMethodsList;
import com.strategyquant.tradinglib.talib.TALibIndicator;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntIterator;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.TreeMap;
import org.jdom2.Content;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Blocks
implements ICustomClasses {
    public static final Logger Log = LoggerFactory.getLogger((String)"Blocks");
    private static Blocks instance;
    private Int2ObjectOpenHashMap<IBlock> mapClasses = new Int2ObjectOpenHashMap();
    private HashMap<String, ArrayList<BlockCategoryInfo>> sortedCategories = new HashMap();
    private Int2ObjectOpenHashMap<ArrayList<IBlock>> sortedBlocks = new Int2ObjectOpenHashMap();
    private HashMap<String, String> oppositeBlocksCache = null;
    private Comparator<IBlock> comparatorByOrder;
    private Comparator<BlockCategoryInfo> categoryComparatorByOrder;

    private Blocks() {
        CustomClassesReg.add((ICustomClasses)this);
        this.comparatorByOrder = new BlockComparatorByOrder();
        this.categoryComparatorByOrder = new CategoryComparatorByOrder();
        this.load();
    }

    private void load() {
        this.mapClasses.clear();
        this.sortedCategories.clear();
        this.sortedBlocks.clear();
        this.initClassesMap("Blocks");
        this.initCustomBlocks();
        for (ArrayList<BlockCategoryInfo> arrayList : this.sortedCategories.values()) {
            Collections.sort(arrayList, this.categoryComparatorByOrder);
        }
        OppositeBlocksConfig oppositeBlocksConfig = new OppositeBlocksConfig();
        this.oppositeBlocksCache = oppositeBlocksConfig.load(MainApp.getDataPath() + "user/settings/OppositeBlocks.csv", this.mapClasses);
    }

    public static void init() throws Exception {
        if (instance != null) {
            throw new Exception("Blocks.init() called more than once!");
        }
        instance = new Blocks();
    }

    private void initClassesMap(String string) {
        try {
            CustomClassesLoader customClassesLoader = new CustomClassesLoader(string);
            while (customClassesLoader.hasNext()) {
                String string2 = customClassesLoader.getNext();
                Object object = customClassesLoader.createInstance(string2);
                if (object == null) {
                    Log.debug("Class " + string2 + " is abstract, skipping.");
                    continue;
                }
                if (object instanceof IBlock) {
                    IBlock iBlock = (IBlock)object;
                    this.mapClasses.put(iBlock.getClass().getSimpleName().hashCode(), (Object)iBlock);
                    this.putClassToSortedMap(iBlock);
                    continue;
                }
                if (!Log.isDebugEnabled()) continue;
                Log.debug("Class: " + string2 + " is not an instance of block");
            }
        }
        catch (Exception exception) {
            Log.error("An error occured while loading custom classes.", (Throwable)exception);
        }
    }

    private void initCustomBlocks() {
        try {
            CustomClassesLoader customClassesLoader = new CustomClassesLoader("Internal");
            while (customClassesLoader.hasNext()) {
                String string = customClassesLoader.getNext();
                if (!string.contains("CDataIndy") && !string.contains("CBlock")) continue;
                Object object = customClassesLoader.createInstance(string);
                if (object instanceof IBlock) {
                    IBlock iBlock = (IBlock)object;
                    this.mapClasses.put(iBlock.getClass().getSimpleName().hashCode(), (Object)iBlock);
                    continue;
                }
                if (!Log.isDebugEnabled()) continue;
                Log.debug("Class: " + string + " is not an instance of block");
            }
        }
        catch (Exception exception) {
            Log.error("An error occured while loading custom classes.", (Throwable)exception);
        }
    }

    private void putClassToSortedMap(IBlock iBlock) throws BlockDefinitionException {
        int n;
        String string = this.getBlockTypeAsString(iBlock);
        int n2 = 100;
        int n3 = 100;
        Class<?> clazz = iBlock.getClass();
        BuildingBlock buildingBlock = clazz.getAnnotation(BuildingBlock.class);
        String string2 = this.getCategoryName(clazz);
        SortOrder sortOrder = clazz.getAnnotation(SortOrder.class);
        n2 = sortOrder != null ? sortOrder.value() : 100;
        CategoryOrder categoryOrder = clazz.getAnnotation(CategoryOrder.class);
        n3 = categoryOrder != null ? categoryOrder.value() : 100;
        if (!this.sortedCategories.containsKey(string)) {
            this.sortedCategories.put(string, new ArrayList());
        }
        BlockCategoryInfo blockCategoryInfo = this.findOrCreateCategory(this.sortedCategories.get(string), string2, n3);
        if (blockCategoryInfo.categoryOrder < n3) {
            blockCategoryInfo.categoryOrder = n3;
        }
        if (!this.sortedBlocks.containsKey(n = string.hashCode() + string2.hashCode())) {
            this.sortedBlocks.put(n, new ArrayList());
        }
        ArrayList arrayList = (ArrayList)this.sortedBlocks.get(n);
        arrayList.add(iBlock);
        IntIterator intIterator = this.sortedBlocks.keySet().iterator();
        while (intIterator.hasNext()) {
            int n4 = (Integer)intIterator.next();
            arrayList = (ArrayList)this.sortedBlocks.get(n4);
            Collections.sort(arrayList, this.comparatorByOrder);
        }
    }

    private String getCategoryName(Class<?> clazz) {
        String string = clazz.getCanonicalName();
        int n = string.lastIndexOf(".");
        string = string.substring(0, n);
        n = string.lastIndexOf(".");
        String string2 = string.substring(n + 1);
        return string2;
    }

    private BlockCategoryInfo findOrCreateCategory(ArrayList<BlockCategoryInfo> arrayList, String string, int n) {
        int n2 = string.hashCode();
        for (BlockCategoryInfo blockCategoryInfo : arrayList) {
            if (blockCategoryInfo.categoryNameHash != n2) continue;
            return blockCategoryInfo;
        }
        BlockCategoryInfo blockCategoryInfo = new BlockCategoryInfo(string, n);
        arrayList.add(blockCategoryInfo);
        return blockCategoryInfo;
    }

    public static IBlock getBlockObject(String string, StrategyBase strategyBase, Element element) throws BlockDefinitionException {
        IBlock iBlock = null;
        iBlock = string.startsWith("talib_") ? new TALibIndicator() : Blocks.get(string);
        iBlock = iBlock.newInstance(strategyBase, element);
        return iBlock;
    }

    public static IBlock get(String string) throws BlockDefinitionException {
        return Blocks.get(string, null);
    }

    public static boolean exists(String string) throws BlockDefinitionException {
        if (instance == null) {
            throw new BlockDefinitionException("You have to call Blocks.init() on program startup!");
        }
        return Blocks.instance.mapClasses.containsKey(string.hashCode());
    }

    private static IBlock get(String string, StrategyBase strategyBase) throws BlockDefinitionException {
        if (instance == null) {
            throw new BlockDefinitionException("You have to call Blocks.init() on program startup!");
        }
        if (string.startsWith("CDataIndy")) {
            return instance._get("CDataIndy", strategyBase);
        }
        if (string.startsWith("CBlock")) {
            return instance._get("CBlock", strategyBase);
        }
        return instance._get(string, strategyBase);
    }

    public static Element generateBlockTreeXml(IBlock iBlock) throws BlockDefinitionException {
        if (instance == null) {
            throw new BlockDefinitionException("You have to call Blocks.init() on program startup!");
        }
        return instance._generateBlockTreeXml(iBlock);
    }

    private IBlock _get(String string, StrategyBase strategyBase) throws BlockDefinitionException {
        int n = string.hashCode();
        if (!this.mapClasses.containsKey(n)) {
            throw new BlockDefinitionException("Cannot find block '" + string + "'");
        }
        try {
            return ((IBlock)this.mapClasses.get(n)).clone(false, strategyBase);
        }
        catch (BlockDefinitionException blockDefinitionException) {
            Log.error("Error during cloning block", (Throwable)blockDefinitionException);
            blockDefinitionException.printStackTrace();
            return null;
        }
    }

    public static void generateBlocksXml(Element element) throws BlockDefinitionException {
        if (instance == null) {
            throw new BlockDefinitionException("You have to call Blocks.init() on program startup!");
        }
        instance._generateBlocksXml(element);
    }

    private void _generateBlocksXml(Element element) throws BlockDefinitionException {
        Element element2 = element.getChild("Blocks");
        Element element3 = element.getChild("ParameterSets");
        for (String string : this.sortedCategories.keySet()) {
            ArrayList<BlockCategoryInfo> arrayList = this.sortedCategories.get(string);
            for (BlockCategoryInfo blockCategoryInfo : arrayList) {
                int n = string.hashCode() + blockCategoryInfo.categoryNameHash;
                ArrayList arrayList2 = (ArrayList)this.sortedBlocks.get(n);
                for (IBlock iBlock : arrayList2) {
                    Element element4;
                    Element element5 = this.createBlock(iBlock, element4 = this.getBlockTypeElement(iBlock, element2), element3);
                    if (element5 == null) continue;
                    String string2 = this.getCategoryName(iBlock, element5);
                    Element element6 = this.getOrCreate(element4, string2, "Category");
                    element6.addContent((Content)element5);
                }
            }
        }
    }

    private Element createBlock(IBlock iBlock, Element element, Element element2) throws BlockDefinitionException {
        Class<?> clazz = iBlock.getClass();
        if (this.isIgnoredBlock(clazz)) {
            return null;
        }
        Element element3 = this.createBlockNode(clazz, "Item");
        String string = this.addReturnTypeAttribute(element3, element, clazz);
        this.addCategoryTypeAttributes(element3, clazz, string);
        this.addNotFirstValueAttribute(element3, clazz);
        this.addBlockParameters(element3, iBlock, clazz, false);
        this.addBlockParameterSets(element2, iBlock, clazz);
        return element3;
    }

    private boolean isIgnoredBlock(Class<?> clazz) {
        String[] stringArray = new String[]{".AND", ".OR", "Values.Price.VolumeDaily"};
        String string = clazz.getCanonicalName();
        for (String string2 : stringArray) {
            if (!string.contains(string2)) continue;
            return true;
        }
        return false;
    }

    private Element _generateBlockTreeXml(IBlock iBlock) throws BlockDefinitionException {
        Class<?> clazz = iBlock.getClass();
        if (clazz.getSimpleName().equals("CDataIndy")) {
            return iBlock.getCustomBlockXml(0);
        }
        if (clazz.getSimpleName().equals("CBlock")) {
            return iBlock.getCustomBlockXml(1);
        }
        if (iBlock instanceof TALibIndicator) {
            TALibIndicator tALibIndicator = (TALibIndicator)iBlock;
            return tALibIndicator.getBlockXml();
        }
        Element element = this.createBlockNode(clazz, "Item");
        this.addBlockParameters(element, iBlock, clazz, true);
        return element;
    }

    private void addBlockParameters(Element element, IBlock iBlock, Class<?> clazz, boolean bl) throws BlockDefinitionException {
        for (Field field : clazz.getFields()) {
            AnnotationProcessor.wizardGenerateXml(field, element, iBlock, clazz, bl);
        }
        OutputAnnotationHandler.wizardGenerateXml(clazz, element, iBlock, clazz, bl);
    }

    private void addBlockParameterSets(Element element, IBlock iBlock, Class<?> clazz) {
        ParameterSet parameterSet;
        ParameterSet[] parameterSetArray = null;
        ParameterSets parameterSets = clazz.getAnnotation(ParameterSets.class);
        if (parameterSets != null) {
            parameterSetArray = parameterSets.value();
        } else {
            parameterSet = clazz.getAnnotation(ParameterSet.class);
            if (parameterSet != null) {
                parameterSetArray = new ParameterSet[]{parameterSet};
            }
        }
        if (parameterSetArray != null) {
            parameterSet = new Element("Item");
            parameterSet.setAttribute("key", clazz.getSimpleName());
            for (int i = 0; i < parameterSetArray.length; ++i) {
                ParameterSet parameterSet2 = parameterSetArray[i];
                String string = parameterSet2.set();
                if (string == null || string.isEmpty()) continue;
                String[] stringArray = string.split("\\,");
                String string2 = "";
                Element element2 = new Element("Set");
                element2.setAttribute("weight", "" + parameterSet2.weight());
                String string3 = null;
                for (Field field : clazz.getFields()) {
                    if (field.getAnnotation(Parameter.class) == null) continue;
                    String string4 = "*";
                    for (int j = 0; j < stringArray.length; ++j) {
                        String[] stringArray2 = stringArray[j].split("=");
                        if (stringArray2.length != 2) {
                            Log.error("Incorrect parameter set definition in block '" + clazz.getSimpleName() + "': Param values '" + string + "'");
                            continue;
                        }
                        if (stringArray2[0].equals("ComputedFrom")) {
                            string3 = stringArray2[1];
                        }
                        if (!stringArray2[0].equals(field.getName())) continue;
                        string4 = stringArray2[1];
                        break;
                    }
                    if (field.getType().isAssignableFrom(DataSeries.class)) {
                        string2 = string2 + string4 + ",";
                        if (string3 == null) {
                            string2 = string2 + "*,";
                            continue;
                        }
                        string2 = string2 + string3 + ",";
                        continue;
                    }
                    string2 = string2 + string4 + ",";
                }
                if (string2.length() <= 0) continue;
                string2 = string2.substring(0, string2.length() - 1);
                element2.setAttribute("values", string2);
                parameterSet.addContent((Content)element2);
            }
            element.addContent((Content)parameterSet);
        }
    }

    private String addReturnTypeAttribute(Element element, Element element2, Class<?> clazz) throws BlockDefinitionException {
        String string = "none";
        BuildingBlock buildingBlock = clazz.getAnnotation(BuildingBlock.class);
        if (element2.getName().equals("Values")) {
            element.setAttribute("returnType", "number");
            if (buildingBlock != null) {
                string = ReturnTypes.translateReturnType(buildingBlock.returnType());
            }
        }
        if (element2.getName().equals("Comparisons")) {
            string = "boolean";
        }
        if (element2.getName().equals("Conditions")) {
            string = "boolean";
        }
        if (element2.getName().equals("Actions")) {
            string = buildingBlock != null && buildingBlock.returnType() == 8 ? "order" : "none";
        }
        element.setAttribute("returnType", string);
        return string;
    }

    private void addCategoryTypeAttributes(Element element, Class<?> clazz, String string) {
        if (this.isIndicator(clazz)) {
            if (string.equals("pricerange")) {
                element.setAttribute("categoryType", "priceRange");
            } else {
                element.setAttribute("categoryType", "indicator");
            }
            Indicator indicator = clazz.getAnnotation(Indicator.class);
            if (indicator != null) {
                if (indicator.oscillator()) {
                    element.setAttribute("isOscillator", "true");
                    element.setAttribute("middleValue", SQUtils.doubleToString((double)indicator.middleValue()));
                }
                element.setAttribute("indicatorMin", SQUtils.doubleToString((double)indicator.min()));
                element.setAttribute("indicatorMax", SQUtils.doubleToString((double)indicator.max()));
                element.setAttribute("indicatorStep", SQUtils.doubleToString((double)indicator.step()));
            }
        } else if (this.isPriceValue(clazz, string)) {
            element.setAttribute("categoryType", "priceValue");
        } else if (this.isOperator(clazz)) {
            element.setAttribute("categoryType", "operators");
        } else if (this.isSimpleRule(clazz)) {
            element.setAttribute("categoryType", "simpleRules");
        } else {
            element.setAttribute("categoryType", "other");
        }
    }

    private boolean isSimpleRule(Class<?> clazz) {
        return Blocks.checkContains(clazz, "ConditionBlock");
    }

    private boolean isOperator(Class<?> clazz) {
        return Blocks.checkContains(clazz, "ComparisonBlock");
    }

    public static boolean checkContains(Class<?> clazz, String string) {
        for (int i = 0; i < 6; ++i) {
            if (clazz.getName().contains(string)) {
                return true;
            }
            if ((clazz = clazz.getSuperclass()) != null) continue;
            return false;
        }
        return false;
    }

    private boolean isPriceValue(Class<?> clazz, String string) {
        return Blocks.checkContains(clazz, "SQ.Blocks.Price") && string.equals("price");
    }

    private boolean isIndicator(Class<?> clazz) {
        boolean bl = Blocks.checkContains(clazz, "IndicatorBlock");
        if (bl) {
            return true;
        }
        Indicator indicator = clazz.getAnnotation(Indicator.class);
        return indicator != null;
    }

    private void addNotFirstValueAttribute(Element element, Class<?> clazz) {
        NotFirstValue notFirstValue = clazz.getAnnotation(NotFirstValue.class);
        if (notFirstValue != null) {
            element.setAttribute("notFirstValue", "true");
        }
    }

    private Element createBlockNode(Class<?> clazz, String string) {
        Object object;
        Object object2;
        IgnoreInBuilder ignoreInBuilder;
        Help help;
        Element element = new Element(string);
        String string2 = SQUtils.insertUppercaseSpaces((String)clazz.getSimpleName());
        String string3 = null;
        int n = 0;
        String string4 = null;
        Object var8_8 = null;
        BuildingBlock buildingBlock = clazz.getAnnotation(BuildingBlock.class);
        if (buildingBlock != null) {
            if (!buildingBlock.name().equals("Null")) {
                string2 = buildingBlock.name();
            }
            if (!buildingBlock.display().equals("Null")) {
                string3 = buildingBlock.display();
            }
            n = buildingBlock.returnType();
        }
        if ((help = clazz.getAnnotation(Help.class)) != null) {
            string4 = help.value();
        }
        element.setAttribute("customSnippet", "" + !SnippetsCompiler.getInstance().isInternalSnippet(clazz.getName()));
        element.setAttribute("key", clazz.getSimpleName());
        element.setAttribute("name", string2);
        if (string3 != null) {
            element.setAttribute("display", string3);
        }
        if (n != 0) {
            try {
                element.setAttribute("returnType", ReturnTypes.translateReturnType(n));
            }
            catch (BlockDefinitionException blockDefinitionException) {
                Log.info("Unknown return type for block {}", (Object)string);
            }
        }
        if (string4 != null) {
            element.setAttribute("help", string4);
        }
        if ((ignoreInBuilder = clazz.getAnnotation(IgnoreInBuilder.class)) != null) {
            element.setAttribute("ignoreInBuilder", "true");
        }
        if (buildingBlock != null) {
            object2 = buildingBlock.mainIndicator();
            if (((String)object2).equals("Null")) {
                object = clazz.getPackage().toString().split("\\.");
                object2 = object != null && ((String[])object).length > 1 ? object[((String[])object).length - 1] : null;
            }
            if (object2 != null) {
                element.setAttribute("mI", (String)object2);
            }
        }
        if ((object2 = clazz.getAnnotation(ForEngine.class)) != null && !object2.value().equals("Null")) {
            object = object2.value();
            element.setAttribute("forEngine", (String)object);
        }
        if ((object = clazz.getAnnotation(MT5ExtendedTemplate.class)) != null) {
            element.setAttribute("mt5ExtendedTemplate", "true");
        }
        return element;
    }

    private Element getBlockTypeElement(IBlock iBlock, Element element) throws BlockDefinitionException {
        String string = this.getBlockTypeAsString(iBlock);
        return this.getOrCreate(element, string, string);
    }

    public static int getBlockType(IBlock iBlock) throws Exception {
        if (instance == null) {
            throw new Exception("You have to call Blocks.init() on program startup!");
        }
        return instance._getBlockType(iBlock);
    }

    private int _getBlockType(IBlock iBlock) throws BlockDefinitionException {
        String string = SQUtils.getClasses(iBlock.getClass());
        if (string.contains("CBlock")) {
            return this.getBlockTypeFromXml(iBlock);
        }
        if (string.contains("TALibIndicator.Object")) {
            return 4;
        }
        if (string.contains(".IndicatorBlock")) {
            return 4;
        }
        if (string.contains(".ValueBlock")) {
            return 4;
        }
        if (string.contains(".ComparisonBlock")) {
            return 2;
        }
        if (string.contains(".ConditionBlock")) {
            return 3;
        }
        if (string.contains(".ActionBlock")) {
            return 5;
        }
        if (string.contains(".FormulaBlock")) {
            return 6;
        }
        if (string.contains(".ExitMethod")) {
            return 7;
        }
        throw new BlockDefinitionException("Block " + iBlock.toString() + " has unknown instance type!");
    }

    private int getBlockTypeFromXml(IBlock iBlock) throws BlockDefinitionException {
        try {
            String string;
            Element element = iBlock.getCustomBlockXml(3);
            if (element == null) {
                throw new BlockDefinitionException("Custom Block " + iBlock.toString() + " has null XML!");
            }
            switch (string = element.getAttributeValue("type")) {
                case "Condition": {
                    return 3;
                }
                case "Action": {
                    return 5;
                }
                case "Price level": {
                    return 4;
                }
                case "Value": {
                    return 4;
                }
            }
            throw new BlockDefinitionException("Custom Block " + iBlock.toString() + " has unknown instance type (1)!");
        }
        catch (BlockDefinitionException blockDefinitionException) {
            throw new BlockDefinitionException("Custom Block " + iBlock.toString() + " has unknown instance type (2)!", blockDefinitionException);
        }
    }

    public static int getReturnType(IBlock iBlock) throws Exception {
        if (instance == null) {
            throw new Exception("You have to call Blocks.init() on program startup!");
        }
        return instance._getReturnType(iBlock);
    }

    private int _getReturnType(IBlock iBlock) {
        BuildingBlock buildingBlock = iBlock.getClass().getAnnotation(BuildingBlock.class);
        if (buildingBlock != null) {
            return buildingBlock.returnType();
        }
        return 0;
    }

    private String getBlockTypeAsString(IBlock iBlock) throws BlockDefinitionException {
        int n = this._getBlockType(iBlock);
        switch (n) {
            case 4: {
                return "Values";
            }
            case 2: {
                return "Comparisons";
            }
            case 3: {
                return "Conditions";
            }
            case 5: {
                return "Actions";
            }
        }
        throw new BlockDefinitionException("Block " + iBlock.toString() + " has unknown instance type!");
    }

    private String getCategoryName(IBlock iBlock, Element element) throws BlockDefinitionException {
        String string = element.getAttributeValue("category");
        if (string == null) {
            string = this.recognizeFromPackagePath(iBlock);
        } else {
            element.removeAttribute("category");
        }
        return string;
    }

    private String recognizeFromPackagePath(IBlock iBlock) throws BlockDefinitionException {
        String string = iBlock.toString();
        String[] stringArray = string.split("\\.");
        if (stringArray.length < 3) {
            return null;
        }
        Class<?> clazz = iBlock.getClass();
        String string2 = Blocks.checkContains(clazz, "IndicatorBlock") ? (stringArray.length >= 5 ? stringArray[stringArray.length - 3] : stringArray[stringArray.length - 2]) : stringArray[stringArray.length - 2];
        return string2;
    }

    private Element getOrCreate(Element element, String string, String string2) {
        String string3 = string.replace(" ", "");
        for (Element element2 : element.getChildren(string2)) {
            if (element2.getAttributeValue("key") == null || !element2.getAttributeValue("key").equals(string3)) continue;
            return element2;
        }
        Element element3 = new Element(string2);
        element3.setAttribute("name", SQUtils.insertUppercaseSpaces((String)string));
        element3.setAttribute("key", string3);
        element.addContent((Content)element3);
        return element3;
    }

    public static IBlock[] getAllAvailableBlocks() throws Exception {
        if (instance == null) {
            throw new Exception("You have to call Blocks.init() on program startup!");
        }
        return instance._getAllAvailableBlocks();
    }

    private IBlock[] _getAllAvailableBlocks() {
        IBlock[] iBlockArray = new IBlock[this.mapClasses.size()];
        int n = 0;
        for (Object e : this.mapClasses.values()) {
            iBlockArray[n++] = (IBlock)e;
            if (n != iBlockArray.length) continue;
            break;
        }
        return iBlockArray;
    }

    public static void generateExitRulesXml(Element element) throws BlockDefinitionException {
        if (instance == null) {
            throw new BlockDefinitionException("You have to call Blocks.init() on program startup!");
        }
        instance._generateExitRulesXml(element);
    }

    private void _generateExitRulesXml(Element element) throws BlockDefinitionException {
        if (element == null) {
            return;
        }
        for (ExitMethod exitMethod : ExitMethodsList.get().getAvailableClasses()) {
            exitMethod.createExitMethodXml(element);
        }
    }

    public void reload() {
        this.load();
    }

    public static TreeMap<String, String> generateOppositeBlocksMap() {
        return instance._generateOppositeBlocksMap();
    }

    private TreeMap<String, String> _generateOppositeBlocksMap() {
        TreeMap<String, String> treeMap = new TreeMap<String, String>();
        for (String string : this.sortedCategories.keySet()) {
            ArrayList<BlockCategoryInfo> arrayList = this.sortedCategories.get(string);
            for (BlockCategoryInfo blockCategoryInfo : arrayList) {
                int n = string.hashCode() + blockCategoryInfo.categoryNameHash;
                ArrayList arrayList2 = (ArrayList)this.sortedBlocks.get(n);
                for (IBlock iBlock : arrayList2) {
                    Class<?> clazz = iBlock.getClass();
                    String string2 = clazz.getSimpleName();
                    OppositeBlock oppositeBlock = clazz.getAnnotation(OppositeBlock.class);
                    String string3 = oppositeBlock == null || oppositeBlock.value().equals("Null") ? string2 : oppositeBlock.value();
                    treeMap.put(string2, string3);
                }
            }
        }
        return treeMap;
    }

    public static IBlock getOppositeBlock(IBlock iBlock) throws BlockDefinitionException {
        return instance._getOppositeBlock(iBlock);
    }

    private IBlock _getOppositeBlock(IBlock iBlock) throws BlockDefinitionException {
        OppositeBlock oppositeBlock;
        String string = iBlock.getClass().getSimpleName();
        if (string.equals("TALibIndicator")) {
            return this._getTALiBOppositeBlock(iBlock);
        }
        String string2 = null;
        if (this.oppositeBlocksCache.containsKey(string)) {
            string2 = this.oppositeBlocksCache.get(string);
            try {
                return this._getOppositeBlockObject(iBlock, string2);
            }
            catch (Exception exception) {
                Log.error("Cannot get block opposite to '" + string + "' from cache, opposite block '" + string2 + "' cannot be created!", (Throwable)exception);
            }
        }
        if ((oppositeBlock = iBlock.getClass().getAnnotation(OppositeBlock.class)) != null) {
            string2 = oppositeBlock.value();
            try {
                return this._getOppositeBlockObject(iBlock, string2);
            }
            catch (Exception exception) {
                Log.error("Cannot get block opposite to '" + string + "' from snippet annotation, opposite block '" + string2 + "' cannot be created!", (Throwable)exception);
            }
        }
        string2 = string;
        try {
            return this._getOppositeBlockObject(iBlock, string2);
        }
        catch (Exception exception) {
            Log.error("Cannot get block opposite to '" + string + "' from same block, opposite block '" + string2 + "' cannot be created!", (Throwable)exception);
            throw new BlockDefinitionException("Cannot create block opposite to '" + string + "'");
        }
    }

    public static IBlock getSameBlock(IBlock iBlock) throws BlockDefinitionException {
        return instance._getSameBlock(iBlock);
    }

    private IBlock _getSameBlock(IBlock iBlock) throws BlockDefinitionException {
        String string = iBlock.getClass().getSimpleName();
        if (string.equals("TALibIndicator")) {
            return this._getTALiBOppositeBlock(iBlock);
        }
        String string2 = string;
        try {
            return this._getOppositeBlockObject(iBlock, string2);
        }
        catch (Exception exception) {
            Log.error("Cannot get block opposite to '" + string + "' from same block, opposite block '" + string2 + "' cannot be created!", (Throwable)exception);
            throw new BlockDefinitionException("Cannot create block opposite to '" + string + "'");
        }
    }

    private IBlock _getTALiBOppositeBlock(IBlock iBlock) {
        TALibIndicator tALibIndicator = new TALibIndicator();
        tALibIndicator.copyFrom((TALibIndicator)iBlock);
        return tALibIndicator;
    }

    private IBlock _getOppositeBlockObject(IBlock iBlock, String string) throws BlockDefinitionException {
        IBlock iBlock2;
        if (iBlock instanceof ExitMethod) {
            iBlock2 = ExitMethodsList.getExitMethodObject(string, null, null);
        } else {
            iBlock2 = Blocks.get(string, iBlock.getStrategy());
            iBlock2.copyCustomData(iBlock);
        }
        return iBlock2;
    }

    public static String getOppositeBlockKey(String string) {
        return instance._getOppositeBlockKey(string);
    }

    private String _getOppositeBlockKey(String string) {
        String string2;
        if (this.oppositeBlocksCache.containsKey(string)) {
            return this.oppositeBlocksCache.get(string);
        }
        Element element = CustomBlocks.getElement(string);
        if (element != null && (string2 = element.getAttributeValue("oppositeBlockKey")) != null) {
            return string2;
        }
        return string;
    }

    public static void sortByOrder(ExitMethod[] exitMethodArray) {
        instance._sortByOrder(exitMethodArray);
    }

    private void _sortByOrder(ExitMethod[] exitMethodArray) {
        Arrays.sort(exitMethodArray, this.comparatorByOrder);
    }
}

