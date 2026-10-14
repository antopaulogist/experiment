# <Experiment name>

## Goal
What we want to be true when this is done, in one or two sentences, with no solution in it.

## The number
What the loop optimises: one command that prints one number on its last line. Say whether lower or higher is better, and what the number means in plain words.
If no honest number exists, say how the judge decides instead (teacher reference + `scripts/text_distance.py`, or blind A-or-B with `scripts/pairwise.py`), and how the judge was checked against a person.

## Data
Where the cases come from, how many, and the held-out split the loop never sees while choosing changes. Real, natural data beats made-up data.

## What may change
The files the attempts may edit.

## What must not break
The guards: tests, behaviours or outputs that must stay true whatever the score does. A change that breaks a guard is binned however good its number.

## Ideas worth trying
Optional starting directions. The attempts are free to go elsewhere.

## Done when
The stop rule: a target number, a plateau (N binned attempts in a row), or a time or cost budget.
