# STEM BIO-AI Clinical Adjacency Trigger List

Reference list of 60+ tools, libraries, and keywords that trigger CLINICAL_ADJACENT detection.
Used by both TEXT_PATH (README keyword scan) and CODE_PATH (import/dependency scan).

## Severity Classification (PATCH-30)

- **CA-DIRECT**: Currently outputs patient-facing recommendations, dosage adjustments, diagnostic classifications, or treatment decisions
- **CA-INDIRECT**: Processes clinical data but does not directly output patient-facing decisions
- **CA-PLANNED**: Listed in roadmap or future work but no implementation exists

Default severity is CA-INDIRECT unless the specific usage context indicates otherwise.
CODE_PATH analysis may upgrade CA-INDIRECT to CA-DIRECT based on actual function behavior.

---

## Medical Imaging and Segmentation (CA-INDIRECT default)

pydicom, SimpleITK, nnU-Net, napari (DICOM context), pathml, histolab,
scikit-image (pathology context), OpenCV (medical context), MONAI,
MONAI Label, MONAI Deploy, MedSAM, Segment Anything Medical Imaging (SAMI),
MedicalZoo, TorchIO, HighRes3DNet, DeepMedic, HD-BET, QuPath,
CellProfiler, deepslide, Slideflow

## Drug Interaction / Docking / Discovery (CA-INDIRECT default)

AutoDock Vina, DiffDock, DrugBank, DailyMed, DDInter, GtoPdb,
OpenTargets, DeepChem (clinical targets), Therapeutics Data Commons (TDC),
REINVENT, DrugEx, MolBART, ChemBERTa (clinical context), ADMET-AI,
pkasolver, SwissADME

## Diagnostic Genomics (CA-INDIRECT default, CA-DIRECT if outputting variant classification)

ClinVar, ClinPGx, GWAS Catalog, gnomAD (clinical context),
GATK (diagnostic pipeline), Franklin, Varsome, InterVar, AutoPVS1,
SpliceAI (clinical), Alamut, Cancer Genome Interpreter, OncoKB,
cBioPortal (clinical)

## Clinical Trial / Regulatory Data (CA-INDIRECT default)

ClinicalTrials.gov connector, FDA database connector, EMA database connector,
MFDS connector, MIMIC-III / MIMIC-IV pipeline, eICU pipeline,
PhysioNet data connectors

## Medical Foundation Models and Clinical LLMs (CA-INDIRECT default)

Med-PaLM, Med-PaLM 2, MedPaLM-M, OpenBioLLM, BioMedGPT,
BioGPT (clinical context), ClinicalBERT, BioBERT (clinical NER/IE context),
GatorTron, NYUTron, Clinical-T5, LLaVA-Med, BioViL, BioViL-T,
RadFM, CheXagent, MedFlamingo, PathChat, CONCH, UNI (clinical pathology)

## Clinical NLP Pipelines (CA-INDIRECT default)

cTAKES, MetaMap, QuickUMLS, MedSpaCy, scispaCy (clinical entity context),
CLAMP, Stanza (clinical), BERT-based ICD coding

## Pharmacogenomics (CA-DIRECT when outputting dosage/avoidance recommendations)

CPIC guidelines, PharmGx, DPYD, CYP2D6, CYP2C19, CYP3A4,
pharmacogenomic allele interpretation, drug-gene interaction databases

## README Keyword Scan Triggers

"clinical trial", "patient data", "EHR", "electronic health record",
"diagnostic", "prognosis", "treatment recommendation", "FDA clearance",
"CE mark", "SaMD", "hospital deployment", "clinical validation"

## CA-PLANNED Indicators (flag only, no penalty)

"planned clinical integration", "future work: clinical",
"roadmap: ClinVar", "upcoming: FDA submission support",
skill stubs in routing tables without backing implementation
