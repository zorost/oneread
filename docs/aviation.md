# Aviation pack

STE was requested by European airlines in the late 1970s so aircraft
maintenance documentation could be read by technicians with a basic command of
English. AECMA Simplified English shipped in 1986. It became an international
specification in 2005 and an international standard in 2025: ASD-STE100
Issue 9, 15 January 2025. Source: [asd-ste100.org](https://www.asd-ste100.org/).

OneRead does not write your AMM. It gives you:

- Rule 7 signal words mapped onto software and onto hardware
- an `amm` emitter that forces WARNING / CAUTION / NOTE / PROCEDURE / RESULT
- the "repeat Do not in each prohibited item" rule
- a fixture pair in `fixtures/slop/aviation.md` and `fixtures/compiled/aviation.md`

## Signal words

| Label | Use when | Sentence limit | Command? |
|---|---|---|---|
| WARNING | injury or death | 20 | Yes |
| CAUTION | damage to equipment or data | 20 | Yes |
| NOTE | information only | 25 | No |
| DANGER | only if the governing safety standard defines it | 20 | Yes |

Order: signal word, then command or condition, then the risk.

## AeroFarr

OneRead is a language compiler. It does not predict delay, explain a
disruption, or retrieve a safety report. That product is
[AeroFarr](https://aerofarr.com), Zorost's aviation intelligence platform:
calibrated pre-departure disruption forecasts, causal explanation, network
cascade, and retrieval over public aviation safety corpora, with citations.
The two meet where a procedure has to be readable and the operation around it
has to be predicted. They are not the same system.
