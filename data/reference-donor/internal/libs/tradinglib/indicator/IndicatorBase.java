/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.dataseries.ComputedDataSeries
 *  com.strategyquant.datalib.dataseries.DataSeriesBase
 *  com.strategyquant.datalib.dataseries.IDataSeriesChangeListener
 *  com.strategyquant.datalib.dataseries.IDataSeriesComputer
 *  com.strategyquant.datalib.dataseries.TimeDataSeries
 *  com.strategyquant.lib.SQUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.indicator;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.dataseries.ComputedDataSeries;
import com.strategyquant.datalib.dataseries.DataSeriesBase;
import com.strategyquant.datalib.dataseries.IDataSeriesChangeListener;
import com.strategyquant.datalib.dataseries.IDataSeriesComputer;
import com.strategyquant.datalib.dataseries.TimeDataSeries;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.Buffer;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.Output;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.debug.DebugConsole;
import com.strategyquant.tradinglib.debug.Debugger;
import com.strategyquant.tradinglib.indicator.IndicatorsObj;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class IndicatorBase
implements IDataSeriesComputer,
IDataSeriesChangeListener {
    public static final Logger Log = LoggerFactory.getLogger((String)"Indicator");
    private static final Logger DebugLog = LoggerFactory.getLogger(Debugger.class);
    @Parameter
    public int Shift;
    protected DataSeriesSet[] inputDataSeries = null;
    protected DataSeriesSet[] outputDataSeries = null;
    protected int CurrentBar = 0;
    private int computingBar = -1;
    private String indicatorName;
    private boolean onInitCalled = false;
    public int Calls = 0;
    public boolean RecursionExceptionEnforced = true;
    private ArrayList<DataSeries> outputLinesForData = null;
    private int userDefinedStartingBar = 0;

    protected void Initialize() throws TradingException {
        this.OnInit();
    }

    protected void Deinitialize() throws TradingException {
        this.deinitializeDataSeries();
        this.OnDeinit();
    }

    private void deinitializeDataSeries() {
        if (this.outputDataSeries != null) {
            for (int i = 0; i < this.outputDataSeries.length; ++i) {
                this.outputDataSeries[i].destroy();
            }
        }
    }

    protected void OnInit() throws TradingException {
    }

    protected abstract void OnBarUpdate() throws TradingException;

    protected void OnDeinit() throws TradingException {
    }

    public void callOnInit() throws TradingException {
        if (!this.onInitCalled) {
            this.onInitCalled = true;
            this.Initialize();
        }
    }

    public abstract void initialize(IndicatorsObj var1, boolean var2) throws TradingException;

    public void initializeStrategy(StrategyBase strategyBase) {
    }

    public void setIndyStartingBar(int n) {
        this.userDefinedStartingBar = n;
    }

    public int getIndyStartingBar() {
        return this.userDefinedStartingBar;
    }

    protected void recognizeAndInitializeDataSeries(boolean bl) throws TradingException {
        int n = 0;
        try {
            Class<?> clazz = this.getClass();
            this.indicatorName = clazz.getSimpleName();
            for (Field field : clazz.getFields()) {
                DataSeriesSet dataSeriesSet;
                DataSeries dataSeries;
                Object object;
                Object object2;
                Parameter parameter = field.getAnnotation(Parameter.class);
                if (parameter != null) {
                    object2 = field.get(this);
                    if (object2 instanceof ComputedDataSeries) {
                        object = (ComputedDataSeries)object2;
                        n = this.addDataSeries("Open", ((ComputedDataSeries)object).Open, bl);
                        this.addDataSeries("High", ((ComputedDataSeries)object).High, bl);
                        this.addDataSeries("Low", ((ComputedDataSeries)object).Low, bl);
                        this.addDataSeries("Close", ((ComputedDataSeries)object).Close, bl);
                        this.addDataSeries("Volume", ((ComputedDataSeries)object).Volume, bl);
                        this.setIndyStartingBar(((ComputedDataSeries)object).Close.getIndyStartingBar());
                    } else if (field.getType().isAssignableFrom(DataSeries.class)) {
                        object = new DataSeriesSet();
                        ((DataSeriesSet)object).series = (DataSeries)object2;
                        ((DataSeriesSet)object).name = field.getName();
                        n = ((DataSeriesSet)object).series.size() + ((DataSeriesSet)object).series.getShift();
                        this.addInputDataSeries((DataSeriesSet)object);
                        ((DataSeriesSet)object).series.addChangeListener(this.recognizeUpdateEvent(bl), (IDataSeriesChangeListener)this);
                        this.setIndyStartingBar(((DataSeriesSet)object).series.getIndyStartingBar());
                    } else if (field.getType().isAssignableFrom(TimeDataSeries.class)) {
                        object = new DataSeriesSet();
                        ((DataSeriesSet)object).series = (DataSeriesBase)field.get(this);
                        ((DataSeriesSet)object).name = field.getName();
                        n = ((DataSeriesSet)object).series.size() + ((DataSeriesSet)object).series.getShift();
                        this.addInputDataSeries((DataSeriesSet)object);
                        this.setIndyStartingBar(((DataSeriesSet)object).series.getIndyStartingBar());
                    } else if (field.getType().isAssignableFrom(ChartData.class)) {
                        int n2;
                        object = (ChartData)field.get(this);
                        this.addDataSeries(field.getName(), ((ChartData)object).Time, bl);
                        this.addDataSeries(field.getName(), ((ChartData)object).Open, bl);
                        this.addDataSeries(field.getName(), ((ChartData)object).High, bl);
                        this.addDataSeries(field.getName(), ((ChartData)object).Low, bl);
                        this.addDataSeries(field.getName(), ((ChartData)object).Close, bl);
                        n = n2 = this.addDataSeries(field.getName(), ((ChartData)object).Volume, bl);
                        this.setIndyStartingBar(((ChartData)object).getIndyStartingBar());
                    }
                }
                if ((object2 = field.getAnnotation(Parameter.class)) != null) continue;
                object = field.getAnnotation(Output.class);
                Buffer buffer = field.getAnnotation(Buffer.class);
                if (object == null && buffer == null) continue;
                if (field.getType().isAssignableFrom(DataSeries.class)) {
                    dataSeries = new DataSeries();
                    if (n > 0) {
                        dataSeries.addValues(n);
                    }
                    field.set(this, dataSeries);
                    dataSeries.setDataComputer((IDataSeriesComputer)this);
                    dataSeriesSet = new DataSeriesSet();
                    dataSeriesSet.series = dataSeries;
                    dataSeriesSet.name = field.getName();
                    dataSeriesSet.type = 1;
                    this.addOutputDataSeries(dataSeriesSet);
                    continue;
                }
                if (!field.getType().isAssignableFrom(TimeDataSeries.class)) continue;
                dataSeries = new TimeDataSeries();
                if (n > 0) {
                    dataSeries.addValues(n);
                }
                field.set(this, dataSeries);
                dataSeries.setDataComputer((IDataSeriesComputer)this);
                dataSeriesSet = new DataSeriesSet();
                dataSeriesSet.series = dataSeries;
                dataSeriesSet.name = field.getName();
                dataSeriesSet.type = 2;
                this.addOutputDataSeries(dataSeriesSet);
            }
        }
        catch (TradingException tradingException) {
            Log.error("Cannot initialize DataSeries for indicator", (Throwable)tradingException);
            throw tradingException;
        }
        catch (IllegalArgumentException illegalArgumentException) {
            Log.error("Cannot initialize DataSeries for indicator (2)", (Throwable)illegalArgumentException);
            throw new TradingException((Exception)illegalArgumentException);
        }
        catch (IllegalAccessException illegalAccessException) {
            Log.error("Cannot initialize DataSeries for indicator (3)", (Throwable)illegalAccessException);
            throw new TradingException((Exception)illegalAccessException);
        }
    }

    private int recognizeUpdateEvent(boolean bl) {
        if (bl) {
            return 4;
        }
        return 2;
    }

    private void addInputDataSeries(DataSeriesSet dataSeriesSet) {
        if (this.inputDataSeries == null) {
            this.inputDataSeries = new DataSeriesSet[1];
        } else {
            DataSeriesSet[] dataSeriesSetArray = Arrays.copyOf(this.inputDataSeries, this.inputDataSeries.length + 1);
            this.inputDataSeries = dataSeriesSetArray;
        }
        this.inputDataSeries[this.inputDataSeries.length - 1] = dataSeriesSet;
    }

    private void addOutputDataSeries(DataSeriesSet dataSeriesSet) {
        if (this.outputDataSeries == null) {
            this.outputDataSeries = new DataSeriesSet[1];
        } else {
            DataSeriesSet[] dataSeriesSetArray = Arrays.copyOf(this.outputDataSeries, this.outputDataSeries.length + 1);
            this.outputDataSeries = dataSeriesSetArray;
        }
        this.outputDataSeries[this.outputDataSeries.length - 1] = dataSeriesSet;
    }

    private int addDataSeries(String string, DataSeries dataSeries, boolean bl) {
        DataSeriesSet dataSeriesSet = new DataSeriesSet();
        dataSeriesSet.series = dataSeries;
        dataSeriesSet.name = string;
        this.addInputDataSeries(dataSeriesSet);
        dataSeriesSet.series.addChangeListener(this.recognizeUpdateEvent(bl), (IDataSeriesChangeListener)this);
        return dataSeriesSet.series.size() + dataSeriesSet.series.getShift();
    }

    private int addDataSeries(String string, TimeDataSeries timeDataSeries, boolean bl) {
        DataSeriesSet dataSeriesSet = new DataSeriesSet();
        dataSeriesSet.series = timeDataSeries;
        dataSeriesSet.name = string;
        this.addInputDataSeries(dataSeriesSet);
        dataSeriesSet.series.addChangeListener(this.recognizeUpdateEvent(bl), (IDataSeriesChangeListener)this);
        return dataSeriesSet.series.size() + dataSeriesSet.series.getShift();
    }

    public void changed(int n, int n2) throws TradingException {
        if (this.outputDataSeries == null || this.outputDataSeries.length == 0) {
            return;
        }
        for (int i = 0; i < this.outputDataSeries.length; ++i) {
            DataSeriesSet dataSeriesSet = this.outputDataSeries[i];
            int n3 = dataSeriesSet.series.specialSize();
            if (n2 > n3) {
                int n4 = n2 - n3;
                if (dataSeriesSet.type == 1) {
                    dataSeriesSet.series.addDoubleValues(n4, 0.0);
                } else {
                    dataSeriesSet.series.addLongValues(n4, 0L);
                }
            }
            dataSeriesSet.series.updateComputedUntil(n + 1);
        }
    }

    public void compute(int n, int n2) throws TradingException {
        if (this.outputDataSeries == null) {
            throw new TradingException("No OutputDataSeries defined!");
        }
        int n3 = this.outputDataSeries[0].series.size() + this.outputDataSeries[0].series.getShift();
        if (n3 == 0) {
            return;
        }
        if (!this.RecursionExceptionEnforced && this.computingBar != -1) {
            return;
        }
        if (n == -1) {
            n = n3;
        } else if (n == n2 && n + 1 < n3) {
            ++n;
        }
        for (int i = n - 1; i >= n2; --i) {
            this.CurrentBar = n3 - i - 1;
            if (this.computingBar != -1 && this.CurrentBar <= this.computingBar) {
                return;
            }
            this.computingBar = this.CurrentBar;
            if (this.computingBar >= this.userDefinedStartingBar) {
                try {
                    this.rememberPreviousShiftAndSetNew(i);
                    this.OnBarUpdate();
                    this.restorePreviousShift();
                }
                catch (TradingException tradingException) {
                    throw tradingException.addCall(this.indicatorName + "(CurrentBar: " + this.CurrentBar + ", Index: " + i + ")");
                }
            }
            if (this.outputDataSeries == null) continue;
            for (int j = 0; j < this.outputDataSeries.length; ++j) {
                this.outputDataSeries[j].series.setComputedUntil(i);
            }
        }
        this.computingBar = -1;
    }

    private void rememberPreviousShiftAndSetNew(int n) {
        int n2;
        if (this.inputDataSeries != null) {
            for (n2 = 0; n2 < this.inputDataSeries.length; ++n2) {
                this.inputDataSeries[n2].shift = this.inputDataSeries[n2].series.getShift();
                this.inputDataSeries[n2].series.setShift(n);
            }
        }
        if (this.outputDataSeries != null) {
            for (n2 = 0; n2 < this.outputDataSeries.length; ++n2) {
                this.outputDataSeries[n2].shift = this.outputDataSeries[n2].series.getShift();
                this.outputDataSeries[n2].series.setShift(n);
            }
        }
    }

    private void restorePreviousShift() {
        int n;
        if (this.inputDataSeries != null) {
            for (n = 0; n < this.inputDataSeries.length; ++n) {
                this.inputDataSeries[n].series.setShift(this.inputDataSeries[n].shift);
            }
        }
        if (this.outputDataSeries != null) {
            for (n = 0; n < this.outputDataSeries.length; ++n) {
                this.outputDataSeries[n].series.setShift(this.outputDataSeries[n].shift);
            }
        }
    }

    public void refreshShift() {
        if (this.inputDataSeries == null) {
            return;
        }
        int n = this.inputDataSeries[0].series.getShift();
        if (this.outputDataSeries != null) {
            for (int i = 0; i < this.outputDataSeries.length; ++i) {
                this.outputDataSeries[i].series.setShift(n);
            }
        }
    }

    public void destroy() {
        int n;
        if (this.inputDataSeries != null) {
            for (n = 0; n < this.inputDataSeries.length; ++n) {
                if (this.inputDataSeries[n].series == null) continue;
                this.inputDataSeries[n].series.destroy();
                this.inputDataSeries[n] = null;
            }
            this.inputDataSeries = null;
        }
        if (this.outputDataSeries != null) {
            for (n = 0; n < this.outputDataSeries.length; ++n) {
                if (this.outputDataSeries[n].series == null) continue;
                this.outputDataSeries[n].series.destroy();
                this.outputDataSeries[n] = null;
            }
            this.outputDataSeries = null;
        }
    }

    public int getOutputsCount() {
        if (this.outputDataSeries == null) {
            return 0;
        }
        return this.outputDataSeries.length;
    }

    public ArrayList<DataSeries> getOutputLines() throws IllegalArgumentException, IllegalAccessException {
        if (this.outputLinesForData == null) {
            this.outputLinesForData = new ArrayList();
            Class<?> clazz = this.getClass();
            for (Field field : clazz.getFields()) {
                Output output = field.getAnnotation(Output.class);
                if (output == null || !field.getType().isAssignableFrom(DataSeries.class)) continue;
                DataSeries dataSeries = (DataSeries)field.get(this);
                dataSeries.setLineName(field.getName());
                dataSeries.setColor(output.color());
                dataSeries.setShowInChart(output.show());
                dataSeries.setShowZeroValues(output.showZeroValues());
                dataSeries.setChartType(output.chartType());
                this.outputLinesForData.add(dataSeries);
            }
        }
        return this.outputLinesForData;
    }

    public boolean checkUsesData(ChartData chartData) {
        if (this.inputDataSeries == null) {
            return false;
        }
        for (int i = 0; i < this.inputDataSeries.length; ++i) {
            DataSeriesSet dataSeriesSet = this.inputDataSeries[i];
            if (chartData.Time == dataSeriesSet.series) {
                return true;
            }
            if (chartData.Open == dataSeriesSet.series) {
                return true;
            }
            if (chartData.High == dataSeriesSet.series) {
                return true;
            }
            if (chartData.Low == dataSeriesSet.series) {
                return true;
            }
            if (chartData.Close == dataSeriesSet.series) {
                return true;
            }
            if (chartData.Volume != dataSeriesSet.series) continue;
            return true;
        }
        return false;
    }

    public void getDataColumnHeader(StringBuilder stringBuilder, ArrayList<String> arrayList) {
        if (this.outputDataSeries != null) {
            for (int i = 0; i < this.outputDataSeries.length; ++i) {
                DataSeriesSet dataSeriesSet = this.outputDataSeries[i];
                StringBuilder stringBuilder2 = new StringBuilder(this.indicatorName);
                if (!dataSeriesSet.name.equals("Value")) {
                    stringBuilder2.append(".");
                    stringBuilder2.append(dataSeriesSet.name);
                }
                String string = stringBuilder2.toString();
                string = this.findUniqueColumnNames(string, arrayList);
                arrayList.add(string);
                stringBuilder.append("\"");
                stringBuilder.append(string);
                stringBuilder.append("\"");
                stringBuilder.append(",");
                dataSeriesSet.series.setDataComputer(null);
                dataSeriesSet.series.setShift(0);
            }
        }
    }

    private String findUniqueColumnNames(String string, ArrayList<String> arrayList) {
        if (!this.columnNamesContain(string, arrayList)) {
            return string;
        }
        String string2 = string;
        int n = 1;
        while (true) {
            StringBuilder stringBuilder = new StringBuilder(string);
            stringBuilder.append("{");
            stringBuilder.append(n);
            stringBuilder.append("}");
            string2 = stringBuilder.toString();
            if (!this.columnNamesContain(string2, arrayList)) {
                return string2;
            }
            ++n;
        }
    }

    private boolean columnNamesContain(String string, ArrayList<String> arrayList) {
        for (String string2 : arrayList) {
            if (!string2.equals(string)) continue;
            return true;
        }
        return false;
    }

    public void setDataShift(int n, int n2) {
        DataSeriesSet dataSeriesSet = this.outputDataSeries[n];
        dataSeriesSet.series.setShift(n2);
    }

    public void setName(String string) {
        this.indicatorName = string;
    }

    public String getName() {
        if (this.indicatorName == null) {
            this.indicatorName = this.getClass().getSimpleName();
        }
        return this.indicatorName;
    }

    public String getPseudoName() {
        StringBuilder stringBuilder = new StringBuilder(this.getClass().getSimpleName());
        stringBuilder.append("(");
        this.addParameters(stringBuilder);
        stringBuilder.append(")");
        return stringBuilder.toString();
    }

    private void addParameters(StringBuilder stringBuilder) {
        Class<?> clazz = this.getClass();
        int n = 0;
        for (Field field : clazz.getFields()) {
            if (field.getName().equals("Shift")) continue;
            for (Annotation annotation : field.getAnnotations()) {
                if (!(annotation instanceof Parameter)) continue;
                String string = field.getType().getName();
                if (string.equals("int") || string.equals("long") || string.equals("double") || string.equals("boolean") || string.equals("java.lang.String") || string.equals("java.lang.Object")) {
                    if (n > 0) {
                        stringBuilder.append(", ");
                    }
                    stringBuilder.append(this.getParamPrimitiveValue(string, field));
                    ++n;
                    continue;
                }
                if (!string.equals("com.strategyquant.tradinglib.IBlock")) continue;
            }
        }
    }

    private String getParamPrimitiveValue(String string, Field field) {
        String string2 = "UNKWN";
        try {
            switch (string) {
                case "int": {
                    string2 = Integer.toString(field.getInt(this));
                    break;
                }
                case "long": {
                    string2 = Long.toString(field.getLong(this));
                    break;
                }
                case "double": {
                    string2 = SQUtils.doubleToString((double)field.getDouble(this));
                    break;
                }
                case "boolean": {
                    string2 = Boolean.toString(field.getBoolean(this));
                    break;
                }
                case "java.lang.String": {
                    string2 = (String)field.get(this);
                    break;
                }
                case "java.lang.Object": {
                    string2 = "Obj";
                }
            }
        }
        catch (IllegalAccessException | IllegalArgumentException exception) {
            // empty catch block
        }
        return string2;
    }

    private void precomputeData() throws TradingException {
        long l = System.currentTimeMillis();
        long l2 = System.currentTimeMillis();
    }

    public void debug(String string, String string2) {
        DebugConsole.log(string, string2);
    }

    public void fdebug(String string, String string2) {
        DebugLog.info(string + " - " + string2);
    }

    class DataSeriesSet {
        public static final int DATASERIES = 1;
        public static final int TIMEDATASERIES = 2;
        public int type;
        DataSeriesBase series;
        int shift = 0;
        String name;

        DataSeriesSet() {
        }

        public void destroy() {
            this.series.destroy();
        }
    }
}

