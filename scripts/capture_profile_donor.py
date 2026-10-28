"""Capture reference profile outputs by compiling unmodified donor Java methods.

Requires a JDK and the local SQX source checkout. Only chart access, configuration,
logging and unused rendering hooks are stubbed. The histogram and analysis method
bodies are extracted verbatim, not translated into a second Python oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def method(source: str, name: str) -> str:
    """Extract one method through the next method-level closing brace."""
    match = re.search(r"    (?:protected|private) [^\n]+\b" + name + r"\(", source)
    if match is None:
        raise ValueError(name)
    end = source.index("\n    }", match.start()) + len("\n    }")
    return source[match.start() : end].replace("throws TradingException", "")


# Orchestration deliberately keeps generated Java and its reference cases together.
def main() -> None:  # noqa: PLR0912
    """Compile source-derived harnesses and write deterministic reference cases."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--donor", type=Path, default=Path(r"C:\SQX-145\internal\extend\Snippets\SQ")
    )
    args = parser.parse_args()
    internal = args.donor / "Internal"
    vp = (internal / "VolumeProfileIndicatorChart.java").read_text()
    tpo = (internal / "TPOProfileIndicatorChart.java").read_text()
    common = """
    static class SQTime {
        static final int MONDAY=1;
        static java.time.ZonedDateTime date(long t) {return java.time.Instant.ofEpochMilli(t).atZone(java.time.ZoneOffset.UTC);}
        static long millis(java.time.ZonedDateTime d) {return d.toInstant().toEpochMilli();}
        static String toFullDateTimeString(long t) {return Long.toString(t);}
        static long setTime(long t,int h,int m,int s,int ms) {return millis(date(t).withHour(h).withMinute(m).withSecond(s).withNano(ms*1000000));}
        static long addDays(long t,int n) {return millis(date(t).plusDays(n));}
        static long addMonths(long t,int n) {return millis(date(t).plusMonths(n));}
        static long addYears(long t,int n) {return millis(date(t).plusYears(n));}
        static long addHours(long t,int n) {return millis(date(t).plusHours(n));}
        static int getHour(long t) {return date(t).getHour();}
        static long setDayOfWeek(long t,int n) {return millis(date(t).with(java.time.temporal.ChronoField.DAY_OF_WEEK,n));}
        static long setDayOfMonth(long t,int n) {return millis(date(t).withDayOfMonth(n));}
        static long setMonthOfYear(long t,int n) {return millis(date(t).withMonth(n));}
    }
    static class SQUtils {static int fixAllowedRange(int x,int lo,int hi,int fallback) {return x<lo||x>hi?fallback:x;}}
    static class DataSeries {double value=0;void set(int shift,double v) {value=v;}}
    static class Info { double tickStep = .25; }
    static class Chart {
        double[][] data;
        int cursor;
        Chart(double[][] rows) {data=rows;cursor=rows.length-1;}
        double[] row(int i) {return data[cursor-i];}
        long Time(int i) {return (long)row(i)[0];}
        double Open(int i) {return row(i)[1];}
        double High(int i) {return row(i)[2];}
        double Low(int i) {return row(i)[3];}
        double Close(int i) {return row(i)[4];}
        double Volume(int i) {return row(i)[5];}
        Info getInstrumentInfo() {return new Info();}
    }
    Chart chart;
    Chart Chart;
    int CurrentBar=0,SessionType=1;
    double TickSize=0;
    boolean UseCustomHours=false;
    int StartHour=0,StartMinute=0,EndHour=23,EndMinute=59;
    long currentSessionStart=0,currentSessionEnd=0;
    long prevSessionStart=1704067200000L, prevSessionEnd=1704153600000L;
    double prevIBH=0,prevIBL=0,prevTotalVolume=0,prevTotalBullVolume=0,prevTotalBearVolume=0;
    int lastNumBins=0;
    static final int MAX_BINS=2000;
    int mode=1,rows=10; boolean clusters=false;
    Chart cfgChart() {return chart;}
    int cfgBinSizeMode() {return mode;}
    int cfgProfileRows() {return rows;}
    int cfgTicksPerBin() {return 1;}
    double cfgValueAreaPct() {return 70;}
    int cfgHvnCount() {return 5;}
    int cfgHvnThresholdPct() {return 20;}
    int cfgLvnThresholdPct() {return 40;}
    boolean cfgEnableLVN() {return true;}
    boolean cfgEnableVCP() {return clusters;}
    double cfgClusterSpread() {return 1.5;}
    int cfgMaxClusterCenters() {return 2;}
    boolean cfgStoreChartData() {return false;}
    int cfgIBMinutes() {return 0;}
    int cfgSessionType() {return SessionType;}
    int cfgBracketMinDaily() {return 30;}
    int cfgBracketMinWeekly() {return 240;}
    int cfgBracketMinMonthly() {return 720;}
    int cfgBracketMinYearly() {return 720;}
    int pivotMethod=1;
    int cfgPivotMethod() {return pivotMethod;}
    int cfgPivotTicks() {return 50;}
    double cfgPivotPct() {return 2.;}
    double cfgPivotATRMultiple() {return 1.5;}
    int cfgPivotATRPeriod() {return 14;}
    void ensureArrays() {}
    int clampInt(int x,int lo,int hi) {return Math.max(lo,Math.min(hi,x));}
    boolean isSunday(long t) {return java.time.Instant.ofEpochMilli(t).atZone(java.time.ZoneOffset.UTC).getDayOfWeek()==java.time.DayOfWeek.SUNDAY;}
    void debug(String a,String b) {}
    void pushSessionHistory(double a,double b) {}
    void pushSessionHistory(double a,double b,double c) {}
"""
    # The declared numerical fields are copied too, preserving initialization.
    vp_fields = vp[
        vp.index("    protected double prevPOC") : vp.index("    // ZigZag state")
    ]
    vp_fields += "\n double[] volumeBins,clusterBins;\n"
    vp_fields += vp[
        vp.index("    protected int zzDirection") : vp.index(
            "    // Arrays for profile calculation"
        )
    ]
    tpo_fields = tpo[
        tpo.index("    protected double prevTPO_POC") : tpo.index(
            "    // TPO history arrays"
        )
    ]
    vp_methods = [
        "calculateVolumeProfile",
        "calculateValueArea",
        "findHVNs",
        "findLVNs",
        "applyClusterEnhancement",
    ]
    tpo_methods = [
        "calculateTPOProfile",
        "calculateTPOLevels",
        "findMaxIndexInt",
        "calculateValueAreaInt",
        "detectProfileShape",
    ]
    vp_names = {
        "poc": "prevPOC",
        "vah": "prevVAH",
        "val": "prevVAL",
        "ibh": "prevIBH",
        "ibl": "prevIBL",
        **{f"hvn{i + 1}": f"prevHVN[{i}]" for i in range(5)},
        **{f"lvn{i + 1}": f"prevLVN[{i}]" for i in range(5)},
        "vpoc": "prevVPOC",
        "vvah": "prevVVAH",
        "vval": "prevVVAL",
        "bull_poc": "prevBullPOC",
        "bear_poc": "prevBearPOC",
        "total_volume": "prevTotalVolume",
        "total_bull_volume": "prevTotalBullVolume",
        "total_bear_volume": "prevTotalBearVolume",
        "delta": "prevDelta",
        "delta_poc": "prevDeltaPOC",
        "delta_va": "prevDeltaVA",
        "profile_range": "prevRange",
        "poc_pct_up": "prevPOCPctUp",
        "poc_pct_down": "prevPOCPctDown",
    }
    tpo_names = {
        "poc": "prevTPO_POC",
        "vah": "prevTPO_VAH",
        "val": "prevTPO_VAL",
        "ib_high": "prevIBH",
        "ib_low": "prevIBL",
        "vpoc": "prevTPO_VPOC",
        "vvah": "prevTPO_VVAH",
        "vval": "prevTPO_VVAL",
        "bull_poc": "prevTPO_BullPOC",
        "bear_poc": "prevTPO_BearPOC",
        "total_volume": "prevTotalVolume",
        "total_bull_volume": "prevTotalBullVolume",
        "total_bear_volume": "prevTotalBearVolume",
        **{
            name: f"({field}?1.:0.)"
            for name, field in (
                ("poor_high", "lastPoorHigh"),
                ("poor_low", "lastPoorLow"),
                ("excess_high", "lastExcessHigh"),
                ("excess_low", "lastExcessLow"),
            )
        },
        "single_prints": "lastSinglePrintCount",
        "buying_tail_len": "lastBuyingTailLen",
        "selling_tail_len": "lastSellingTailLen",
        "profile_shape": "lastProfileShape",
        "ledge_up": "lastLedgeUpPrice",
        "ledge_down": "lastLedgeDownPrice",
    }
    rng = np.random.default_rng(781)
    datasets = []
    for label, count in (
        ("intraday", 48),
        ("sparse", 7),
        ("single_bar", 1),
        ("zero_volume", 12),
        ("bull_only", 24),
        ("bear_only", 24),
        ("capped_bins", 4),
    ):
        close = 100 + np.cumsum(rng.normal(0, 0.8, count))
        open_ = close + rng.normal(0, 0.5, count)
        if label == "bull_only":
            open_ = close - 0.2
        if label == "bear_only":
            open_ = close + 0.2
        high = np.maximum(close, open_) + rng.uniform(0.1, 2, count)
        low = np.minimum(close, open_) - rng.uniform(0.1, 2, count)
        if label == "capped_bins":
            high += 1000
        volume = rng.integers(1, 500, count).astype(float)
        if label == "zero_volume":
            volume[:] = 0
        times = 1704067200000 + np.arange(count) * 600_000
        datasets.append(
            (label, np.column_stack((times, open_, high, low, close, volume)).tolist())
        )
    captures = []
    sessions = []
    vp_block = args.donor / "Blocks/Indicators/VolumeProfile/VolumeProfile.java"
    tpo_block = args.donor / "Blocks/Indicators/TPOProfile/TPOProfile.java"
    custom_block = (
        args.donor / "Blocks/Indicators/VolumeProfile/VolumeProfileCustomHours.java"
    )
    multi_block = (
        args.donor
        / "Blocks/Indicators/VolumeProfile/VolumeProfileCustomHoursMultiSession.java"
    )
    with tempfile.TemporaryDirectory(prefix="profile-donor-") as temporary:
        directory = Path(temporary)
        for name, source, fields, methods, outputs in (
            ("VP", vp, vp_fields, vp_methods, vp_names),
            ("TPO", tpo, tpo_fields, tpo_methods, tpo_names),
        ):
            block_source = (vp_block if name == "VP" else tpo_block).read_text()
            extra = (
                method(block_source, "OnBarUpdate")
                + "\n"
                + method(block_source, "calculateSessionBoundaries")
            )
            extra += "\n" + method(source, "getIBPeriodMillis")
            if name == "VP":
                extra += "\n" + "\n".join(
                    method(source, m)
                    for m in (
                        "computePivotThreshold",
                        "computeATR",
                        "detectZigZagPivot",
                    )
                )
            else:
                extra += "\n" + method(source, "getBracketMillis")
            extra += "\n" + "\n".join(
                "DataSeries " + field + "=new DataSeries();"
                for field in re.findall(r"public DataSeries (\w+);", block_source)
            )
            if name == "VP":
                custom_source = custom_block.read_text()
                extra += "\nstatic class Custom extends VP {\nint SessionMode=1,SessionStartHours=8,SessionStartMinutes=0,SessionEndHours=16,SessionEndMinutes=0;\n"
                extra += (
                    method(custom_source, "OnBarUpdate")
                    + "\n"
                    + method(custom_source, "calculateSessionBoundaries")
                    + "\n}\n"
                )
                multi_source = multi_block.read_text()
                multi_fields = multi_source[
                    multi_source.index(
                        "    private static final int NUM_SESSIONS"
                    ) : multi_source.index(
                        "    // Arrays for profile calculation (reused across sessions)"
                    )
                ]
                extra += (
                    "\nstatic class Multi extends VP {\n"
                    + multi_fields
                    + "\nint activeSes=0,SessionMode=1;\n"
                )
                extra += "boolean EnableLondon=true,EnableNewYork=true,EnableSydney=false,EnableTokyo=true;\n"
                extra += "int LondonStartHour=7,LondonStartMin=0,LondonEndHour=16,LondonEndMin=0,NewYorkStartHour=13,NewYorkStartMin=0,NewYorkEndHour=22,NewYorkEndMin=0,SydneyStartHour=21,SydneyStartMin=0,SydneyEndHour=6,SydneyEndMin=0,TokyoStartHour=0,TokyoStartMin=0,TokyoEndHour=9,TokyoEndMin=0;\n"
                named_outputs = [
                    field
                    for field in re.findall(r"public DataSeries (\w+);", multi_source)
                    if field
                    not in re.findall(r"public DataSeries (\w+);", block_source)
                ]
                extra += "\n".join(
                    "DataSeries " + field + "=new DataSeries();"
                    for field in named_outputs
                )
                extra += (
                    "\n"
                    + "\n".join(
                        method(multi_source, m)
                        for m in (
                            "OnBarUpdate",
                            "calculateSessionBoundaries",
                            "copyToParentScalars",
                            "copyFromParentScalars",
                            "isSessionEnabled",
                            "getSessionTimes",
                        )
                    )
                    + "\n}\n"
                )
            java = (
                "public class "
                + name
                + " {\n"
                + common
                + fields
                + "\n"
                + "\n".join(method(source, m) for m in methods)
                + "\n"
                + extra
            )
            java += "\npublic static void main(String[] args) throws Exception {\n"
            for label, data in datasets:
                for mode in (1, 2):
                    for clusters in (False, True) if name == "VP" else (False,):
                        case_id = f"{name}_{label}_{mode}_{clusters}"
                        data_literal = (
                            "new double[][]{"
                            + ",".join(
                                "{" + ",".join(repr(x) for x in row) + "}"
                                for row in data
                            )
                            + "}"
                        )
                        java += (
                            "{"
                            + name
                            + " p=new "
                            + name
                            + "(); p.chart=new Chart("
                            + data_literal
                            + ");p.mode="
                            + str(mode)
                            + ";p.clusters="
                            + str(clusters).lower()
                            + ";"
                        )
                        java += (
                            "p."
                            + methods[0]
                            + '();System.out.print("'
                            + case_id
                            + '");'
                        )
                        for key, field in outputs.items():
                            java += (
                                'System.out.print(" ' + key + '="+p.' + field + ");"
                                if not field.startswith("(")
                                else 'System.out.print(" '
                                + key
                                + '="+(p.'
                                + field[1:]
                                + ");"
                            )
                        java += "System.out.println();}\n"
                        captures.append(
                            {
                                "id": case_id,
                                "kind": name,
                                "data": data,
                                "bin_size_mode": mode,
                                "enable_vcp": clusters,
                                "expected": {},
                            }
                        )
            # Replay actual donor OnBarUpdate over gaps, weekends, year/month
            # boundaries, intrabar reversals and insufficient-history states.
            replay = [row.copy() for row in datasets[0][1][:20]]
            dates = [
                "2024-01-01T00:00",
                "2024-01-01T08:00",
                "2024-01-01T08:30",
                "2024-01-01T13:30",
                "2024-01-01T14:00",
                "2024-01-01T16:00",
                "2024-01-01T21:00",
                "2024-01-02T00:00",
                "2024-01-02T06:00",
                "2024-01-02T08:00",
                "2024-01-05T12:00",
                "2024-01-07T00:00",
                "2024-01-07T01:00",
                "2024-01-08T00:00",
                "2024-02-01T00:00",
                "2024-02-29T12:00",
                "2024-03-01T00:00",
                "2024-12-31T12:00",
                "2025-01-01T00:00",
                "2025-01-01T12:00",
            ]
            for row, date in zip(replay, dates, strict=True):
                if date == "2024-01-01T14:00":
                    # Force a confirmed reversal even with the 50-tick setting.
                    row[1:5] = [price + 100 for price in row[1:5]]
                row[0] = float(
                    datetime.fromisoformat(date).replace(tzinfo=UTC).timestamp() * 1000
                )
            literal = (
                "new double[][]{"
                + ",".join("{" + ",".join(repr(x) for x in row) + "}" for row in replay)
                + "}"
            )
            java += "double[][] replay=" + literal + ";\n"
            for selection in range(1, 11 if name == "VP" else 9):
                for pivot_method in (1, 2, 3) if selection >= 9 else (1,):
                    case_id = f"{name}_session_{selection}_pivot_{pivot_method}"
                    sessions.append(
                        {
                            "id": case_id,
                            "kind": name,
                            "session_type": selection,
                            "pivot_method": pivot_method,
                            "data": replay,
                            "expected": [],
                        }
                    )
                    java += (
                        "{"
                        + name
                        + " p=new "
                        + name
                        + "();p.chart=new Chart(replay);p.Chart=p.chart;p.SessionType="
                        + str(selection)
                        + ";p.pivotMethod="
                        + str(pivot_method)
                        + ";p.prevSessionStart=0;p.prevSessionEnd=0;"
                    )
                    java += (
                        'for(int cursor=0;cursor<replay.length;cursor++){p.chart.cursor=cursor;p.CurrentBar=cursor;p.OnBarUpdate();System.out.print("'
                        + case_id
                        + '");'
                    )
                    for key, field in outputs.items():
                        expression = (
                            "p." + field
                            if not field.startswith("(")
                            else "(p." + field[1:]
                        )
                        java += 'System.out.print(" ' + key + '="+' + expression + ");"
                    java += "System.out.println();}}\n"
            if name == "VP":
                output_fields = list(
                    re.findall(r"public DataSeries (\w+);", multi_source)
                )
                standard_names = list(outputs)
                named_keys = [
                    f"{session}_{key}"
                    for session in ("london", "new_york", "sydney", "tokyo")
                    for key in ("poc", "vah", "val")
                ]
                for actual in (False, True):
                    for mask in (15, 2, 0):
                        case_id = f"VP_multi_{actual}_{mask}"
                        flags = {
                            "enable_" + session: bool(mask & (1 << index))
                            for index, session in enumerate(
                                ("london", "new_york", "sydney", "tokyo")
                            )
                        }
                        sessions.append(
                            {
                                "id": case_id,
                                "kind": "VP",
                                "session_type": 1,
                                "pivot_method": 1,
                                "configuration": dict(
                                    profile_mode="multi",
                                    session_mode=2 if actual else 1,
                                    **flags,
                                ),
                                "data": replay,
                                "expected": [],
                            }
                        )
                        java += (
                            "{Multi p=new Multi();p.chart=new Chart(replay);p.Chart=p.chart;p.SessionMode="
                            + str(2 if actual else 1)
                            + ";"
                        )
                        for index, label in enumerate(
                            ("London", "NewYork", "Sydney", "Tokyo")
                        ):
                            java += (
                                "p.Enable"
                                + label
                                + "="
                                + str(bool(mask & (1 << index))).lower()
                                + ";"
                            )
                        java += (
                            'for(int cursor=0;cursor<replay.length;cursor++){p.chart.cursor=cursor;p.CurrentBar=cursor;p.OnBarUpdate();System.out.print("'
                            + case_id
                            + '");'
                        )
                        for key, field in zip(
                            standard_names + named_keys, output_fields, strict=True
                        ):
                            java += (
                                'System.out.print(" '
                                + key
                                + '="+p.'
                                + field
                                + ".value);"
                            )
                        java += "System.out.println();}}\n"
            for start, end in ((480, 960), (1260, 360)):
                for actual in (False, True):
                    case_id = f"{name}_custom_{start}_{end}_{actual}"
                    settings = (
                        {
                            "profile_mode": "custom",
                            "session_mode": 2 if actual else 1,
                            "session_start": start,
                            "session_end": end,
                        }
                        if name == "VP"
                        else {
                            "use_custom_hours": True,
                            "session_start": start,
                            "session_end": end,
                        }
                    )
                    sessions.append(
                        {
                            "id": case_id,
                            "kind": name,
                            "session_type": 5 if actual else 1,
                            "pivot_method": 1,
                            "configuration": settings,
                            "data": replay,
                            "expected": [],
                        }
                    )
                    java += (
                        "{"
                        + name
                        + " p=new "
                        + ("Custom" if name == "VP" else name)
                        + "();p.chart=new Chart(replay);p.Chart=p.chart;p.prevSessionStart=0;p.prevSessionEnd=0;"
                    )
                    if name == "VP":
                        java += (
                            "((Custom)p).SessionMode="
                            + str(2 if actual else 1)
                            + ";((Custom)p).SessionStartHours="
                            + str(start // 60)
                            + ";((Custom)p).SessionStartMinutes="
                            + str(start % 60)
                            + ";((Custom)p).SessionEndHours="
                            + str(end // 60)
                            + ";((Custom)p).SessionEndMinutes="
                            + str(end % 60)
                            + ";"
                        )
                    else:
                        java += (
                            "p.UseCustomHours=true;p.SessionType="
                            + str(5 if actual else 1)
                            + ";p.StartHour="
                            + str(start // 60)
                            + ";p.StartMinute="
                            + str(start % 60)
                            + ";p.EndHour="
                            + str(end // 60)
                            + ";p.EndMinute="
                            + str(end % 60)
                            + ";"
                        )
                    java += (
                        'for(int cursor=0;cursor<replay.length;cursor++){p.chart.cursor=cursor;p.CurrentBar=cursor;p.OnBarUpdate();System.out.print("'
                        + case_id
                        + '");'
                    )
                    for key, field in outputs.items():
                        expression = (
                            "p." + field
                            if not field.startswith("(")
                            else "(p." + field[1:]
                        )
                        java += 'System.out.print(" ' + key + '="+' + expression + ");"
                    java += "System.out.println();}}\n"
            java += "}\n}"
            (directory / f"{name}.java").write_text(java)
            subprocess.run(
                ["javac", str(directory / f"{name}.java")], check=True, text=True
            )
            run = subprocess.run(
                ["java", "-cp", str(directory), name],
                check=True,
                capture_output=True,
                text=True,
            )
            for line in run.stdout.splitlines():
                case_id, *values = line.split()
                expected = {
                    key: float(value)
                    for key, value in (item.split("=") for item in values)
                }
                if (
                    "_session_" in case_id
                    or "_custom_" in case_id
                    or "_multi_" in case_id
                ):
                    next(row for row in sessions if row["id"] == case_id)[
                        "expected"
                    ].append(expected)
                else:
                    next(row for row in captures if row["id"] == case_id)[
                        "expected"
                    ] = expected
    datasets_by_hash = {}
    for case in captures + sessions:
        data = case.pop("data")
        identifier = hashlib.sha256(json.dumps(data).encode()).hexdigest()[:16]
        datasets_by_hash[identifier] = data
        case["dataset"] = identifier
    artifact = {
        "sources": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                internal / "VolumeProfileIndicatorChart.java",
                internal / "TPOProfileIndicatorChart.java",
                vp_block,
                tpo_block,
                custom_block,
                multi_block,
            )
        },
        "protocol": "Unmodified donor numerical and session method bodies with chart/configuration/UTC-calendar stubs. Core session: 2024-01-01. Replays span 2024-2025. Tick .25; rows 10; VA 70%; IB and TPO brackets follow session type; LVN on; VCP sigma 1.5, two centres. Multi-session delta contamination is an explicitly corrected deviation.",
        "datasets": datasets_by_hash,
        "cases": captures,
        "sessions": sessions,
    }
    # One case per line keeps fixture diffs bounded without duplicating inputs.
    sections = []
    for key, value in artifact.items():
        if isinstance(value, list):
            body = ",\n".join(
                "    " + json.dumps(row, separators=(",", ":")) for row in value
            )
            sections.append(f'  "{key}": [\n{body}\n  ]')
        else:
            sections.append(f'  "{key}": ' + json.dumps(value, separators=(",", ":")))
    (ROOT / "docs/dev/fixtures/profile-donor-reference.json").write_text(
        "{\n" + ",\n".join(sections) + "\n}\n"
    )
    print(f"Captured {len(captures)} core cases and {len(sessions)} session replays")


if __name__ == "__main__":
    main()
