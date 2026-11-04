import com.strategyquant.lib.random.MersenneTwisterFast;
import com.strategyquant.lib.random.MTRandom;
import java.util.StringJoiner;

/** Execute recovered donor classes, without reimplementing their PRNG algorithms. */
public class DonorRandomVectors {
    public static void main(String[] args) {
        for (long seed : new long[]{0, 42, -1, 4294967296L, Long.MIN_VALUE, Long.MAX_VALUE}) {
            for (String op : new String[]{"double", "int", "power", "reject", "long", "gaussian", "bool", "probability", "stepped", "range", "secondary"}) {
                MersenneTwisterFast fast = new MersenneTwisterFast(seed);
                MTRandom secondary = new MTRandom(seed);
                StringJoiner values = new StringJoiner(",", "[", "]");
                for (int i = 0; i < 640; i++) {
                    // Wrapper formulas below are from MersenneTwisterRng.java.
                    switch (op) {
                        case "double": values.add(Double.toString(fast.nextDouble())); break;
                        case "int": values.add(Integer.toString(fast.nextInt(37))); break;
                        case "power": values.add(Integer.toString(fast.nextInt(1024))); break;
                        case "reject": values.add(Integer.toString(fast.nextInt(1073741825))); break;
                        case "long": values.add(Long.toString(fast.nextLong())); break;
                        case "gaussian": values.add(Double.toString(fast.nextGaussian())); break;
                        case "bool": values.add(Boolean.toString(fast.nextInt(2) == 0)); break;
                        case "probability":
                            double p = new double[]{0, -0.5, 1, 1.5, 0.5, Double.NaN}[i % 6];
                            values.add(Boolean.toString(p == 1.0 || fast.nextDouble() < p)); break;
                        case "stepped":
                            // Exactly representable steps isolate PRNG/selection from decimal rounding.
                            values.add(Double.toString(-2.0 + fast.nextInt(8) * 0.5)); break;
                        case "range": values.add(Integer.toString(-7 + fast.nextInt(8) * 3)); break;
                        case "secondary": values.add(Double.toString(secondary.nextDouble())); break;
                        default: throw new IllegalArgumentException(op);
                    }
                }
                System.out.println("{\"seed\":" + seed + ",\"op\":\"" + op + "\",\"values\":" + values + "}");
            }
        }
    }
}
