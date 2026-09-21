# How the anomaly detector works, and why

This explains the choices behind the detector in Step 4 of the notebook — in particular why it
compares each reading against only the **30 readings before it** rather than against the whole
dataset.

## The calculation, with real numbers

Here is the single largest deviation in our data: axis 2, reading 13,334, at 09:54:06 on 18 October.

**Step 1 — take the 30 readings immediately before it** (amps):

```text
 8.75  22.25  11.44   0.74  11.23  27.94   1.27  11.44   8.22  11.33
11.49  27.99   7.96   7.43   4.27   4.01   4.06   4.01   7.17   7.38
11.07  11.23  23.25   1.53  18.66   4.85  11.33   1.90  11.12  11.39
```

**Step 2 — the baseline.** Add them up and divide by 30:

```text
306.695 ÷ 30 = 10.223 A
```

This is what the joint has been drawing lately.

**Step 3 — the standard deviation.** This measures how much those 30 readings wobble around the
baseline. Some are 0.74A, some are 27.99A, so the spread is wide:

```text
standard deviation = 7.330 A
```

Read it as "a typical reading sits about 7.3A away from the baseline". A small value means a steady
joint; a large one means an erratic joint.

**Step 4 — the deviation.** How far the new reading sits from the baseline:

```text
51.239 − 10.223 = 41.016 A
```

**Step 5 — the z-score.** The deviation expressed in units of standard deviation:

```text
41.016 ÷ 7.330 = 5.60
```

The reading sits 5.6 typical wobbles above where the joint had been running. Anything past 3 is
flagged, so this one is.

## Why the standard deviation is in there at all

It is what makes the test fair across joints. A 4A jump is enormous on axis 8, which normally draws
0.3A and barely varies. The same 4A on axis 2, which averages 10A and swings between 0.7A and 28A,
is an ordinary Tuesday. Dividing by the spread asks "is this surprising *for this joint*" rather
than "is this a big number".

## Why 30 readings and not the whole dataset

This is the important choice, and it is easy to get wrong. We tested both.

**Using the whole dataset as the baseline** means comparing every reading against one fixed average
computed from all 14,185 active readings:

```text
global mean = 10.11 A      global standard deviation = 8.17 A
```

Anything above about 34.7A gets flagged, and nothing below ever does, because the bar never moves.
That approach flags 304 readings on axis 2.

**Using a rolling 30-reading window** means the baseline moves with the robot. Across the shift, the
local baseline ranges from **6.2A to 16.0A** — it more than doubles depending on what the robot is
doing at the time.

That difference matters. The rolling window flags 341 readings on axis 2, and **124 of them would be
missed entirely by a global baseline**. For example:

| Reading | Local baseline | Local z | Global z | Global verdict |
|---|---|---|---|---|
| 31.31 A | 8.42 A | 4.80 | 2.60 | normal |
| 30.94 A | 10.16 A | 3.10 | 2.55 | normal |
| 34.42 A | 8.84 A | 4.68 | 2.98 | normal |

A 31A spike while the robot had been idling along at 8.4A is a real event. A global baseline shrugs
at it, because 31A is unremarkable *on average across the whole day*.

**Three reasons the rolling window is the right choice here:**

1. **The robot does different work at different times.** It runs different programs and carries
   different loads through a shift. One average blended across all of them describes nothing the
   robot actually does.
2. **We are looking for change, not size.** The failure we care about — a torque tube wearing out —
   shows up as a joint drawing more than *it recently did*, not more than some universal threshold.
   A global baseline cannot express that question.
3. **A global baseline hides slow degradation.** If a joint gradually draws more current over
   weeks, those later readings pull the global average up with them, so the drift looks normal
   relative to an average that now includes it. A rolling window is not immune either, but it fails
   more slowly and the trend analysis is what catches that case.

**The cost of a rolling window** is that the first 30 readings of every session have no history to
compare against, so they are not scored at all. In our data that excludes 2,490 of 14,185 active
readings. We report that number rather than quietly scoring them against a half-formed baseline.

## Why the window resets after a gap

The robot stops for long stretches — our longest is 2 hours 28 minutes. Without a reset, the first
reading after a stoppage would be compared against readings from before it, which is not "recent
behaviour" in any useful sense. More than 60 seconds between readings starts a new session, and the
30-reading count starts again.

## Why 30, specifically

30 readings is roughly one minute of operation at the 2-second sampling interval — long enough for
the spread to be meaningful, short enough to still be "recent". It is a judgement call, not a
derived optimum, so the notebook publishes how sensitive the result is to it:

| Window | Threshold | Flagged share of scored readings |
|---|---|---|
| 15 | 2.5 | 35.9% |
| 15 | 3.0 | 29.5% |
| 30 | 2.5 | 28.4% |
| **30** | **3.0** | **22.4%** |
| 60 | 3.0 | 18.7% |
| 60 | 4.0 | 11.2% |

A shorter window or lower threshold flags considerably more. Quoting one number without that range
would imply a precision the method does not have.

## What this method cannot do

- **We cannot report precision or recall.** The dataset has no confirmed fault labels, so we know
  how many readings we flag but not how many were real faults.
- **A z-score assumes a roughly symmetric distribution.** Axis 2's active readings have a skewness
  of 1.69 — strongly right-skewed — so `|z| > 3` does not carry its usual meaning of about one
  reading in 370. Many flags mark the upper tail of normal operation.
- **Near-constant baselines distort the score.** Where a joint has been almost steady the spread can
  be about 0.01A, and an ordinary 1A change would score above 100. We floor the divisor at 0.1A,
  below which a difference is sensor noise rather than a real change. That floor changed the flag
  count by one, which is how we know it clipped only the pathological tail.
- **A fault that appears only as the robot not moving is invisible**, because all-zero readings are
  excluded by design.
