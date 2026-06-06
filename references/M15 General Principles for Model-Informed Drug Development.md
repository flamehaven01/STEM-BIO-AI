# M15 General Principles

# for Model-Informed

# Drug Development

## Guidance for Industry

```
U.S. Department of Health and Human Services
Food and Drug Administration
Center for Drug Evaluation and Research (CDER)
Center for Biologics Evaluation and Research (CBER)
```
```
June 2026
ICH-Multidisciplinary
```

# M15 General Principles

# for Model-Informed

# Drug Development

## Guidance for Industry

```
Additional copies are available from:
```
```
Division of Drug Information
Center for Drug Evaluation and Research
Food and Drug Administration
Phone: 855 -543-3784 or 301-796- 3400
Email: druginfo@fda.hhs.gov
https://www.fda.gov/drugs/guidance-compliance-regulatory-information/guidances-drugs
```
```
and/or
```
```
Office of Communication, Outreach, and Development
Center for Biologics Evaluation and Research
Food and Drug Administration
Phone: 800- 835 -4709 or 240-402-8010; Email: industry.biologics@fda.hhs.gov
https://www.fda.gov/vaccines-blood-biologics/guidance-compliance-regulatory-information-biologics/biologics-guidances
```
```
U.S. Department of Health and Human Services
Food and Drug Administration
Center for Drug Evaluation and Research (CDER)
Center for Biologics Evaluation and Research (CBER)
```
```
June 2026
ICH-Multidisciplinary
```

##### FOREWORD

The International Council for Harmonisation of Technical Requirements for Pharmaceuticals for
Human Use (ICH) has the mission of achieving greater regulatory harmonization worldwide to
ensure that safe, effective, and high-quality medicines are developed, registered, and maintained
in the most resource-efficient manner. By harmonizing the regulatory expectations in regions
around the world, ICH guidelines have substantially reduced duplicative clinical studies,
prevented unnecessary animal studies, standardized safety reporting and marketing application
submissions, and contributed to many other improvements in the quality of global drug
development and manufacturing and the products available to patients.

ICH is a consensus-driven process that involves technical experts from regulatory authorities and
industry parties in detailed technical and science-based harmonization work that results in the
development of ICH guidelines. The commitment to consistent adoption of these consensus-
based guidelines by regulators around the globe is critical to realizing the benefits of safe,
effective, and high-quality medicines for patients as well as for industry. As a Founding
Regulatory Member of ICH, the Food and Drug Administration (FDA) plays a major role in the
development of each of the ICH guidelines, which FDA then adopts and issues as guidance to
industry.


## TABLE OF CONTENTS

- I. INTRODUCTION (1)
   - A. Objective of the Guidance (1.1)
   - B. Background (1.2)
   - C. Scope of the Guidance (1.3)
   - D. Guidance Overview (1.4)
- II. FRAMEWORK FOR ASSESSMENT OF MIDD EVIDENCE (2)
   - A. Key Assessment Elements (2.1)
      - 1. Question of Interest (2.1.1)
      - 2. Context of Use (2.1.2)
      - 3. Model Influence (2.1.3)
      - 4. Consequence of Wrong Decision (2.1.4)
      - 5. Model Risk (2.1.5)
      - 6. Model Impact (2.1.6)........................................................................................................................
         - Decision-making (2.2) B. Additional Considerations for Interaction with Regulators and to Inform
      - 1. Technical Criteria (2.2.1)
      - 2. Appropriateness of Proposed MIDD (2.2.2)
      - 3. Evaluation of Model(s) and Model Outcomes (2.2.3)
      - 4. Outcome of the MIDD Evidence Assessment (2.2.4)
- III. MODEL EVALUATION (3)
- IV. MIDD REPORTING AND SUBMISSION (4)
   - A. Model Analysis Plan (4.1)
   - B. Model Analysis Report(4.2)
   - C. Documentation for Regulatory Interactions and Submissions (4.3)
- APPENDIX 1: TABLE FOR ASSESSMENT OF MIDD EVIDENCE
- APPENDIX 2: MODEL ANALYSIS REPORT CONTENT
- GLOSSARY.................................................................................................................................


```
M15 General Principles for Model-Informed Drug Development
Guidance for Industry^1
```
This guidance represents the current thinking of the Food and Drug Administration (FDA or Agency)
on this topic. It does not establish any rights for any person and is not binding on FDA or the public.
You can use an alternative approach if it satisfies the requirements of the applicable statutes and
regulations. To discuss an alternative approach, contact the FDA office responsible for this guidance
as listed on the title page.

##### I. INTRODUCTION (1 )^2

### A. Objective of the Guidance (1.1)

This guidance provides general recommendations for planning, model evaluation, and
documentation of evidence derived from model-informed drug development (MIDD),
hereafter referred to as _MIDD evidence_.^3 This guidance establishes a harmonized assessment
framework (including associated terminology) for MIDD evidence.

### B. Background (1.2)

For the purposes of this guidance, MIDD is defined^4 as the use of computational modeling
and simulation (M&S)^5 methods that can include and integrate nonclinical data, clinical data,
prior information, and knowledge (e.g., drug^6 and disease characteristics) to generate
evidence. The generated MIDD evidence is used to inform drug development and
decision-making by drug developers, regulatory authorities, and other stakeholders.

(^1) This guidance was developed within the Expert Working Group ( _Multidisciplinary_ ) of the International Council
for Harmonisation of Technical Requirements for Registration of Pharmaceuticals for Human Use (ICH) and has
been subject to consultation by the regulatory parties, in accordance with the ICH process. This document has
been endorsed by the ICH Assembly at _Step 4_ of the ICH process, January 2026. At _Step 4_ of the process, the
final draft is recommended for adoption to the regulatory bodies of the ICH regions.
(^2) The numbers in parentheses reflect the organizational breakdown of the document endorsed by the ICH
Assembly at Step 4 of the ICH process, January 2026.
(^3) MIDD evidence is defined as model outcomes (see Table 1 and Glossary) that have been determined by
application of the MIDD evidence assessment framework (see section II (2)), including model evaluation, to be
appropriate to inform the answer to the question of interest.
(^4) It is acknowledged that MIDD is a general term with other definitions that relate to its use with respect to
general drug development strategy (including trial design) and decision-making that may not require submission
to regulatory authorities.
(^5) While it is acknowledged that they are not always synonymous, the terms _model_ or _modeling_ are often used in
this guidance to represent _M&S_ to improve readability and reflect commonly used terminology.
(^6) For the purpose of this guidance, the term _drug_ is considered synonymous with investigational product,
medicine, medicinal product, biological product, and pharmaceutical product; this includes _drugs_ for which
marketing authorization is sought.


Early planning and inclusion of MIDD into the overall drug development plan ensures that the
necessary data are generated to support MIDD strategies. Similarly, as encouraged in this
guidance, effective communication and early alignment with regulatory authorities regarding
planned MIDD strategies facilitates the subsequent acceptance of MIDD evidence.

M&S methods and approaches used in MIDD strategies include, but are not limited to,
population pharmacokinetics and pharmacodynamics, physiologically based pharmacokinetics
and biopharmaceutics, exposure-response, model-based meta-analysis, quantitative systems
pharmacology and toxicology, agent-based models, disease progression models, and artificial
intelligence/machine learning. M&S methods and approaches may be used alone or in
combination.

### C. Scope of the Guidance (1.3)

This International Council for Harmonisation (ICH) M15 guidance on general principles for
MIDD applies to both current and emerging M&S methods, approaches, and applications. It
focuses on assessment of MIDD evidence and provides recommendations for related
regulatory interactions, reporting, and submission. This guidance is intended to facilitate a
multidisciplinary understanding of MIDD and associated evidence generation. This guidance
should be used in conjunction with relevant topic-specific ICH guidances.^7

Model development should be consistent with the general recommendations outlined in this
guidance in conjunction with current accepted standards and/or scientific practices for the
M&S method(s). This guidance does not focus on details regarding technical aspects of the
model development process.

This guidance should be read in conjunction with supplementary official ICH training
materials.^8

(^7) See for example the ICH guidances for industry _E4 Dose-Response Information to Support Drug Registration_
(July 1996), _E5 Ethnic Factors in the Acceptability of Foreign Clinical Data_ (June 1998), _E6(R3) Good Clinical
Practice (GCP)_ (September 2025), _E6(R2) Good Clinical Practice: Integrated Addendum to ICH E6(R1)
(March 2018), E7 Studies in Support of Special Populations; Geriatrics; Questions and Answers_ (March 2012),
_E7 Studies in Support of Special Populations Geriatrics_ (August 1994), _E9(R1) Statistical Principles for Clinical
Trials: Addendum: Estimands and Sensitivity Analysis in Clinical Trials_ (May 2021), _E9 Statistical Principles
for Clinical Trials_ (September 1998), _E11A Pediatric Extrapolation_ (December 2024), _E11(R1) Addendum:
Clinical Investigation of Medicinal Products in the Pediatric Population_ (April 2018), _E11 Clinical Investigation
of Medicinal Products in the Pediatric Population_ (December 2000), _E14 and S7B Clinical and Nonclinical
Evaluation of QT/QTc Interval Prolongation and Proarrhythmic Potential—Questions and Answers_ (August
2022), _E14 Clinical Evaluation of QT/QTc Interval Prolongation and Proarrhythmic Potential for Non-
Antiarrhythmic Drugs Questions and Answers (R3)_ (June 2017), _E14 Clinical Evaluation of QT/QTc Interval
Prolongation and Proarrhythmic Drugs_ (October 2005), _E17 General Principles for Planning and Design of
Multi-Regional Clinical Trials (July 2018), M12 Drug Interaction Studies_ (August 2024), _M12 Drug Interaction
Studies: Questions and Answers_ (August 2024), _M13A Bioequivalence for Immediate-Release Solid Oral
Dosage Forms_ (October 2024), and _S7B Nonclinical Evaluation of the Potential for Delayed Ventricular
Repolarization (QT Interval Prolongation) by Human Pharmaceuticals_ (October 2005). We update guidances
periodically. For the most recent version of a guidance, check the FDA guidance web page at
https://www.fda.gov/regulatory-information/search-fda-guidance-documents. Also see the ICH draft guidances
for industry _E6(R3) Good Clinical Practice Annex 2_ (December 2024) and _M13B Bioequivalence for Immediate-
Release Solid Oral Dosage Forms: Additional Strengths Biowaiver_ (May 2025). When final, these guidances
will represent the FDA’s current thinking on these topics.
(^8) At the time of release of this guidance, these training materials are in development.


### D. Guidance Overview (1.4)

This guidance first outlines the framework for assessing MIDD evidence (section II (2)), then
provides an overview of the model evaluation needed (section III (3)) as the basis for
MIDD evidence assessment, and finally presents general recommendations for reporting and
submission at both the model and MIDD evidence levels (section IV (4) ).

An overview of this guidance in relation to MIDD planning and MIDD evidence submission
is provided in Table 1.

In general, FDA’s guidance documents do not establish legally enforceable responsibilities.
Instead, guidances describe the Agency’s current thinking on a topic and should be viewed
only as recommendations, unless specific regulatory or statutory requirements are cited. The
use of the word _should_ in Agency guidances means that something is suggested or
recommended, but not required.


**Table 1. Guidance Overview in Relation to MIDD Planning and MIDD Evidence Submission**

```
MIDD Planning^1 and Regulatory Interaction^ Implementation, Reporting, and MIDD Evidence Submission^2
Key Assessment
Elements
```
```
Additional Considerations for
Interaction with Regulators
and to Inform Decision-making
```
```
Model
Evaluation^
```
```
Model Analysis
Reporting
```
```
Documentation for Regulatory
Interactions and Submissions
```
- Question of interest
- Context of use
- Model influence
- Consequence of
    wrong decision
- Model risk
- Model impact
    - Technical criteria for
       evaluating model and model
       outcome^3
    - Appropriateness of proposed
       MIDD
These should be documented
(e.g., in a MAP).
- Verification
- Validation and
applicability
assessment
- MAR(s) • Regulatory documents,
including complete assessment
table:
− Evaluation of model(s) and
model outcomes
− Outcome of MIDD
evidence assessment
− References to all relevant
MAPs and MARs
Section II.A (2.1) and
Appendix 1

```
Sections II.B (2.2) and IV.A
(4.1) and Appendix 1
```
```
Section III ( 3 ) Section IV.B (4.2)
and Appendix 2
```
Sections II ( 2 ) and IV.C (4.3)
and Appendix 1
MIDD = model-informed drug development; MAP = model analysis plan; MAR = model analysis report.
Note: Terms used in this table are defined in the relevant guidance sections.

(^1) MIDD planning refers to any timepoint when drug developers are planning MIDD activities, generally prior to availability of model outcomes relevant to the
current question of interest. Planning may include internal activities; however, for the purpose of this guidance, the focus is on consultation between drug
developers and regulatory authorities.
(^2) MIDD evidence submission refers to any timepoint when model outcomes are considered as MIDD evidence and submitted to regulators. This generally
refers to submission for marketing applications and also includes other regulatory interactions.
(^3) Model outcomes are results derived from M&S (i.e., via model-based predictions or simulations) and associated conclusions that are typically aligned to a
question of interest.
**Inform
Decision-making**


## II. FRAMEWORK FOR ASSESSMENT OF MIDD EVIDENCE (2)

This section describes key concepts for assessing MIDD evidence to inform decision-making.
To aid in regulatory interaction and submission, a table for assessment of MIDD evidence^9
(hereafter referred to as the _assessment table_ ) is provided in Appendix 1.

Drug developers should use the assessment table as a tool for communication between drug
developers and regulatory authorities, across multidisciplinary teams, to increase transparency
and provide an understanding of the proposed MIDD strategy, its implementation, and
available results with respect to provision of MIDD evidence. Early alignment with
regulatory authorities facilitates subsequent acceptance of MIDD evidence.

Within the following subsections, definitions for each part of the assessment table are
provided followed by instructions with respect to their use. An example of a completed
assessment table is provided in the supplemental official ICH training materials to illustrate
the concept and the thought process on how to fill out the assessment table.

### A. Key Assessment Elements (2.1)

The key assessment elements include question of interest, context of use, model influence,
consequence of wrong decision, model risk, and model impact. Model risk and model impact
are the outcome of risk and impact assessment, respectively. Model risk is the combination of
model influence and consequence of wrong decision and is essential for determining the
requirements for model evaluation. All key assessment elements are expected to be included
in the assessment table regardless of whether they are used at the planning or submission
stages. A clear understanding of these elements is considered essential for planning, evidence
assessment, and communication. The key assessment elements are described in the following
subsections. For each assessment element that is rated low, medium, or high, justification is
always expected and essential in enabling the assessment.

#### 1. Question of Interest (2.1.1)

The question of interest is the question that MIDD is intended to answer. The question of
interest should be explicitly stated. It should reflect and inform multidisciplinary assessments
and regulatory decision-making. It should be noted that the question of interest can be
broader than the intended use of the model(s). It should reflect information needed for the
drug development program given the development stage and/or product lifecycle status. If
MIDD is planned to answer different questions of interest, it is recommended to use separate
tables for each question.

#### 2. Context of Use (2.1.2)

The context of use should be outlined as a concise, clear, and explicit description of the role
and scope of the model(s) used to answer the question of interest. It should include a
description of the model, its role and scope, the data used to build the model, and any
additional data or evidence that will inform the answer to the question of interest. The
additional data or evidence can include evidence from clinical trials or nonclinical

(^9) Some concepts in this assessment framework/table have been modified from: The American Society of
Mechanical Engineers (ASME) V & V 40- 2018 _Assessing Credibility of Computational Modeling Through
Verification and Validation: Application to Medical Devices_.


experiments, post-marketing, or real-world evidence that will inform the answer to the
question of interest.

#### 3. Model Influence (2.1.3)

Model influence is the intended weight of the model outcomes in decision-making
considering the contribution of additional data or evidence.

Model influence should be described and rated as low, medium, or high, and then the rating
justified. The description, rating, and justification should focus on the weight of the model
outcomes in relation to the other relevant information used for answering the question of
interest. The model influence rating should increase from low to medium to high as the
weight of model outcomes increases.

In general, when model outcomes are the sole source to support the decision, model influence
should be considered as high. If there is considerable data and evidence coming from other
relevant sources, the model influence may be rated low or medium depending on the weight
of the model outcomes.

#### 4. Consequence of Wrong Decision (2.1.4)

The consequence of wrong decision refers to the potential negative effect (e.g., on patient
safety and/or lack of efficacy) resulting from an incorrect decision based on all available
information.

Consequence of wrong decision should be described and rated as low, medium, or high, and
then the rating justified.

The rating for consequence of wrong decision should take into consideration both the severity
of potential negative effects as well as the likelihood that a wrong decision will result in
potential negative effects. Both of these factors should be considered based on all available
information at the time of regulatory interaction (e.g., nonclinical data, clinical data, prior
information, and knowledge) and then combined to generate a rating for consequence of
wrong decision.

#### 5. Model Risk (2.1.5)

Model risk is the contribution of the model outcomes to a possible wrong decision and
subsequent potential undesirable consequences.

The model risk is derived by combining model influence and consequence of wrong decision.
Model risk should be described and rated as low, medium, or high, and then the rating should
be justified. The rating should increase from low to medium to high as the ratings for model
influence and/or consequence of wrong decision increase. In general, if the ratings for both
model influence and consequence of wrong decision are low, model risk is low. If the ratings
for both are high, model risk is high. When the ratings for model influence and consequence
of wrong decision differ, the model risk rating may be driven by the most influential of the
two items; these considerations should be captured in the justification.


Model risk is key for determining the requirements for model evaluation and is used for
MIDD planning, communication, and evidence assessment. Model evaluation should, at
minimum, meet the current accepted standards and be commensurate with the model risk (see
section III (3)).

Model risk should be interpreted in the context of answering a specific question of interest and
is not to be perceived as a risk intrinsic to MIDD or M&S.

#### 6. Model Impact (2.1.6)........................................................................................................................

Model impact reflects the extent to which the proposed MIDD strategy varies from regulatory
standards, or expectations when no regulatory standard is in place, for answering the question
of interest.

Model impact should be described and rated as low, medium, or high, and then the rating
should be justified.

The rating should increase with the degree to which the MIDD strategy varies from current
regulatory standards, or expectations when no regulatory standard is in place.

Model impact is used for MIDD planning, communication, early alignment, and evidence
assessment.

```
B. Additional Considerations for Interaction with Regulators and to Inform
Decision-making (2.2)
```
In addition to the key assessment elements described in section II.A (2.1), technical criteria,
appropriateness of proposed MIDD, evaluation of model(s) and model outcomes, and
outcome of the MIDD evidence assessment should be included to inform decision-making
related to MIDD planning and/or MIDD evidence submission and should be provided to
regulators to support regulatory interactions.

Technical criteria and appropriateness of proposed MIDD can be discussed as early as the
planning stage in conjunction with key assessment elements.

A summary related to evaluation of model and model outcomes should be submitted once the
analysis is completed and ready for regulatory submission.

The outcome of the MIDD evidence assessment should be provided at the MIDD evidence
submission stage.

#### 1. Technical Criteria (2.2.1)

Technical criteria are key criteria for evaluating the model^10 and model outcomes, and that are
needed to inform MIDD evidence acceptance, contributing to the answer to the question of
interest.

(^10) General technical standards for model evaluation are addressed in section III (3).


A clear and concise description of and rationale for the technical criteria, which are specific to
the question of interest, should be provided in the assessment table.

As part of predefining technical criteria, drug developers should outline how this is
commensurate with model risk. The details of technical criteria should be provided in
appropriate documents (e.g., in a model analysis plan [MAP] or regulatory interaction
background materials; see section IV (4) ).

#### 2. Appropriateness of Proposed MIDD (2.2.2)

The appropriateness of proposed MIDD is the rationale for why the proposed MIDD is
suitable to answer the question of interest.

To facilitate regulatory interaction, most importantly at the planning stage, drug developers
should provide a brief discussion of why and how the proposed MIDD is considered
appropriate for answering the question of interest. Drug developers are encouraged to
consider aspects of the key assessment elements to provide justification for appropriateness.
Information on how the technical criteria are suitable to ensure the appropriateness of the
model outcomes for generating MIDD evidence should be included.

#### 3. Evaluation of Model(s) and Model Outcomes (2.2.3)

Evaluation of model(s) and model outcomes is a brief discussion of the key results and
conclusions of the technical evaluation of the model and model outcomes.

To facilitate regulatory interaction at the MIDD evidence submission stage, drug developers
should include a concise summary of the technical evaluation of the model and model
outcomes and describe how they fulfill the technical criteria. A detailed evaluation of model
and model outcomes should be provided in appropriate documents (e.g., in a model analysis
report [MAR] or regulatory interaction background materials; see Appendix 2). For
additional details on model evaluation, refer to section III (3).

#### 4. Outcome of the MIDD Evidence Assessment (2.2.4)

The outcome of the MIDD evidence assessment is the multidisciplinary team’s assessment
and conclusion on whether the model outcomes are considered MIDD evidence. This should
integrate all the assessment elements and be summarized.

Once model outcomes are determined to be MIDD evidence, it should be used to answer the
question of interest. A concise summary of the MIDD evidence and its use should be
provided. MIDD evidence can be used in combination with other relevant information and/or
evidence to answer the question of interest.


## III. MODEL EVALUATION (3)

This section provides an overview of model evaluation elements (i.e., verification, validation,
and applicability assessment^11 ) and related general recommendations. These elements should
be used to determine the acceptability of the model(s) to answer the question of interest,
forming the basis of MIDD evidence assessment to inform related decision-making (see
section II (2) ). Model evaluation should at minimum meet the current accepted standards, if
available, and/or established scientific practices associated with the specific M&S method(s)
(see section I.C ( 1.3)) and be commensurate with model risk (see s ection II (2) and section
II.B.1 (2.2.1)).

Descriptions of model evaluation and related general recommendations in this section are
intentionally presented at a high level to facilitate use across M&S methods. Adopting these
recommendations ensures that appropriate actions have been taken to inform decision-making.

The elements of model evaluation are defined as follows:

- Verification activities aim to ensure user-generated codes for processing the data and
    conducting the analysis are error-free, equations reflecting the model assumptions and
    their representation in the programming language or software are correct, and
    calculations are accurate.
- Validation and applicability assessment (also referred to as _fit-for-purpose_ ) activities
    aim to assess the model performance and robustness. These activities include
    assessing the adequacy and relevance of the following: the data, the model’s
    conceptual form (e.g., overall structure and complexity), the model assumptions, the
    approach to model development, the graphical and numerical diagnostics, and the
    external validation. Validation focuses on the overall comparison of the model versus
    data, prior information, and knowledge, while applicability assessment focuses on the
    adequacy of the data and model for each intended use.

The following are general recommendations for the model evaluation elements:

**Verification**

- Verification of the key user-generated codes, equations, and calculations should be
    documented and available for review by regulatory authorities.
- Modeling activities should use a valid computerized system that is reliable,
    reproducible, and traceable. Documentation of appropriate software testing should be
    available.
- Compliance with appropriate quality assurance is expected for data management and
    modeling activities.

(^11) Model applicability is not interchangeable with appropriateness of proposed MIDD. As described in section
II.B.2 (2.2.2), appropriateness assesses whether the proposed MIDD strategy is suitable, while applicability
assesses whether the data and model are adequate for their intended use.


**Validation and Applicability Assessment**

- The relevance and appropriateness of the data to answer the question of interest should
    be justified. The rationale for exclusion of data should be provided and the potential
    for bias assessed. In general, data selection, associated transformations, and
    imputations should be specified, justified, and documented in the MAP and MAR.
- The model structure and parameters should be consistent with the available knowledge
    on drug characteristics, pharmacology, physiology, and disease pathophysiology,
    when relevant.
- Limitations of the data and model should be described and discussed.
- Key M&S assumptions^12 should be identified, described, and justified, and alternatives
    considered.
- M&S method-specific issues should be considered (e.g., selection bias for
    model-based meta-analysis, knowledge gaps for a mechanistic model, or overfitting
    for an artificial intelligence/machine learning model).
- Model robustness should be assessed to characterize the dependency on data,
    parameters, parameterization, assumptions, and associated uncertainty (e.g., sensitivity
    analysis).
- Model performance (e.g., precision and bias) should meet general technical standards
    associated with the specific M&S method(s) and should be assessed using graphical
    and numerical metrics. The metrics that relate to the question of interest and
    associated analysis objective(s) should be prioritized in model evaluation.
- As indicated in section II.B (2.2), drug developers are encouraged to gain alignment
    with regulatory authorities on technical criteria as part of the MIDD using the
    assessment table.
- External validation with independent data is encouraged in order to assess the
    adequacy of model performance. Depending on the question of interest, context of
    use, and model risk, external validation can further increase confidence and in some
    cases can be essential for the model’s proposed application.
- Simulation methods and scenarios should be described sufficiently to enable the
    evaluation of their plausibility and the relevance to model applicability and should
    account for parameter and assumption uncertainties.
- Predefined MAPs covering the planned model evaluation activities and technical
    criteria are recommended (see section IV.A (4.1)). Changes to the planned analyses
    should be justified, and these should be documented in the MAR.

(^12) M&S assumptions include but are not limited to data handling (e.g., imputation), model structure and
parameters (e.g., derived or fixed based on prior information), and mathematical or statistical aspects of the
model.


## IV. MIDD REPORTING AND SUBMISSION (4)

This section provides recommendations on MAPs (section IV.A (4.1)), MARs (section IV.B
(4.2)), and documentation for regulatory interactions and submissions (section IV.C (4.3)).

### A. Model Analysis Plan (4.1)

It is recommended to pre-define^13 and document each intended model analysis in a MAP. A
MAP typically includes an introduction, objectives, data, and methods, which align with the
corresponding MAR sections (Appendix 2). Planned model evaluation activities and
technical criteria should be described in the MAP. For regulatory interactions, providing a
MAP that defines the M&S can facilitate discussions.

### B. Model Analysis Report(4.2)

The results of each model analysis submitted to regulators should be documented in a MAR.
Descriptions of the typical MAR sections are provided in Appendix 2. The MAR structure
can be adjusted to meet the needs for reporting specific M&S methods. If a MAP was
developed, it should be provided as an appendix within the associated MAR. Changes to the
planned analyses should be justified and documented. M&S results should be described, and
interpretation of results and model evaluation should be discussed.

### C. Documentation for Regulatory Interactions and Submissions (4.3)

The following are general recommendations for documentation of MIDD planning as well as
evidence reporting and submissions:

- The assessment table should be used as a communication tool throughout interactions
    with regulatory authorities during the MIDD planning stage and MIDD evidence
    submission stage.
- New questions of interest may emerge requiring separate assessment tables, and the
    associated plan could evolve as data and knowledge accumulate. Some of these
    iterations may require engagement with regulatory authorities to gain alignment on the
    MIDD planning.
- Additional documents relevant to MIDD planning or model use in the generation of
    MIDD evidence, such as individual MAPs or MARs, should be cross-referenced
    within the assessment table and other relevant regulatory documents.
- The assessment table should be included in the most appropriate section(s) of the
    respective regulatory documentation (e.g., regulatory interaction background materials
    and Common Technical Document sections) in line with the question of interest.
- Additional details supporting the assessment table and not captured in the MAR(s)
    (e.g., when a question of interest emerges after MAR finalization and a new MAR is

(^13) For the purposes of this guidance, _pre-define_ refers to documentation prior to accessing the data or performing
the analysis, as appropriate considering the context of use.


```
not produced) should be described in other relevant regulatory documents. These
details may include but are not limited to the following:
```
```
− Further descriptions of the integration of multiple models or multiple sources of
evidence to answer the question of interest
```
```
− Additional evaluation and discussion of model(s), model outcomes, and technical
criteria related to the specific to the question of interest
```
- Inclusion of a summary of previously received regulatory feedback (including
    regulatory assessment, if possible) on the MIDD is encouraged to be provided within
    regulatory interaction background materials and other relevant regulatory documents.
- All documents and files supporting submitted MIDD evidence, including data used in
    M&S analyses, relevant coding scripts (e.g., the base and final models for population
    pharmacokinetics including dataset building), definition files, and other relevant
    electronic files used should be submitted or available for regulatory review and
    assessment.


##### APPENDICIES

## APPENDIX 1: TABLE FOR ASSESSMENT OF MIDD EVIDENCE

**Item Definition Instruction Entry**

**Key Assessment Elements**
Key assessment elements are expected to be included in the assessment table regardless of whether
it is used at planning or submission stages.
Question of
interest^1

```
The question that MIDD is
intended to answer.
```
Explicitly state the question of
interest. This should reflect and
inform multidisciplinary
assessments and regulatory
decision-making.
Context of use The role and scope of the
model(s) used to answer the
question of interest.

Provide a concise, clear, and
explicit description of the model,
its role and scope, and the data used
to build the model. In addition,
discuss any additional data or
evidence that will inform the
answer to the question of interest.
Model influence The intended weight of the
model outcomes in decision-
making considering the
contribution of additional data
or evidence.

```
Describe the model influence; rate
it as low, medium, or high; and
provide a justification for the
rating.
```
Consequence of
wrong decision

```
The potential negative effect
(e.g., on patient safety and/or
lack of efficacy) resulting from
an incorrect decision based on
all available information.
```
```
Describe the consequence of a
wrong decision; rate it as low,
medium, or high; and provide a
justification for the rating.
```
Model risk^2 The contribution of the model
outcomes to a possible wrong
decision and subsequent
potential undesirable
consequences.

The model risk is derived by
combining model influence and
consequence of wrong decision.
Describe the model risk; rate it as
low, medium, or high; and provide
a justification for the rating.
Model impact The extent to which the
proposed MIDD strategy varies
from regulatory standards, or
expectations when no
regulatory standard is in place,
for answering the question of
interest.

```
Describe the model impact; rate it
as low, medium, or high; and
provide a justification for the
rating.
```
```
continued
```

_Table continued_

**Item Definition Instruction Entry**

```
Additional Considerations for Interaction with Regulators and to Inform Decision-making
MIDD Planning Stage^3
The following items/rows are to be completed at the MIDD planning stage:
Technical criteria Key criteria for evaluating the
model and model outcomes,
and that are needed to inform
MIDD evidence acceptance,
contributing to the answer to
the question of interest.
```
```
Provide a clear and concise
description of, and rationale for, the
technical criteria, which are
specific to the question of interest.
```
```
Appropriateness
of proposed
MIDD
```
```
The rationale for why the
proposed MIDD is suitable to
answer the question of interest.
```
```
Provide a brief discussion of why
and how the proposed MIDD is
considered appropriate for
answering the question of interest,
taking into account aspects of the
key assessment elements and
including information on how the
technical criteria are suitable to
ensure the appropriateness.
MIDD Evidence Submission Stage
The following items/rows are to be filled at the MIDD evidence submission stage:
Evaluation of
model(s) and
model outcomes
```
```
A brief discussion of the key
results and conclusions of the
technical evaluation^4 of the
model and model outcomes.
```
```
Provide a concise summary of the
technical evaluation of the model
and model outcomes and describe
how they fulfill the technical
criteria.
Outcome of the
MIDD evidence
assessment^5
```
```
The multidisciplinary team’s
assessment and conclusion on
whether the model outcomes are
considered MIDD evidence.
```
```
Provide a concise multidisciplinary
assessment and conclusion of
whether the model outcomes are
considered MIDD evidence. This
should integrate all of the
assessment elements.
Also provide a concise summary of
the MIDD evidence related to the
question of interest.
MIDD = model-informed drug development.
Note: This table should be used to provide concise information. Details should be provided in appropriate supportive
documents (e.g., in a model analysis plan (MAP) or regulatory interaction background materials).
```
(^1) If MIDD is planned to answer different questions of interest, it is recommended to use separate tables for each question.
**2** (^) Model risk should be interpreted in the context of answering a specific question of interest and is not to be perceived as
a risk intrinsic to MIDD or modeling and simulation (M&S).
(^3) These items should also be provided at the MIDD evidence submission stage.
(^4) Using the principles of model evaluation described in section III (3), with specific focus on technical criteria.
(^5) _Assessment_ in this context does not refer to any regulatory review activities or processes.


## APPENDIX 2: MODEL ANALYSIS REPORT CONTENT

This appendix provides the content typically found within a model analysis report (MAR),
although the content and structure should be adapted to the specific modeling and simulation
(M&S) methodology employed. As noted in section IV.C (4.3), a single MAR or multiple
MARs can provide model outcomes to answer question(s) of interest. The sections of the
MAR, especially the objectives, may align directly with particular question(s) of interest or
may have a broader perspective.

When a MAR describes model outcomes intended to be model-informed drug development
(MIDD) evidence to support the answer to a specific question of interest, the details
associated with elements of the assessment table (e.g., technical criteria, model outcomes) can
be included in the MAR and cross-references to the relevant assessment table elements may
be included.

```
Sections Content
Executive
summary
```
- An overview of the rationale for the analyses
- A brief summary of the data and methods
- A brief summary of the results and conclusions

Introduction (^) • The rationale for the analyses

- Relevant background information and knowledge
- If applicable, a description of pre-existing analyses with reference to
    previously submitted reports
Objectives The objectives of the analyses including the intended application of the model.
These may align directly with particular question(s) of interest or may have a
broader perspective.^1^
Data and
methods

```
Descriptions of the following:
```
- Data sources
    − Criteria and rationale with respect to source data inclusion and
       exclusion
    − Relevant design features of studies and/or experiments
- M&S methods, computational platforms, model development, assumptions,
    and strategic approaches (e.g., the sequence of development, numerical
    methods; see section II (2) and section III (3))
- Approaches for model evaluation (i.e., verification, validation, and
    applicability assessment; see section III (3))
- If relevant, prediction and simulation methods and scenarios
- Detailed technical criteria for model evaluation and model outcomes^1

Results (^) • Data description, including graphical and/or tabular displays, as
appropriate. Data excluded during the analyses should be described along
with the appropriate rationale.

- The results of model development and model evaluation, with predictions
    and simulations (e.g., parameter estimates, related uncertainty) as graphical
    and/or tabular displays
- The detailed results of the assessment against the technical criteria for
    model evaluation and model outcomes^1
- If relevant, deviations from the MAP should be described and justified.
    _continued_


_Table continued_
**Sections Content**
Discussion Interpretation of results, including data and model adequacy, limitations of the
data and model, and clinical and/or other implications, taking into account:

- Deviations from the MAP
- Model evaluation and model outcomes^1 (including technical criteria^1 and
    model applicability)
- Relevant nonclinical and clinical information and knowledge, if applicable

Conclusions The conclusions of the analyses
Appendices Additional materials cross-referenced in the MAR, for example:

- A references list covering the sources of data used for the analyses
    (e.g., bioanalytical reports, clinical study reports, laboratory reports, or
    literature)
- Supplemental data descriptions and model development and evaluation
    results, including graphical and/or tabular displays, as appropriate
- The user-generated code for the relevant model(s)
M&S = modeling and simulation; MAP = model analysis plan; MAR = model analysis report.

(^1) When a MAR describes model outcomes intended to be MIDD evidence to support the answer to a specific question of
interest, the details associated with elements of the assessment table (e.g., technical criteria, model outcomes) can be
included in the MAR and cross-references to the relevant assessment table elements may be included.


## GLOSSARY.................................................................................................................................

The following list of key terms and definitions is intended to promote consistent
understanding and application of this guidance:

**Appropriateness of proposed MIDD** :
The rationale for why the proposed MIDD is suitable to answer the question of interest.

**Consequence of wrong decision** :
The potential negative effect (e.g., on patient safety and/or lack of efficacy) resulting from an
incorrect decision based on all available information.

**Context of use** :
The role and scope of the model(s) used to answer the question of interest.

**Evaluation of model(s) and model outcomes** :
A brief discussion of the key results and conclusions of the technical evaluation of the model
and model outcomes.

**MIDD evidence** :
Model outcomes that have been determined by application of the MIDD evidence assessment
framework, including model evaluation, to be appropriate to inform the answer to the question
of interest.

**MIDD evidence submission stage** :
Any timepoint when model outcomes are considered as MIDD evidence and submitted to
regulators. This generally refers to submission for marketing applications and also includes
other regulatory interactions.

**MIDD planning stage** :
Any timepoint when drug developers are planning MIDD activities, generally prior to
availability of model outcomes relevant to the question of interest. Planning may include
internal activities; however, for the purpose of this guidance, the focus is on consultation
between drug developers and regulatory authorities.

**Model evaluation** :
Model evaluation refers to performing verification, validation, and applicability assessment of
the model.

**Model impact** :
The extent to which the proposed MIDD strategy varies from regulatory standards, or
expectations when no regulatory standard is in place, for answering the question of interest.

**Model influence** :
The intended weight of the model outcomes in decision-making considering the contribution
of additional data or evidence.

**Model-Informed Drug Development (MIDD)** :
The use of computational modeling and simulation (M&S) methods that can include and
integrate nonclinical data, clinical data, prior information, and knowledge (e.g., drug and


disease characteristics) to generate evidence to inform drug development and decision-making
by drug developers, regulatory authorities, and other stakeholders.

**Model outcomes** :
Results derived from M&S (i.e., via model-based predictions or simulations) and associated
conclusions that are typically aligned to a question of interest. These can be assessed as
MIDD evidence using the MIDD evidence assessment framework.

**Model risk** :
The contribution of the model outcomes to a possible wrong decision and subsequent potential
undesirable consequences.

**Multidisciplinary team** :
A team of subject matter experts from functional areas relevant to the question of interest and
context of use.

**Outcome of the MIDD evidence assessment** :
The multidisciplinary team’s assessment and conclusion on whether the model outcomes are
considered MIDD evidence. _Assessment_ in this context does not refer to any regulatory
review activities or processes.

**Question of interest** :
The question that MIDD is intended to answer.

**Technical criteria** :
Key criteria for evaluating the model and model outcomes, and that are needed to inform
MIDD evidence acceptance, contributing to the answer to the question of interest.

**User-generated code:**
Instructions written by the user of a programming language or software.

**Validation and applicability assessment** :
Activities that aim to assess the model performance and robustness.

**Verification** :
An activity that aims to ensure user-generated codes for processing the data and conducting
the analysis are error-free, equations reflecting the model assumptions and their representation
in the programming language or software are correct, and calculations are accurate.


