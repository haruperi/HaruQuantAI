# Stage 01 donor RNG vectors

`vectors.jsonl` is stdout from `DonorRandomVectors.java`, executing the recovered
donor classes directly. No Python RNG contributes expected values. Six seeds,
11 operations, and 640 draws per operation exercise 42,240 outputs and multiple
MT state transitions. Integer and ordinary double outputs compare exactly;
Gaussian outputs allow absolute/relative tolerance `1e-14` for libm/StrictMath.

From the repository root, PowerShell (Java 26.0.2.1 used for this capture):

```powershell
$donorVectorBuild = Join-Path $env:TEMP ('haru-donor-rng-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $donorVectorBuild | Out-Null
javac -d $donorVectorBuild data/reference-donor/internal/libs/lib/random/MersenneTwisterFast.java data/reference-donor/internal/libs/lib/random/MTRandom.java tests/core/lib/fixtures/stage01_random/DonorRandomVectors.java
if ($LASTEXITCODE -ne 0) { throw 'Donor compilation failed' }
java -cp $donorVectorBuild DonorRandomVectors | Set-Content -Encoding utf8 tests/core/lib/fixtures/stage01_random/vectors.jsonl
uv run pytest tests/core/lib/test_random.py tests/core/lib/test_random_generation.py --no-cov -q
```

The compiler emits an informational `strictfp` warning on modern Java.
The harness uses wrapper expressions from `MersenneTwisterRng.java` for boolean,
probability, stepped and range selection. Exactly representable half steps avoid
conflating sequence verification with decimal rounding. Rounding and invalid
bounds have separate source-derived tests. The harness does not execute the full
SQX application, nor certify strategy-generation parity.

SHA-256 source fingerprints at capture:

- `MersenneTwisterFast.java`: `9F63F4E34C90F4457E359723BF99B1135CB6BB14413C1BFDF161361BF1679B8B`
- `MTRandom.java`: `CE3CDA9949A62C23DD80FA8B50AE2B2B8E4140D6D3F937F719409027C650DF93`
- `vectors.jsonl`: `6A5BD4BBF999F45CBCA53681FAD8B870722F5EF99007674B2843DEC18BA178D3`
