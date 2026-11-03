/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  net.xeoh.plugins.base.PluginInformation
 *  net.xeoh.plugins.base.PluginManager
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  net.xeoh.plugins.base.annotations.meta.Version
 *  net.xeoh.plugins.base.impl.PluginManagerFactory
 *  net.xeoh.plugins.base.options.AddPluginsFromOption
 *  net.xeoh.plugins.base.options.GetPluginOption
 *  net.xeoh.plugins.base.util.PluginManagerUtil
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.pluginlib;

import com.strategyquant.pluginlib.DirManager;
import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.DownloadUrl;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.LongDesc;
import com.strategyquant.pluginlib.annotations.Mandatory;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.PageUrl;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import net.xeoh.plugins.base.PluginInformation;
import net.xeoh.plugins.base.PluginManager;
import net.xeoh.plugins.base.annotations.meta.Author;
import net.xeoh.plugins.base.annotations.meta.Version;
import net.xeoh.plugins.base.impl.PluginManagerFactory;
import net.xeoh.plugins.base.options.AddPluginsFromOption;
import net.xeoh.plugins.base.options.GetPluginOption;
import net.xeoh.plugins.base.util.PluginManagerUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQPluginManager {
    public static final Logger Log = LoggerFactory.getLogger((String)"SQPluginManager");
    public static final String PLUGIN_CATEGORY_OTHERS = "Others";
    private PluginManager pm = null;
    private static PluginManagerUtil pmu;
    private PluginInformation pi;
    private String product = null;
    private HashMap<Class, ArrayList> loadedPluginsMap = new HashMap();
    private HashMap<Class, ArrayList> availablePluginsMap = new HashMap();
    private static SQPluginManager instance;
    private static String workDirectory;

    public static SQPluginManager getInstance() {
        if (instance == null) {
            instance = new SQPluginManager();
        }
        return instance;
    }

    public static void setWorkDirectory(String string) {
        workDirectory = string;
    }

    public HashMap<Class, ArrayList> getAvailablePlugins() {
        return this.availablePluginsMap;
    }

    public static <P extends ISQPlugin> String getPluginName(Class<P> clazz) {
        String string = clazz.toString();
        int n = string.lastIndexOf(".");
        if (n > 0) {
            return string.substring(n + 1);
        }
        return string;
    }

    public static void initForProduct(String string) throws Exception {
        SQPluginManager.initForProduct(string, null);
    }

    public static void initForProduct(String string, String string2) throws Exception {
        SQPluginManager sQPluginManager = SQPluginManager.getInstance();
        sQPluginManager.pm = PluginManagerFactory.createPluginManager();
        sQPluginManager.pi = (PluginInformation)sQPluginManager.pm.getPlugin(PluginInformation.class, new GetPluginOption[0]);
        pmu = new PluginManagerUtil(sQPluginManager.pm);
        SQPluginManager.loadFromFolder("internal/plugins", string2);
        SQPluginManager.loadFromFolder("user/extend/Plugins", string2);
        sQPluginManager.product = string;
    }

    private static void loadFromFolder(String string, String string2) throws Exception {
        String string3 = workDirectory == null ? string : workDirectory + string;
        if (string2 != null && !string2.equalsIgnoreCase("")) {
            string3 = string3 + "/" + string2;
        }
        SQPluginManager.instance.pm.addPluginsFrom(new File(string3).toURI(), new AddPluginsFromOption[0]);
        for (String string4 : DirManager.listAllSubdirectoryPaths(string3)) {
            SQPluginManager.instance.pm.addPluginsFrom(new File(string4).toURI(), new AddPluginsFromOption[0]);
        }
    }

    public static <P extends ISQPlugin> ArrayList<P> getPlugins(Class<P> clazz) {
        return SQPluginManager.getInstance()._getPlugins(clazz);
    }

    private <P extends ISQPlugin> ArrayList<P> _getPlugins(Class<P> clazz) {
        if (!this.loadedPluginsMap.containsKey(clazz)) {
            return new ArrayList();
        }
        return this.loadedPluginsMap.get(clazz);
    }

    public static <P extends ISQPlugin> void loadPlugins(Class<P> clazz) throws Exception {
        SQPluginManager.getInstance()._loadPlugins(clazz);
    }

    private <P extends ISQPlugin> void _loadPlugins(Class<P> clazz) throws Exception {
        if (this.loadedPluginsMap.containsKey(clazz)) {
            return;
        }
        ArrayList arrayList = (ArrayList)pmu.getPlugins(clazz);
        ArrayList<ISQPlugin> arrayList2 = new ArrayList<ISQPlugin>();
        ArrayList<ISQPlugin> arrayList3 = new ArrayList<ISQPlugin>();
        Collections.sort(arrayList, ISQPlugin.PositionComparator);
        StringBuilder stringBuilder = new StringBuilder();
        StringBuilder stringBuilder2 = new StringBuilder();
        stringBuilder.append("Loading plugins extending ");
        stringBuilder.append(clazz.getSimpleName());
        stringBuilder.append(": ");
        for (int i = 0; i < arrayList.size(); ++i) {
            ISQPlugin iSQPlugin = (ISQPlugin)arrayList.get(i);
            String string = SQPluginManager.getPluginName(iSQPlugin);
            stringBuilder.append(i == 0 ? "" : ", ");
            stringBuilder.append(string);
            if (iSQPlugin.getProduct() == null) {
                stringBuilder2.append("Plugin '");
                stringBuilder2.append(string);
                stringBuilder2.append("' has no product defined, it is skipped!\n");
                continue;
            }
            if (!(this.product.equals("TESTAPP") || iSQPlugin.getProduct().equals("any") || iSQPlugin.getProduct().contains(this.product))) {
                stringBuilder2.append("Plugin '");
                stringBuilder2.append(string);
                stringBuilder2.append("' is created for another product, not '");
                stringBuilder2.append(this.product);
                stringBuilder2.append("'.\n");
                continue;
            }
            arrayList2.add(iSQPlugin);
            arrayList3.add(iSQPlugin);
        }
        if (Log.isDebugEnabled()) {
            Log.debug(stringBuilder.toString());
            if (stringBuilder2.length() > 0) {
                Log.debug(stringBuilder2.toString());
            }
        }
        this.loadedPluginsMap.put(clazz, arrayList2);
        this.availablePluginsMap.put(clazz, arrayList3);
        for (ISQPlugin iSQPlugin : arrayList2) {
            iSQPlugin.initPlugin();
        }
    }

    public static String getPluginAuthor(ISQPlugin iSQPlugin) {
        Class<?> clazz = iSQPlugin.getClass();
        Author author = clazz.getAnnotation(Author.class);
        if (author instanceof Author) {
            Author author2 = author;
            return author2.name();
        }
        return "Unknown";
    }

    public static String getLicense(ISQPlugin iSQPlugin) {
        Class<?> clazz = iSQPlugin.getClass();
        License license = clazz.getAnnotation(License.class);
        if (license instanceof License) {
            License license2 = license;
            return license2.text();
        }
        return "Unknown";
    }

    public static boolean isPluginMandatory(ISQPlugin iSQPlugin) {
        Class<?> clazz = iSQPlugin.getClass();
        Mandatory mandatory = clazz.getAnnotation(Mandatory.class);
        if (mandatory instanceof Mandatory) {
            Mandatory mandatory2 = mandatory;
            return mandatory2.value();
        }
        return false;
    }

    public static String getPluginName(ISQPlugin iSQPlugin) {
        Class<?> clazz = iSQPlugin.getClass();
        Name name = clazz.getAnnotation(Name.class);
        if (name instanceof Name) {
            Name name2 = name;
            return name2.name();
        }
        return iSQPlugin.getClass().getSimpleName();
    }

    public static String getPluginCategory(ISQPlugin iSQPlugin) {
        Class<?> clazz = iSQPlugin.getClass();
        Category category = clazz.getAnnotation(Category.class);
        if (category instanceof Category) {
            Category category2 = category;
            return category2.name();
        }
        return PLUGIN_CATEGORY_OTHERS;
    }

    public static String getPluginShortDesc(ISQPlugin iSQPlugin) {
        Class<?> clazz = iSQPlugin.getClass();
        ShortDesc shortDesc = clazz.getAnnotation(ShortDesc.class);
        if (shortDesc instanceof ShortDesc) {
            ShortDesc shortDesc2 = shortDesc;
            return shortDesc2.text();
        }
        return "";
    }

    public static String getPluginLongDesc(ISQPlugin iSQPlugin) {
        Class<?> clazz = iSQPlugin.getClass();
        LongDesc longDesc = clazz.getAnnotation(LongDesc.class);
        if (longDesc instanceof LongDesc) {
            LongDesc longDesc2 = longDesc;
            return longDesc2.text();
        }
        return "";
    }

    public static String getPluginPageUrl(ISQPlugin iSQPlugin) {
        Class<?> clazz = iSQPlugin.getClass();
        PageUrl pageUrl = clazz.getAnnotation(PageUrl.class);
        if (pageUrl instanceof PageUrl) {
            PageUrl pageUrl2 = pageUrl;
            return pageUrl2.url();
        }
        return "";
    }

    public static String getPluginDownloadUrl(ISQPlugin iSQPlugin) {
        Class<?> clazz = iSQPlugin.getClass();
        DownloadUrl downloadUrl = clazz.getAnnotation(DownloadUrl.class);
        if (downloadUrl instanceof DownloadUrl) {
            DownloadUrl downloadUrl2 = downloadUrl;
            return downloadUrl2.url();
        }
        return "";
    }

    public static int getPluginVersion(ISQPlugin iSQPlugin) {
        Class<?> clazz = iSQPlugin.getClass();
        Version version = clazz.getAnnotation(Version.class);
        if (version instanceof Version) {
            Version version2 = version;
            return version2.version();
        }
        return 0;
    }

    public static String printPluginVersion(ISQPlugin iSQPlugin) {
        int n = SQPluginManager.getPluginVersion(iSQPlugin);
        return SQPluginManager.formatVersion(n);
    }

    public static ISQPlugin findPluginByName(String string) {
        if (string == null) {
            return null;
        }
        for (Map.Entry<Class, ArrayList> entry : SQPluginManager.getInstance().availablePluginsMap.entrySet()) {
            for (Object e : entry.getValue()) {
                if (!(e instanceof ISQPlugin) || !string.equals(SQPluginManager.getPluginName((ISQPlugin)e))) continue;
                return (ISQPlugin)e;
            }
        }
        return null;
    }

    public static String formatVersion(int n) {
        try {
            String string = "";
            String string2 = String.valueOf(n);
            if (string2.length() == 5) {
                string2 = "0" + string2;
            } else if (string2.length() != 6) {
                throw new Exception("Incorrect version definition. Version=" + n);
            }
            string = Integer.parseInt(string2.substring(0, 2)) + "";
            string = string + "." + Integer.parseInt(string2.substring(2, 4));
            string = string + "." + Integer.parseInt(string2.substring(4, 6));
            return string;
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
            return "0";
        }
    }

    public static <P extends ISQPlugin> ArrayList<P> getAllAvailablePlugins(Class<P> clazz) {
        return (ArrayList)pmu.getPlugins(clazz);
    }

    static {
        workDirectory = null;
    }
}

