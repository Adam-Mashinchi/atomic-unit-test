---

# PROJECT NO LONGER MAINTAINED!
This project was ultimately a prototype for what ended up becoming [atomic-operator](https://github.com/swimlane/atomic-operator), which you should like use instead if you want greater functionality beyond what is provided here!

---

# Atomic Unit Test
**(aka "Atomic Confetti Bomb")**

A _very_ simple way of running [Atomic Red Team](https://github.com/redcanaryco/atomic-red-team)'s Atomic Tests using Python!

Set Up
-----

### On a Windows machine?

Simply double click the `setup_on_windows.bat` (or `setup_on_windows_then_TDR.bat`) file to start!

### DIY Setup

Install required Python packages.

    (venv) $ pip install -r requirements.txt



Example Usage
-----

### Target a directory of YAML files, and see their output

```
python atomic-unit-test.py --atomics atomic_tests/TDR_2021 --verbose
```

### Run Tests, but use an external file for their `input_arguments`, and _only_ use Tests in that file

```
python atomic-unit-test.py --atomics atomic_tests/examples --config atomic_tests/examples/example.yaml.conf --only
```
