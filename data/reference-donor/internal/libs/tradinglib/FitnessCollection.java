/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import org.jdom2.Element;

public class FitnessCollection {
    private double fitnessIS = 0.0;
    private double fitnessOOS = 0.0;
    private double fitnessFS = 0.0;
    private double fitnessIST = 0.0;
    private double fitnessISV = 0.0;
    private double fitnessISV1 = 0.0;
    private double fitnessISV2 = 0.0;
    private double fitnessISV3 = 0.0;
    private double fitnessISV4 = 0.0;
    private double fitnessISV5 = 0.0;
    private double fitnessISV6 = 0.0;
    private double fitnessISV7 = 0.0;
    private double fitnessISV8 = 0.0;
    private double fitnessISV9 = 0.0;
    private double fitnessISV10 = 0.0;
    private double fitnessOOS1 = 0.0;
    private double fitnessOOS2 = 0.0;
    private double fitnessOOS3 = 0.0;
    private double fitnessOOS4 = 0.0;
    private double fitnessOOS5 = 0.0;
    private double fitnessOOS6 = 0.0;
    private double fitnessOOS7 = 0.0;
    private double fitnessOOS8 = 0.0;
    private double fitnessOOS9 = 0.0;
    private double fitnessOOS10 = 0.0;

    public double getFitness(byte by) {
        switch (by) {
            case 10: {
                return this.fitnessIS;
            }
            case 11: {
                return this.fitnessIST;
            }
            case 40: {
                return this.fitnessISV;
            }
            case 41: {
                return this.fitnessISV1;
            }
            case 42: {
                return this.fitnessISV2;
            }
            case 43: {
                return this.fitnessISV3;
            }
            case 44: {
                return this.fitnessISV4;
            }
            case 45: {
                return this.fitnessISV5;
            }
            case 46: {
                return this.fitnessISV6;
            }
            case 47: {
                return this.fitnessISV7;
            }
            case 48: {
                return this.fitnessISV8;
            }
            case 49: {
                return this.fitnessISV9;
            }
            case 50: {
                return this.fitnessISV10;
            }
            case 20: {
                return this.fitnessOOS;
            }
            case 21: {
                return this.fitnessOOS1;
            }
            case 22: {
                return this.fitnessOOS2;
            }
            case 23: {
                return this.fitnessOOS3;
            }
            case 24: {
                return this.fitnessOOS4;
            }
            case 25: {
                return this.fitnessOOS5;
            }
            case 26: {
                return this.fitnessOOS6;
            }
            case 27: {
                return this.fitnessOOS7;
            }
            case 28: {
                return this.fitnessOOS8;
            }
            case 29: {
                return this.fitnessOOS9;
            }
            case 30: {
                return this.fitnessOOS10;
            }
            case 127: {
                return this.fitnessFS;
            }
        }
        return 0.0;
    }

    public void setFitness(byte by, double d) {
        switch (by) {
            case 10: {
                this.fitnessIS = d;
                break;
            }
            case 11: {
                this.fitnessIST = d;
                break;
            }
            case 40: {
                this.fitnessISV = d;
                break;
            }
            case 41: {
                this.fitnessISV1 = d;
                break;
            }
            case 42: {
                this.fitnessISV2 = d;
                break;
            }
            case 43: {
                this.fitnessISV3 = d;
                break;
            }
            case 44: {
                this.fitnessISV4 = d;
                break;
            }
            case 45: {
                this.fitnessISV5 = d;
                break;
            }
            case 46: {
                this.fitnessISV6 = d;
                break;
            }
            case 47: {
                this.fitnessISV7 = d;
                break;
            }
            case 48: {
                this.fitnessISV8 = d;
                break;
            }
            case 49: {
                this.fitnessISV9 = d;
                break;
            }
            case 50: {
                this.fitnessISV10 = d;
                break;
            }
            case 20: {
                this.fitnessOOS = d;
                break;
            }
            case 21: {
                this.fitnessOOS1 = d;
                break;
            }
            case 22: {
                this.fitnessOOS2 = d;
                break;
            }
            case 23: {
                this.fitnessOOS3 = d;
                break;
            }
            case 24: {
                this.fitnessOOS4 = d;
                break;
            }
            case 25: {
                this.fitnessOOS5 = d;
                break;
            }
            case 26: {
                this.fitnessOOS6 = d;
                break;
            }
            case 27: {
                this.fitnessOOS7 = d;
                break;
            }
            case 28: {
                this.fitnessOOS8 = d;
                break;
            }
            case 29: {
                this.fitnessOOS9 = d;
                break;
            }
            case 30: {
                this.fitnessOOS10 = d;
                break;
            }
            case 127: {
                this.fitnessFS = d;
            }
        }
    }

    public FitnessCollection clone() {
        FitnessCollection fitnessCollection = new FitnessCollection();
        fitnessCollection.fitnessIS = this.fitnessIS;
        fitnessCollection.fitnessOOS = this.fitnessOOS;
        fitnessCollection.fitnessFS = this.fitnessFS;
        fitnessCollection.fitnessIST = this.fitnessIST;
        fitnessCollection.fitnessISV = this.fitnessISV;
        fitnessCollection.fitnessISV1 = this.fitnessISV1;
        fitnessCollection.fitnessISV2 = this.fitnessISV2;
        fitnessCollection.fitnessISV3 = this.fitnessISV3;
        fitnessCollection.fitnessISV4 = this.fitnessISV4;
        fitnessCollection.fitnessISV5 = this.fitnessISV5;
        fitnessCollection.fitnessISV6 = this.fitnessISV6;
        fitnessCollection.fitnessISV7 = this.fitnessISV7;
        fitnessCollection.fitnessISV8 = this.fitnessISV8;
        fitnessCollection.fitnessISV9 = this.fitnessISV9;
        fitnessCollection.fitnessISV10 = this.fitnessISV10;
        fitnessCollection.fitnessOOS1 = this.fitnessOOS1;
        fitnessCollection.fitnessOOS2 = this.fitnessOOS2;
        fitnessCollection.fitnessOOS3 = this.fitnessOOS3;
        fitnessCollection.fitnessOOS4 = this.fitnessOOS4;
        fitnessCollection.fitnessOOS5 = this.fitnessOOS5;
        fitnessCollection.fitnessOOS6 = this.fitnessOOS6;
        fitnessCollection.fitnessOOS7 = this.fitnessOOS7;
        fitnessCollection.fitnessOOS8 = this.fitnessOOS8;
        fitnessCollection.fitnessOOS9 = this.fitnessOOS9;
        fitnessCollection.fitnessOOS10 = this.fitnessOOS10;
        return fitnessCollection;
    }

    public void clear() {
        this.fitnessIS = 0.0;
        this.fitnessOOS = 0.0;
        this.fitnessFS = 0.0;
        this.fitnessIST = 0.0;
        this.fitnessISV = 0.0;
        this.fitnessISV1 = 0.0;
        this.fitnessISV2 = 0.0;
        this.fitnessISV3 = 0.0;
        this.fitnessISV4 = 0.0;
        this.fitnessISV5 = 0.0;
        this.fitnessISV6 = 0.0;
        this.fitnessISV7 = 0.0;
        this.fitnessISV8 = 0.0;
        this.fitnessISV9 = 0.0;
        this.fitnessISV10 = 0.0;
        this.fitnessOOS1 = 0.0;
        this.fitnessOOS2 = 0.0;
        this.fitnessOOS3 = 0.0;
        this.fitnessOOS4 = 0.0;
        this.fitnessOOS5 = 0.0;
        this.fitnessOOS6 = 0.0;
        this.fitnessOOS7 = 0.0;
        this.fitnessOOS8 = 0.0;
        this.fitnessOOS9 = 0.0;
        this.fitnessOOS10 = 0.0;
    }

    public Element getXML() {
        Element element = new Element("Fitnesses");
        element.setAttribute("IS", Double.toString(SQUtils.round6((double)this.fitnessIS)));
        element.setAttribute("FS", Double.toString(SQUtils.round6((double)this.fitnessFS)));
        element.setAttribute("IST", Double.toString(SQUtils.round6((double)this.fitnessIST)));
        element.setAttribute("ISV", Double.toString(SQUtils.round6((double)this.fitnessISV)));
        element.setAttribute("ISV1", Double.toString(SQUtils.round6((double)this.fitnessISV1)));
        element.setAttribute("ISV2", Double.toString(SQUtils.round6((double)this.fitnessISV2)));
        element.setAttribute("ISV3", Double.toString(SQUtils.round6((double)this.fitnessISV3)));
        element.setAttribute("ISV4", Double.toString(SQUtils.round6((double)this.fitnessISV4)));
        element.setAttribute("ISV5", Double.toString(SQUtils.round6((double)this.fitnessISV5)));
        element.setAttribute("ISV6", Double.toString(SQUtils.round6((double)this.fitnessISV6)));
        element.setAttribute("ISV7", Double.toString(SQUtils.round6((double)this.fitnessISV7)));
        element.setAttribute("ISV8", Double.toString(SQUtils.round6((double)this.fitnessISV8)));
        element.setAttribute("ISV9", Double.toString(SQUtils.round6((double)this.fitnessISV9)));
        element.setAttribute("ISV10", Double.toString(SQUtils.round6((double)this.fitnessISV10)));
        element.setAttribute("OOS", Double.toString(SQUtils.round6((double)this.fitnessOOS)));
        element.setAttribute("OOS1", Double.toString(SQUtils.round6((double)this.fitnessOOS1)));
        element.setAttribute("OOS2", Double.toString(SQUtils.round6((double)this.fitnessOOS2)));
        element.setAttribute("OOS3", Double.toString(SQUtils.round6((double)this.fitnessOOS3)));
        element.setAttribute("OOS4", Double.toString(SQUtils.round6((double)this.fitnessOOS4)));
        element.setAttribute("OOS5", Double.toString(SQUtils.round6((double)this.fitnessOOS5)));
        element.setAttribute("OOS6", Double.toString(SQUtils.round6((double)this.fitnessOOS6)));
        element.setAttribute("OOS7", Double.toString(SQUtils.round6((double)this.fitnessOOS7)));
        element.setAttribute("OOS8", Double.toString(SQUtils.round6((double)this.fitnessOOS8)));
        element.setAttribute("OOS9", Double.toString(SQUtils.round6((double)this.fitnessOOS9)));
        element.setAttribute("OOS10", Double.toString(SQUtils.round6((double)this.fitnessOOS10)));
        return element;
    }

    public void setFromXML(Element element) {
        Element element2 = element.getChild("Fitnesses");
        if (element2 == null) {
            return;
        }
        this.fitnessIS = XMLUtil.getDoubleAttr((Element)element2, (String)"IS", (double)0.0);
        this.fitnessFS = XMLUtil.getDoubleAttr((Element)element2, (String)"FS", (double)0.0);
        this.fitnessIST = XMLUtil.getDoubleAttr((Element)element2, (String)"IST", (double)0.0);
        this.fitnessISV = XMLUtil.getDoubleAttr((Element)element2, (String)"ISV", (double)0.0);
        this.fitnessISV1 = XMLUtil.getDoubleAttr((Element)element2, (String)"ISV1", (double)0.0);
        this.fitnessISV2 = XMLUtil.getDoubleAttr((Element)element2, (String)"ISV2", (double)0.0);
        this.fitnessISV3 = XMLUtil.getDoubleAttr((Element)element2, (String)"ISV3", (double)0.0);
        this.fitnessISV4 = XMLUtil.getDoubleAttr((Element)element2, (String)"ISV4", (double)0.0);
        this.fitnessISV5 = XMLUtil.getDoubleAttr((Element)element2, (String)"ISV5", (double)0.0);
        this.fitnessISV6 = XMLUtil.getDoubleAttr((Element)element2, (String)"ISV6", (double)0.0);
        this.fitnessISV7 = XMLUtil.getDoubleAttr((Element)element2, (String)"ISV7", (double)0.0);
        this.fitnessISV8 = XMLUtil.getDoubleAttr((Element)element2, (String)"ISV8", (double)0.0);
        this.fitnessISV9 = XMLUtil.getDoubleAttr((Element)element2, (String)"ISV9", (double)0.0);
        this.fitnessISV10 = XMLUtil.getDoubleAttr((Element)element2, (String)"ISV10", (double)0.0);
        this.fitnessOOS = XMLUtil.getDoubleAttr((Element)element2, (String)"OOS", (double)0.0);
        this.fitnessOOS1 = XMLUtil.getDoubleAttr((Element)element2, (String)"OOS1", (double)0.0);
        this.fitnessOOS2 = XMLUtil.getDoubleAttr((Element)element2, (String)"OOS2", (double)0.0);
        this.fitnessOOS3 = XMLUtil.getDoubleAttr((Element)element2, (String)"OOS3", (double)0.0);
        this.fitnessOOS4 = XMLUtil.getDoubleAttr((Element)element2, (String)"OOS4", (double)0.0);
        this.fitnessOOS5 = XMLUtil.getDoubleAttr((Element)element2, (String)"OOS5", (double)0.0);
        this.fitnessOOS6 = XMLUtil.getDoubleAttr((Element)element2, (String)"OOS6", (double)0.0);
        this.fitnessOOS7 = XMLUtil.getDoubleAttr((Element)element2, (String)"OOS7", (double)0.0);
        this.fitnessOOS8 = XMLUtil.getDoubleAttr((Element)element2, (String)"OOS8", (double)0.0);
        this.fitnessOOS9 = XMLUtil.getDoubleAttr((Element)element2, (String)"OOS9", (double)0.0);
        this.fitnessOOS10 = XMLUtil.getDoubleAttr((Element)element2, (String)"OOS10", (double)0.0);
    }
}

