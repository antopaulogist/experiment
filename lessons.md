# Lessons

- Define an honest number before debating improvements.
- Check the judge against human judgments and a known-bad output first.
- Separate development cases from held-back scoring cases; repeated aggregate feedback can still overfit.
- Guard costly error types explicitly: a better total can hide a harmful tradeoff.
- Record failed attempts with their hypotheses so later attempts do not repeat them blindly.
- Test a rule on the raw input it will receive, not only on already transformed output.
- Give each working copy its own build cache to avoid scoring stale artifacts.
- Check whether a guard understands legitimate transformations before trusting its verdict.
- Order-swapped comparisons expose position bias; subtle differences need more evidence.
- Try deleting existing rules as well as adding new ones.
- Frozen tests preserve existing behaviour, including behaviour that may deserve reconsideration.
