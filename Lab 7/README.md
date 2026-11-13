# L6_L7_06 — Event Ticket Tier

Lab 7: Fuzz Testing with Hypothesis

## About

A set of property-based fuzz tests targeting promotional voucher codes, tiered seat row calculations, and attendee badge CSV strings to expose unhandled edge cases.

## Files

| File | Description |
|------|-------------|
| `processor.py` | The module under test (buggy starter code) |
| `test_processor.py` | Starter test file to complete using Hypothesis |

Keep all your Lab 7 work in this `LAB7` folder.

Refer to the lab handout for instructions.

## Lab 7 Submission — P T Mounika (PES1UG24CS311)

| File | Description |
|------|-------------|
| `processor.py` | **Fixed** module — validates type, length, field count, numbers and ranges; returns `Invalid ...` messages instead of crashing |
| `test_processor.py` | **Completed** Hypothesis fuzz tests (3 no-crash fuzz tests + 3 valid-input property tests) |
| `Lab7_FuzzTesting_Report_PES1UG24CS311.pdf` | Report with screenshots of every step |
| `screenshots/` | Step-wise output screenshots |

Run:
```
pip install hypothesis pytest
python processor.py
python -m pytest test_processor.py -v
```
Result: Hypothesis found 14 input-validation bugs in the original code (3 tests failed); after the fix all 6 tests pass.
