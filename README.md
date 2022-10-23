Predictions Utilities
=====================

CapSteel

Setup
-----

Requires Python 3.6+.

Getting Started
---------------

1)  Download your responses csv files from Google Drive. Massage any inconsistencies in data by hand (you might
    not notice these until you start seeing errors in step 3).

2)  Create your match outcome files.

    ```bash
    python3 predictions.py matches --responses day1_responses.csv --matches day1_matches.csv
    ```

    This example asks for the outcomes of all matches in day1_responses.csv, then saves the
    match outcomes to day1_matches.csv

3)  Create your day scores files.

    ```bash
    python3 predictions.py scores --responses day1_responses.csv --matches day1_matches.csv --scores day1_scores.csv
    ```

    This example compares participants' responses in day1_responses.csv to the outcomes recorded in day1_matches.csv, then saves the computed scores to day1_scores.csv

4)  Create your total scores file.

    ```bash
    python3 predictions.py totals --scores day1_scores.csv day2_scores.csv --total total_scores.csv
    ```

    This example adds up scores recorded in day1_scores.csv and day2_scores.csv, then saves the computed total scores to total_scores.csv

Useful scripts
--------------

Re-generate all scores output

```bash
x=8
for i in `seq ${x}`; do python3 predictions.py scores --responses in/day${i}_responses.csv --matches in/day${i}_matches.csv --scores out/day${i}_scores.csv > out/day${i}_scores.txt; done
python3 predictions.py totals --scores $(for i in `seq ${x}`; do echo out/day${i}_scores.csv; done) --total out/day${x}_totals.csv > out/day${x}_totals.txt
```