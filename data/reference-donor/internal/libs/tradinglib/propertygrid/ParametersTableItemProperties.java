/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.time.SQTimeOld
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.propertygrid;

import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.Activator;
import com.strategyquant.tradinglib.Editor;
import com.strategyquant.tradinglib.Editors;
import com.strategyquant.tradinglib.ForEngine;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.debug.Debugger;
import com.strategyquant.tradinglib.propertygrid.IPGParameter;
import com.strategyquant.tradinglib.propertygrid.PGBooleanParameter;
import com.strategyquant.tradinglib.propertygrid.PGComboParameter;
import com.strategyquant.tradinglib.propertygrid.PGDoubleParameter;
import com.strategyquant.tradinglib.propertygrid.PGIntParameter;
import com.strategyquant.tradinglib.propertygrid.PGStringParameter;
import com.strategyquant.tradinglib.propertygrid.PGTimeParameter;
import com.strategyquant.tradinglib.propertygrid.ParameterDoesntExistException;
import java.io.Serializable;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.TreeMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ParametersTableItemProperties
extends Debugger
implements Serializable {
    public static final Logger Log = LoggerFactory.getLogger((String)"ParametersTableItemProperties");
    public static final SimpleDateFormat df = new SimpleDateFormat(SQTimeOld.shortDateFormat);
    public static final int TYPE_INT = 1;
    public static final int TYPE_DOUBLE = 2;
    public static final int TYPE_BOOLEAN = 3;
    public static final int TYPE_INT_LIST = 4;
    public static final int TYPE_STR_LIST = 5;
    public static final int TYPE_TIME = 10;
    public static final int TYPE_DATE = 20;
    public static final int TYPE_STRING = 30;
    protected ArrayList<String> propertiesOrder = new ArrayList();
    private ArrayList<IPGParameter> params = null;

    public ParametersTableItemProperties() {
        this.setDefaultValues();
    }

    public void setParams(ArrayList<IPGParameter> arrayList) {
        this.params = arrayList;
    }

    public ArrayList<IPGParameter> getParams() {
        if (this.params == null) {
            this.params = new ArrayList();
            block20: for (Field field : this.getClass().getFields()) {
                String string = field.getName();
                Parameter parameter = field.getAnnotation(Parameter.class);
                if (parameter == null) continue;
                Activator activator = field.getAnnotation(Activator.class);
                String string2 = activator != null ? activator.param() : null;
                ForEngine forEngine = field.getAnnotation(ForEngine.class);
                String string3 = forEngine != null ? forEngine.value() : null;
                switch (field.getType().getSimpleName()) {
                    case "int": {
                        IPGParameter iPGParameter;
                        Editor editor = field.getAnnotation(Editor.class);
                        if (editor != null) {
                            if (editor.type() == 110) {
                                iPGParameter = new PGTimeParameter();
                                ((PGTimeParameter)iPGParameter).setKey(string);
                                ((PGTimeParameter)iPGParameter).setName(parameter.name());
                                ((PGTimeParameter)iPGParameter).setCategory(parameter.category());
                                ((PGTimeParameter)iPGParameter).setEngine(string3);
                                ((PGTimeParameter)iPGParameter).setActivator(string2);
                                ((PGTimeParameter)iPGParameter).setDescription(this.getHelpValue(field));
                                try {
                                    ((PGTimeParameter)iPGParameter).setValue((int)Double.parseDouble(parameter.defaultValue()));
                                }
                                catch (Exception exception) {
                                    ((PGTimeParameter)iPGParameter).setValue(3600);
                                }
                                this.params.add(iPGParameter);
                                continue block20;
                            }
                            if (editor.type() == 40) {
                                iPGParameter = new PGComboParameter();
                                ((PGComboParameter)iPGParameter).setKey(string);
                                ((PGComboParameter)iPGParameter).setName(parameter.name());
                                ((PGComboParameter)iPGParameter).setCategory(parameter.category());
                                ((PGComboParameter)iPGParameter).setEngine(string3);
                                ((PGComboParameter)iPGParameter).setActivator(string2);
                                ((PGComboParameter)iPGParameter).setDescription(this.getHelpValue(field));
                                ((PGComboParameter)iPGParameter).setValue(parameter.defaultValue());
                                ((PGComboParameter)iPGParameter).setOptions(this.getOptions(editor));
                                this.params.add(iPGParameter);
                                continue block20;
                            }
                            Log.error("Unsupported type of Editor - " + editor.type());
                            continue block20;
                        }
                        iPGParameter = new PGIntParameter();
                        ((PGIntParameter)iPGParameter).setKey(string);
                        ((PGIntParameter)iPGParameter).setName(parameter.name());
                        ((PGIntParameter)iPGParameter).setCategory(parameter.category());
                        ((PGIntParameter)iPGParameter).setEngine(string3);
                        ((PGIntParameter)iPGParameter).setActivator(string2);
                        ((PGIntParameter)iPGParameter).setDescription(this.getHelpValue(field));
                        ((PGIntParameter)iPGParameter).setMax((int)parameter.maxValue());
                        ((PGIntParameter)iPGParameter).setMin((int)parameter.minValue());
                        ((PGIntParameter)iPGParameter).setStep((int)parameter.step());
                        try {
                            ((PGIntParameter)iPGParameter).setValue((int)Double.parseDouble(parameter.defaultValue()));
                        }
                        catch (Exception exception) {
                            ((PGIntParameter)iPGParameter).setValue(((PGIntParameter)iPGParameter).getMin());
                        }
                        this.params.add(iPGParameter);
                        continue block20;
                    }
                    case "double": {
                        IPGParameter iPGParameter = new PGDoubleParameter();
                        ((PGDoubleParameter)iPGParameter).setKey(string);
                        ((PGDoubleParameter)iPGParameter).setName(parameter.name());
                        ((PGDoubleParameter)iPGParameter).setCategory(parameter.category());
                        ((PGDoubleParameter)iPGParameter).setEngine(string3);
                        ((PGDoubleParameter)iPGParameter).setActivator(string2);
                        ((PGDoubleParameter)iPGParameter).setDescription(this.getHelpValue(field));
                        ((PGDoubleParameter)iPGParameter).setMax(parameter.maxValue());
                        ((PGDoubleParameter)iPGParameter).setMin(parameter.minValue());
                        ((PGDoubleParameter)iPGParameter).setStep(parameter.step());
                        ((PGDoubleParameter)iPGParameter).setDecimals(parameter.decimals());
                        try {
                            ((PGDoubleParameter)iPGParameter).setValue(Double.parseDouble(parameter.defaultValue()));
                        }
                        catch (Exception exception) {
                            ((PGDoubleParameter)iPGParameter).setValue(((PGDoubleParameter)iPGParameter).getMin());
                        }
                        this.params.add(iPGParameter);
                        continue block20;
                    }
                    case "String": {
                        IPGParameter iPGParameter;
                        Editor editor = field.getAnnotation(Editor.class);
                        if (editor != null) {
                            if (editor.type() == 40) {
                                iPGParameter = new PGComboParameter();
                                ((PGComboParameter)iPGParameter).setKey(string);
                                ((PGComboParameter)iPGParameter).setName(parameter.name());
                                ((PGComboParameter)iPGParameter).setCategory(parameter.category());
                                ((PGComboParameter)iPGParameter).setEngine(string3);
                                ((PGComboParameter)iPGParameter).setActivator(string2);
                                ((PGComboParameter)iPGParameter).setDescription(this.getHelpValue(field));
                                ((PGComboParameter)iPGParameter).setValue(parameter.defaultValue());
                                ((PGComboParameter)iPGParameter).setOptions(this.getOptions(editor));
                                this.params.add(iPGParameter);
                                continue block20;
                            }
                            Log.error("Unsupported type of Editor - " + editor.type());
                            continue block20;
                        }
                        iPGParameter = new PGStringParameter();
                        ((PGStringParameter)iPGParameter).setKey(string);
                        ((PGStringParameter)iPGParameter).setName(parameter.name());
                        ((PGStringParameter)iPGParameter).setCategory(parameter.category());
                        ((PGStringParameter)iPGParameter).setEngine(string3);
                        ((PGStringParameter)iPGParameter).setActivator(string2);
                        ((PGStringParameter)iPGParameter).setDescription(this.getHelpValue(field));
                        ((PGStringParameter)iPGParameter).setValue(parameter.defaultValue());
                        this.params.add(iPGParameter);
                        continue block20;
                    }
                    case "boolean": {
                        IPGParameter iPGParameter = new PGBooleanParameter();
                        ((PGBooleanParameter)iPGParameter).setKey(string);
                        ((PGBooleanParameter)iPGParameter).setName(parameter.name());
                        ((PGBooleanParameter)iPGParameter).setCategory(parameter.category());
                        ((PGBooleanParameter)iPGParameter).setEngine(string3);
                        ((PGBooleanParameter)iPGParameter).setActivator(string2);
                        ((PGBooleanParameter)iPGParameter).setDescription(this.getHelpValue(field));
                        try {
                            ((PGBooleanParameter)iPGParameter).setValue(Boolean.parseBoolean(parameter.defaultValue()));
                        }
                        catch (Exception exception) {
                            ((PGBooleanParameter)iPGParameter).setValue(false);
                        }
                        this.params.add(iPGParameter);
                    }
                }
            }
        }
        return this.params;
    }

    public void setDefaultValues() {
        for (Field field : this.getClass().getFields()) {
            try {
                Parameter parameter = field.getAnnotation(Parameter.class);
                if (parameter == null || parameter.defaultValue().equals("Null")) continue;
                switch (field.getType().getSimpleName()) {
                    case "int": {
                        field.setInt(this, Integer.parseInt(parameter.defaultValue()));
                        break;
                    }
                    case "double": {
                        field.setDouble(this, Double.parseDouble(parameter.defaultValue()));
                        break;
                    }
                    case "String": {
                        field.set(this, parameter.defaultValue());
                        break;
                    }
                    case "boolean": {
                        field.setBoolean(this, Boolean.parseBoolean(parameter.defaultValue()));
                    }
                }
            }
            catch (Exception exception) {
                Log.error("Error while loading default values of snippet " + this.getClass().getSimpleName() + " / " + field.getName(), (Throwable)exception);
            }
        }
    }

    private String getHelpValue(Field field) {
        Help help = field.getAnnotation(Help.class);
        if (help != null) {
            return help.value();
        }
        return "Null";
    }

    protected void applyParameters(Object[] objectArray) throws Exception {
        int n = 0;
        for (Field field : this.getClass().getFields()) {
            for (Annotation annotation : field.getAnnotations()) {
                if (!(annotation instanceof Parameter)) continue;
                IPGParameter iPGParameter = this.getPGParameter(field.getName());
                iPGParameter.setValue(objectArray[n] + "");
                field.set(this, objectArray[n]);
                ++n;
            }
        }
    }

    protected void applyParameters(ArrayList<IPGParameter> arrayList) throws Exception {
        for (Field field : this.getClass().getFields()) {
            for (Annotation annotation : field.getAnnotations()) {
                if (!(annotation instanceof Parameter)) continue;
                boolean bl = false;
                String string = field.getName();
                for (IPGParameter iPGParameter : arrayList) {
                    if (!iPGParameter.getKey().equals(string)) continue;
                    switch (iPGParameter.getType()) {
                        case 1: {
                            field.set(this, ((PGIntParameter)iPGParameter).getValue());
                            break;
                        }
                        case 2: {
                            field.set(this, ((PGDoubleParameter)iPGParameter).getValue());
                            break;
                        }
                        case 3: {
                            field.set(this, ((PGBooleanParameter)iPGParameter).getValue());
                            break;
                        }
                        case 30: {
                            field.set(this, ((PGStringParameter)iPGParameter).getValue());
                            break;
                        }
                        case 4: {
                            field.set(this, ((PGComboParameter)iPGParameter).getValue());
                            break;
                        }
                        case 5: {
                            field.set(this, ((PGComboParameter)iPGParameter).getValue());
                            break;
                        }
                        case 10: {
                            field.set(this, ((PGTimeParameter)iPGParameter).getValue());
                            break;
                        }
                        default: {
                            throw new Exception(String.format("Cannot recognize type %d for parameter %s", iPGParameter.getType(), string));
                        }
                    }
                    bl = true;
                    break;
                }
                if (bl) continue;
                throw new Exception("Value for parameter '" + string + "' not found when creating new instance");
            }
        }
    }

    public Object getPGParameterValue(String string) throws Exception {
        IPGParameter iPGParameter = this.getPGParameter(string);
        switch (iPGParameter.getType()) {
            case 1: {
                return ((PGIntParameter)iPGParameter).getValue();
            }
            case 2: {
                return ((PGDoubleParameter)iPGParameter).getValue();
            }
            case 3: {
                return ((PGBooleanParameter)iPGParameter).getValue();
            }
            case 30: {
                return ((PGStringParameter)iPGParameter).getValue();
            }
            case 4: {
                return ((PGComboParameter)iPGParameter).getValue();
            }
            case 5: {
                return ((PGComboParameter)iPGParameter).getValue();
            }
            case 20: {
                throw new Exception("Not implemented yet!");
            }
            case 10: {
                return ((PGTimeParameter)iPGParameter).getValue();
            }
        }
        throw new Exception(String.format("Cannot recognize type %d for parameter %s", iPGParameter.getType(), string));
    }

    public synchronized List<String> getParametersList() {
        if (this.params == null) {
            this.getParams();
        }
        ArrayList<String> arrayList = new ArrayList<String>();
        for (IPGParameter iPGParameter : this.params) {
            arrayList.add(iPGParameter.getKey());
        }
        return arrayList;
    }

    public void setParameterValue(String string, String string2) throws Exception {
        block3: {
            try {
                Field field = this.getClass().getField(string);
                Editor editor = field.getAnnotation(Editor.class);
                if (editor != null && editor.type() == 110) {
                    string2 = Editors.convertTimeToHHMM(string2);
                }
                this.setFieldValue(field, string2);
                IPGParameter iPGParameter = this.getPGParameter(string);
                iPGParameter.setValue(string2);
            }
            catch (NoSuchFieldException noSuchFieldException) {
                if (!Log.isDebugEnabled()) break block3;
                Log.debug("Couldn't set parameter value - NoSuchField: {}.{}={}", new Object[]{this.getClass().getSimpleName(), string, string2});
            }
        }
    }

    private void setFieldValue(Field field, String string) throws Exception {
        Class<Serializable> clazz = field.getType();
        if (string.trim().equalsIgnoreCase("nan")) {
            throw new Exception(String.format("'%s' parameter value cannot be NaN", field.getName()));
        }
        if (clazz.isAssignableFrom(Integer.class) || clazz.isAssignableFrom(Integer.TYPE)) {
            field.set(this, Integer.parseInt(string));
        } else if (clazz.isAssignableFrom(Long.class) || clazz.isAssignableFrom(Long.TYPE)) {
            field.set(this, Long.parseLong(string));
        } else if (clazz.isAssignableFrom(Double.class) || clazz.isAssignableFrom(Double.TYPE)) {
            field.set(this, Double.parseDouble(string));
        } else if (clazz.isAssignableFrom(Float.class) || clazz.isAssignableFrom(Float.TYPE)) {
            field.set(this, Float.valueOf(Float.parseFloat(string)));
        } else if (clazz.isAssignableFrom(Boolean.class) || clazz.isAssignableFrom(Boolean.TYPE)) {
            field.set(this, Boolean.parseBoolean(string));
        } else {
            field.set(this, string);
        }
    }

    public Object getParameterValue(String string) throws Exception {
        Field field = this.getClass().getField(string);
        return field.get(this);
    }

    private IPGParameter getPGParameter(String string) throws ParameterDoesntExistException {
        for (IPGParameter iPGParameter : this.getParams()) {
            if (!iPGParameter.getKey().equals(string)) continue;
            return iPGParameter;
        }
        throw new ParameterDoesntExistException(string);
    }

    public TreeMap<String, String> getCustomOptions() {
        return null;
    }

    private TreeMap<String, String> getOptions(Editor editor) {
        TreeMap<String, String> treeMap = this.getCustomOptions();
        return treeMap == null ? this.getOptions(editor.values()) : treeMap;
    }

    private TreeMap<String, String> getOptions(String string) {
        String[] stringArray;
        TreeMap<String, String> treeMap = new TreeMap<String, String>();
        for (String string2 : stringArray = string.split(",")) {
            String[] stringArray2 = string2.split("=");
            if (stringArray2.length == 2) {
                String string3 = stringArray2[0].trim();
                String string4 = stringArray2[1].trim();
                treeMap.put(string3, string4);
                continue;
            }
            Log.debug(String.format("ComboBox items - Invalid item definition '%s'.", string2));
        }
        return treeMap;
    }
}

