# STEM-AI B3 COI Declaration Discrimination Guide

3-tier scoring for Conflict of Interest disclosure (PATCH-22).
Apply the highest applicable tier. Do not assign non-standard values.

---

## +0 (Absent)

No organizational affiliation, funding, or COI information anywhere
in README, CHANGELOG, or LICENSE.

## +3 (Institutional affiliation disclosed)

- "Developed at Stanford SNAP" -- org name present
- "Affiliated with MIT CSAIL" -- lab affiliation
- "Contributors from Heidelberg Institute for Theoretical Studies"

NOTE: affiliation disclosure != COI declaration.
Knowing who built it is not the same as knowing who funded it or profits from it.

## +5 (Funding disclosed)

- "Funded by NIH R01 GM123456"
- "Supported by Wellcome Trust grant 208986/Z/17/Z"
- "This work was funded by DARPA under contract HR0011-20-C-0023"

## +5 (Commercial COI declared)

- "Authors hold equity in BioStartup Inc."
- "Author X is a paid consultant for PharmaCo"
- "Developed in collaboration with [commercial entity] under sponsored research agreement"

---

## Boundary Cases

- "MIT License" = licensing clarity, NOT COI. Score B3 = +0.
- "Stanford SNAP affiliation + MIT License" = +3 (affiliation only)
- "K-Dense Inc. affiliation stated" = +3 (corporate affiliation, no funding detail)
- "K-Dense Inc. + funding model described" = +5

Maximum: +5 (non-cumulative -- highest applicable tier).
Valid scores: 0, 3, or 5 only.
