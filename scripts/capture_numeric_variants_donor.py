"""Capture numeric variant references by executing the donor's Java sources.

Only the framework/chart/calendar shell is stubbed; calculator source bodies and
indicator methods are compiled directly. SQUtils.round is supplied as Math.round
at eight decimal places, so this harness does not certify proprietary utility
rounding at binary/decimal halfway boundaries.
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

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = (
    "BarRange/BarRange",
    "BarRange/BiggestRange",
    "BarRange/SmallestRange",
    "BarRange/HighestInRange",
    "BarRange/LowestInRange",
    "BollingerBands/BBRange",
    "BollingerBands/BBWidthRatio",
    "HighestLowest/Highest",
    "HighestLowest/Lowest",
    "HighestLowest/HighestIndex",
    "HighestLowest/LowestIndex",
)


def declaration(source: str) -> str:
    """Keep each class body and its methods; remove framework annotations."""
    start = re.search(r"public (?:abstract )?class \w+", source)
    if start is None:
        raise ValueError("Missing Java class declaration")
    body = source[start.start() :]
    body = re.sub(r"@\w+(?:\([^\n]*\))?", "", body)
    return body.replace("public class ", "static class ", 1).replace(
        "public abstract class ", "static abstract class ", 1
    )


# Keep generated Java configuration next to its matching reference case.
def main() -> None:  # noqa: PLR0912
    """Compile unchanged donor algorithms and capture complete output histories."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--donor", type=Path, default=Path(r"C:\SQX-145\internal\extend\Snippets\SQ")
    )
    args = parser.parse_args()
    sources = {}
    classes = []
    for name in (
        "AbstractCalculator",
        "AverageCalculator",
        "StdDevCalculator",
        "HighestCalculator",
        "LowestCalculator",
    ):
        path = args.donor / f"Calculators/{name}.java"
        source = path.read_text()
        sources[str(path.relative_to(args.donor)).replace("\\", "/")] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        classes.append(declaration(source))
    for name in BLOCKS:
        path = args.donor / f"Blocks/Indicators/{name}.java"
        sources[str(path.relative_to(args.donor)).replace("\\", "/")] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        classes.append(declaration(path.read_text()))
    shell = r"""
    static class TradingException extends Exception {TradingException(String s){super(s);}}
    static class Logger {void debug(String s){}}
    static class LoggerFactory {static Logger getLogger(String s){return new Logger();}}
    static class Debugger {}
    static class SQUtils {static double round(double x,int digits){double scale=Math.pow(10,digits);return Math.round(x*scale)/scale;}}
    static class SQTime {static long correctDayStart(long t){return Math.floorDiv(t,86400000L)*86400000L;}}
    static double[][] rows;static int cursor;
    static class DataSeries {
        int column=-1;double value;
        DataSeries(){} DataSeries(int c){column=c;}
        double get(int lag){return cursor-lag>=0?rows[cursor-lag][column]:Double.NaN;}
        void set(double v){value=v;} void set(int lag,double v){value=v;}
    }
    static class PriceSeries extends DataSeries {
        int selector;PriceSeries(int s){selector=s;}
        double get(int lag){if(cursor-lag<0)return Double.NaN;double[] r=rows[cursor-lag];
            switch(selector){case 0:return r[4];case 1:return r[1];case 2:return r[2];case 3:return r[3];
            case 4:return (r[2]+r[3])/2;case 5:return (r[2]+r[3]+r[4])/3;default:return (r[2]+r[3]+2*r[4])/4;}}
    }
    static class ChartData {
        DataSeries High=new DataSeries(2),Low=new DataSeries(3);
        double High(int lag){return High.get(lag);} double Low(int lag){return Low.get(lag);}
        long Time(int lag){return (long)rows[cursor-lag][0];}
        DataSeries getSeries(int selector){return new PriceSeries(selector);}
    }
    static class IndicatorBlock {
        int CurrentBar=0,Shift=0;
        int getCurrentBar(){return CurrentBar;}
        protected void OnInit() throws TradingException {}
        protected void OnBarUpdate() throws TradingException {}
    }
    """
    datasets = {
        "mixed": [
            [1704099600000.0, 10.0, 12.123456789, 9.0, 11.0],
            [1704101400000.0, 11.0, 14.0, 10.0, 13.0],
            [1704103200000.0, 13.0, 14.0, 11.0, 12.0],
            [1704106800000.0, 12.0, 14.0, 11.0, 13.0],
            [1704186000000.0, 13.0, 13.0, 12.0, 12.5],
            [1704193200000.0, 12.0, 16.0, 10.0, 14.0],
            [1704272400000.0, 14.0, 15.0, 14.0, 14.5],
            [1704531600000.0, 14.0, 17.0, 12.0, 16.0],
        ],
        "wide": [
            [
                1704099600000.0 + i * 1800000,
                100_000_000.0,
                200_000_000.0,
                0.0,
                100_000_000.0,
            ]
            for i in range(8)
        ],
        "flat": [[1704099600000.0 + i * 1800000, 4.0, 4.0, 4.0, 4.0] for i in range(8)],
        "negative": [
            [1704099600000.0 + i * 1800000, -3.0, -1.0, -5.0, (-2.0 if i % 2 else 0.0)]
            for i in range(8)
        ],
        "overnight": [
            [
                float(datetime.fromisoformat(t).replace(tzinfo=UTC).timestamp() * 1000),
                10.0,
                12.0 + i,
                8.0 - i,
                10.0 + i / 10,
            ]
            for i, t in enumerate(
                (
                    "2024-01-01T20:00",
                    "2024-01-01T21:00",
                    "2024-01-01T23:00",
                    "2024-01-02T01:00",
                    "2024-01-02T06:00",
                    "2024-01-02T21:00",
                    "2024-01-03T06:00",
                )
            )
        ],
    }
    cases = []
    body = []
    for dataset, data in datasets.items():
        literal = (
            "new double[][]{"
            + ",".join(
                "{" + ",".join(repr(float(x)) for x in row) + "}" for row in data
            )
            + "}"
        )
        body.append("rows=" + literal + ";")
        for path in BLOCKS:
            name = path.split("/")[-1]
            for period in (1, 3, 14):
                if name.endswith("InRange") and period != 3:
                    continue
                selectors = range(7) if name in ("BBRange", "BBWidthRatio") else (0,)
                if name in ("BBRange", "BBWidthRatio") and period == 1:
                    continue
                for selector in selectors:
                    case_id = f"{name}_{dataset}_{period}_{selector}"
                    settings = {}
                    code = (
                        "{" + name + " p=new " + name + "();p.Value=new DataSeries();"
                    )
                    if name in (
                        "BarRange",
                        "BiggestRange",
                        "SmallestRange",
                        "HighestInRange",
                        "LowestInRange",
                    ):
                        code += (
                            "p.Chart" if name == "BarRange" else "p.Input"
                        ) + "=new ChartData();"
                    elif name in ("BBRange", "BBWidthRatio"):
                        code += (
                            ("p.Chart" if name == "BBRange" else "p.Input")
                            + "=new ChartData();p.ComputedFrom="
                            + str(selector)
                            + ";p.Deviation=2.;"
                        )
                        settings.update(computed_from=selector, deviation=2.0)
                    else:
                        column = 3 if name.startswith("Lowest") else 2
                        code += "p.Input=new DataSeries(" + str(column) + ");"
                    if name.endswith("InRange"):
                        start, end = (
                            (2100, 600) if dataset == "overnight" else (900, 1100)
                        )
                        code += (
                            "p.TimeFrom=" + str(start) + ";p.TimeTo=" + str(end) + ";"
                        )
                        settings.update(
                            time_from=start, time_to=end, timestamp_unit="milliseconds"
                        )
                    elif name != "BarRange":
                        code += "p.Period=" + str(period) + ";"
                        settings["period"] = period
                    code += (
                        'p.OnInit();System.out.print("'
                        + case_id
                        + '");for(cursor=0;cursor<rows.length;cursor++){p.CurrentBar=cursor;p.OnBarUpdate();System.out.print(" "+p.Value.value);}System.out.println();}'
                    )
                    body.append(code)
                    cases.append(
                        {
                            "id": case_id,
                            "block": path,
                            "dataset": dataset,
                            "parameters": settings,
                            "expected": [],
                        }
                    )
    java = (
        "public class NumericDonor {\n"
        + shell
        + "\n"
        + "\n".join(classes)
        + "\npublic static void main(String[] args) throws Exception {\n"
        + "\n".join(body)
        + "\n}}"
    )
    with tempfile.TemporaryDirectory(prefix="numeric-donor-") as temporary:
        directory = Path(temporary)
        path = directory / "NumericDonor.java"
        path.write_text(java)
        subprocess.run(["javac", str(path)], check=True)
        run = subprocess.run(
            ["java", "-cp", str(directory), "NumericDonor"],
            check=True,
            capture_output=True,
            text=True,
        )
    by_id = {row["id"]: row for row in cases}
    for line in run.stdout.splitlines():
        key, *values = line.split()
        by_id[key]["expected"] = [float(x) for x in values]
    artifact = {
        "sources": sources,
        "protocol": __doc__,
        "datasets": datasets,
        "cases": cases,
    }
    (ROOT / "docs/dev/fixtures/numeric-variants-donor-reference.json").write_text(
        json.dumps(artifact, indent=2, allow_nan=False) + "\n"
    )
    print(f"Captured {len(cases)} source-executed numeric cases")


if __name__ == "__main__":
    main()
