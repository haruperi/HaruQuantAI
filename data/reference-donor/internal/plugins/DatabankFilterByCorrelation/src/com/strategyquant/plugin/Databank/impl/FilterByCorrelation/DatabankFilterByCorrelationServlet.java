package com.strategyquant.plugin.Databank.impl.FilterByCorrelation;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import com.strategyquant.tradinglib.correlation.DatabankCorrelationFilter;

import org.json.JSONObject;
import java.util.Map;

public class DatabankFilterByCorrelationServlet extends HttpJSONServlet {

	private static final Logger Log = LoggerFactory.getLogger(DatabankFilterByCorrelationServlet.class);

    @Override
    protected String execute(String command, Map<String, String[]> args, String method){
        switch(command) {
            case "filter": return onFilter(args);
            default:
                return apiErrorJSON("Execution failed. Unknown command '"+command+"'.", null);
        }
    }

    //------------------------------------------------------------------------

    private String onFilter(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = tryGetParam(args, "projectName")[0];
            String databankName = tryGetParam(args, "databankName")[0];
            int period = Integer.parseInt(tryGetParam(args, "period")[0]);
            double maxCorrelation = Double.parseDouble(tryGetParam(args, "maxCorrelation")[0]);

            // the filtering itself is shared with the filter_by_correlation MCP tool
            int removedCount = DatabankCorrelationFilter.filter(projectName, databankName, period, maxCorrelation).size();

            response.put("success", "Strategies filtered, "+removedCount+" strategies removed.");
            return response.toString();
        }
        catch(Exception e){
            Log.error("Error while filtering strategies by correlation", e);
            response.put("error", "Filtering failed - " + e.getMessage());
            return response.toString();
        }
    }
}
