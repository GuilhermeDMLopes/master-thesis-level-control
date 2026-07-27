# Gateway DAC Boundary Limiter Runtime Validation

## Objective

Validate that the gateway limits every DAC value actually written to the PLC or simulator to a maximum absolute change of 150 units.

This protection is complementary to the SAFE_DAC_RATE_LIMITER function block running in FORTE.

## Source Version

```text
Branch: feature/safe-dac-rate-limiter
Base commit: 5d39f59e586bfada8ca1bb8f034ae46bc6f457a5
Run ID: 20260727-141105
```

## Architecture

```text
PI_LEVEL_CONTROLLER
    -> SAFE_DAC_RATE_LIMITER in FORTE
    -> OPC UA requested DAC
    -> gateway DAC write-boundary limiter
    -> simulated B&R PLC
    -> DAC feedback
```

## Configuration

```text
DAC boundary maximum delta: 150
DAC minimum: 0
DAC maximum: 32000
Gateway cycle: approximately 100 ms
```

## Automated Tests

```text
Gateway-specific tests: 53 passed
Complete test suite: 126 passed
```

## Runtime Results

```text
Actual DAC writes: 550
First positive applied DAC: 150
Maximum actual write delta: 150
Maximum logged write delta: 150
Maximum requested-applied gap: 300
Actual write-rate violations: 0
Logged-delta mismatches: 0
Limited-flag mismatches: 0
```

The gateway accepted requested DAC changes larger than 150 units but limited every value actually written to the simulated PLC to a maximum change of 150 units.

Command and feedback remained coherent during the validation.

## CSV Sampling Note

Consecutive CSV rows are periodic samples and do not necessarily represent consecutive PLC writes.

A difference of 300 between consecutive CSV samples can therefore contain an intermediate write that was not captured by the CSV sampling cycle.

The write-rate guarantee must be evaluated using the gateway log entries containing:

```text
Written to B&R PLC: DAC requested=..., applied=..., delta=..., limited=...
```

## Analyzer Output

```text
Run ID: 20260727-141105
Gateway log encoding: utf-16
Actual DAC writes: 550

First actual gateway DAC writes:
index | requested | applied | observed_delta | logged_delta | limited
    0 |       300 |     150 |            150 |          150 | True   
    1 |       300 |     300 |            150 |          150 | False  
    2 |       600 |     450 |            150 |          150 | True   
    3 |       600 |     600 |            150 |          150 | False  
    4 |       900 |     750 |            150 |          150 | True   
    5 |      1200 |     900 |            150 |          150 | True   
    6 |      1200 |    1050 |            150 |          150 | True   
    7 |      1500 |    1200 |            150 |          150 | True   
    8 |      1500 |    1350 |            150 |          150 | True   
    9 |      1500 |    1500 |            150 |          150 | False  
   10 |      1800 |    1650 |            150 |          150 | True   
   11 |      1800 |    1800 |            150 |          150 | False  
   12 |      1950 |    1950 |            150 |          150 | False  
   13 |      2100 |    2100 |            150 |          150 | False  
   14 |      2400 |    2250 |            150 |          150 | True   
   15 |      2550 |    2400 |            150 |          150 | True   
   16 |      2550 |    2550 |            150 |          150 | False  
   17 |      2700 |    2700 |            150 |          150 | False  
   18 |      3150 |    2850 |            150 |          150 | True   
   19 |      3150 |    3000 |            150 |          150 | True   
   20 |      3450 |    3150 |            150 |          150 | True   
   21 |      3450 |    3300 |            150 |          150 | True   
   22 |      3600 |    3450 |            150 |          150 | True   
   23 |      3750 |    3600 |            150 |          150 | True   
   24 |      3750 |    3750 |            150 |          150 | False  
   25 |      4050 |    3900 |            150 |          150 | True   
   26 |      4050 |    4050 |            150 |          150 | False  
   27 |      4350 |    4200 |            150 |          150 | True   
   28 |      4650 |    4350 |            150 |          150 | True   
   29 |      4650 |    4500 |            150 |          150 | True   
   30 |      4950 |    4650 |            150 |          150 | True   
   31 |      4950 |    4800 |            150 |          150 | True   
   32 |      5250 |    4950 |            150 |          150 | True   
   33 |      5250 |    5100 |            150 |          150 | True   
   34 |      5550 |    5250 |            150 |          150 | True   
   35 |      5550 |    5400 |            150 |          150 | True   
   36 |      5850 |    5550 |            150 |          150 | True   
   37 |      6000 |    5700 |            150 |          150 | True   
   38 |      6150 |    5850 |            150 |          150 | True   
   39 |      6150 |    6000 |            150 |          150 | True   
   40 |      6150 |    6150 |            150 |          150 | False  
   41 |      6450 |    6300 |            150 |          150 | True   
   42 |      6750 |    6450 |            150 |          150 | True   
   43 |      6750 |    6600 |            150 |          150 | True   
   44 |      6900 |    6750 |            150 |          150 | True   
   45 |      7050 |    6900 |            150 |          150 | True   
   46 |      7050 |    7050 |            150 |          150 | False  
   47 |      7500 |    7200 |            150 |          150 | True   
   48 |      7500 |    7350 |            150 |          150 | True   
   49 |      7800 |    7500 |            150 |          150 | True   

First positive applied DAC: 150
Maximum actual write delta: 150
Maximum logged write delta: 150
Maximum requested-applied gap: 300
Actual write-rate violations: 0
Logged-delta mismatches: 0
Limited-flag mismatches: 0

First actual write valid: True
Actual write rate valid: True
Logged delta valid: True
Limited flag valid: True
Boundary limiter exercised: True

Gateway actual-write validation: PASSED
```

## Conclusion

The gateway DAC write-boundary limiter passed the runtime validation.

The following requirements were satisfied:

- deterministic first applied DAC of 150;
- maximum absolute change of 150 between actual PLC writes;
- no write-rate violations;
- internal logged deltas consistent with observed writes;
- diagnostic limited flags consistent with requested and applied values;
- requested DAC preserved separately from applied DAC;
- applied DAC and PLC feedback remained coherent.

The gateway boundary protection is approved for the next offline closed-loop validation stage.
