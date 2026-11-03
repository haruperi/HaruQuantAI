/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.blocks.random;

import com.strategyquant.tradinglib.BlockSuperTypes;
import com.strategyquant.tradinglib.ReturnTypes;
import com.strategyquant.tradinglib.blocks.random.BlockParameter;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.io.Serializable;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BlockDefinition
implements Serializable {
    public static final Logger Log = LoggerFactory.getLogger((String)"BlockDefinition");
    public String key;
    public String name;
    public int superType;
    public ObjectArrayList<BlockParameter> parameters = new ObjectArrayList();
    private Element elBlock;
    public boolean notFirstValue = false;
    public boolean isIndicator = false;
    public double indicatorMin;
    public double indicatorMax;
    public double indicatorStep;
    public int returnType;
    public String categoryType = null;

    public BlockDefinition(Element element, Element element2, String string) throws Exception {
        this.key = element.getAttributeValue("key");
        this.name = element.getAttributeValue("name");
        this.superType = BlockSuperTypes.translate(string);
        this.returnType = ReturnTypes.translate(element.getAttributeValue("returnType"));
        this.categoryType = element.getAttributeValue("categoryType");
        this.elBlock = element;
        String string2 = element.getAttributeValue("notFirstValue");
        if (string2 != null && string2.equals("true")) {
            this.notFirstValue = true;
        }
        if (element.getAttributeValue("categoryType") != null) {
            this.isIndicator = element.getAttributeValue("categoryType").equals("indicator");
        }
        String string3 = element.getAttributeValue("indicatorMin");
        String string4 = element.getAttributeValue("indicatorMax");
        String string5 = element.getAttributeValue("indicatorStep");
        this.indicatorMin = string3 != null ? Double.parseDouble(string3) : -999999.0;
        this.indicatorMax = string4 != null ? Double.parseDouble(string4) : 999999.0;
        this.indicatorStep = string5 != null ? Double.parseDouble(string5) : 0.0;
        this.parseParameters(element2);
    }

    BlockDefinition(String string, int n) {
        this.elBlock = new Element("Item");
        this.elBlock.setAttribute("key", "CDataIndy_" + string);
        this.elBlock.setAttribute("cdataType", Integer.toString(n));
    }

    private void parseParameters(Element element) {
        int n;
        if (element != null) {
            for (Element element2 : element.getChildren()) {
                for (Element element3 : element2.getChildren("Param")) {
                    this.parameters.add((Object)new BlockParameter(element3));
                }
            }
        }
        if (this.superType == 2 && (n = this.computeValueParameters()) == 1) {
            this.superType = 1;
        }
    }

    private int computeValueParameters() {
        int n = 0;
        for (BlockParameter blockParameter : this.parameters) {
            if (!blockParameter.isValueParameter()) continue;
            ++n;
        }
        return n;
    }

    public Element getXml() {
        return this.elBlock;
    }

    public String getKey() {
        return this.key;
    }

    public String getName() {
        return this.name;
    }

    public BlockParameter getParamByKey(String string) {
        for (int i = 0; i < this.parameters.size(); ++i) {
            BlockParameter blockParameter = (BlockParameter)this.parameters.get(i);
            if (!blockParameter.key.equals(string)) continue;
            return blockParameter;
        }
        return null;
    }
}

