/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.optimization.NonexistingVariableException;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Comparator;
import org.jdom2.Element;

public class Variables
extends ArrayList<Variable> {
    private Element xml;

    private Variables() {
    }

    public Variables(Element element) {
        this.xml = element;
        this.parseXmlVariables();
    }

    public Variables(Object object) {
        this.xml = null;
        Class<?> clazz = object.getClass();
        block0: for (Field field : clazz.getFields()) {
            for (Annotation annotation : field.getAnnotations()) {
                if (!(annotation instanceof Parameter)) continue;
                Variable variable = new Variable(object, field);
                this.add(variable);
                continue block0;
            }
        }
    }

    private void parseXmlVariables() {
        if (this.xml == null) {
            return;
        }
        Element element = this.xml.getChild("Strategy").getChild("Variables");
        if (element == null) {
            return;
        }
        for (Element element2 : element.getChildren("variable")) {
            Variable variable = new Variable(element2);
            this.add(variable);
        }
    }

    public Variable get(String string) {
        for (int i = 0; i < this.size(); ++i) {
            Variable variable = (Variable)this.get(i);
            if (!variable.getName().equals(string)) continue;
            return variable;
        }
        return null;
    }

    public Variable getById(String string) {
        for (int i = 0; i < this.size(); ++i) {
            Variable variable = (Variable)this.get(i);
            if (!variable.getId().equals(string)) continue;
            return variable;
        }
        return null;
    }

    public Variable getByField(Object object, String string) {
        for (int i = 0; i < this.size(); ++i) {
            Variable variable = (Variable)this.get(i);
            if (!variable.isObjectRegistered(object, string)) continue;
            return variable;
        }
        return null;
    }

    public void sortByName() {
        this.sort(new Comparator<Variable>(){

            @Override
            public int compare(Variable variable, Variable variable2) {
                return variable.getName().compareTo(variable2.getName());
            }
        });
    }

    public void setValue(String string, double d) throws NonexistingVariableException {
        for (int i = 0; i < this.size(); ++i) {
            Variable variable = (Variable)this.get(i);
            if (!variable.getName().equals(string)) continue;
            switch (variable.getInternalType()) {
                case 2: {
                    variable.setValue(d != 0.0);
                    break;
                }
                case 4: {
                    variable.setValue(d);
                    break;
                }
                case 1: 
                case 5: {
                    variable.setValue((int)d);
                    break;
                }
                default: {
                    throw new NonexistingVariableException(String.format("Cannot set value for variable %s with type %d", variable.getName(), variable.getInternalType()));
                }
            }
            return;
        }
        throw new NonexistingVariableException(String.format("Variable '%s' doesn't exist!", string));
    }

    public boolean canSetValue(String string) throws NonexistingVariableException {
        for (int i = 0; i < this.size(); ++i) {
            Variable variable = (Variable)this.get(i);
            if (!variable.getName().equals(string)) continue;
            switch (variable.getInternalType()) {
                case 1: 
                case 2: 
                case 4: 
                case 5: {
                    return true;
                }
            }
            return false;
        }
        throw new NonexistingVariableException(String.format("Variable '%s' doesn't exist!", string));
    }

    public void setValueInXml(String string, double d) throws NonexistingVariableException {
        for (int i = 0; i < this.size(); ++i) {
            Variable variable = (Variable)this.get(i);
            if (!variable.getName().equals(string)) continue;
            switch (variable.getInternalType()) {
                case 2: {
                    variable.setValueInXml(d);
                    break;
                }
                case 4: {
                    variable.setValueInXml(d);
                    break;
                }
                case 1: 
                case 5: {
                    variable.setValueInXml((int)d);
                    break;
                }
                default: {
                    throw new NonexistingVariableException(String.format("Cannot set value for variabe %s with type %d", variable.getName(), variable.getInternalType()));
                }
            }
            return;
        }
        throw new NonexistingVariableException(String.format("Variable '%s' doesn't exist!", string));
    }
}

