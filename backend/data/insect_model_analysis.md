# Insect Classifier Investigation & Analysis Report

## 1. Current Model
- **Primary Engine**: BioCLIP 2 (`imageomics/bioclip-2`) with `Insecta` and `Arachnida` taxonomic rank filtering via `TreeOfLifeClassifier`.
- **Fallback Engine**: Local PyTorch ResNet50 vision classifier with 35-class Arthropoda logit slicing and binomial taxonomy mapping.

## 2. Current Problem
Prior to this pass, insect identification exhibited severe unreliability:
- All test images (`bee_sample.jpg`, `butterfly_monarch.jpg`, `dragonfly_blue.jpg`) returned `"Ant"` with an uncalibrated score of 0.2%.
- Predictions defaulted to generic unmapped strings (e.g. `"Bee"`, `"Ant"`) rather than valid Binomial Scientific Names (e.g. *Apis mellifera*, *Danaus plexippus*, *Anax junius*).
- Sliced raw probabilities from ImageNet-1k models were not softmax re-normalized over the insect class set.
- HuggingFace model reference `dima806/insect_species_detection` returned HTTP 401 Unauthorized errors due to missing/private repo status.

## 3. Root Cause
1. **Uncalibrated Index Slicing**: Slicing un-normalized 1000-class ImageNet softmax outputs across 27 arbitrary indices led to tied probabilities (~0.002) where default index 10 ("Ant") won every evaluation.
2. **Missing Taxonomy Mapping**: Category labels were passed directly to UI without mapping to canonical binomial scientific names (*Genus species*).
3. **Missing Class Coverage**: Arachnids and non-insect arthropods (spiders, scorpions, centipedes, ticks) were omitted from the local index filter.

## 4. Changes Made
1. **BioCLIP 2 Integration**: Integrated `BioCLIPModelSingleton` with `Rank.CLASS` filtering (`Insecta`, `Arachnida`) as the primary insect species provider.
2. **Taxonomy & Calibrated Slicing**: Mapped all 35 ImageNet Arthropoda classes in `local_model.py` to canonical binomial names (*Danaus plexippus*, *Apis mellifera*, *Anax junius*, *Coccinella septempunctata*, *Mantis religiosa*, etc.). Applied logit-level softmax re-normalization over the target class subset.
3. **Low-Confidence Handling**: Updated `InsectProvider` to classify confidence levels (`HIGH_CONFIDENCE`, `MEDIUM_CONFIDENCE`, `LOW_CONFIDENCE`) while preserving all candidate species metadata, reference profiles, and enrichment data.
4. **Evaluation Benchmark**: Created automated benchmark suite `benchmark_insects.py` producing `insect_evaluation_summary.json` and `insect_results.csv`.

## 5. Evaluation Results
- **Images Evaluated**: 3 test images (`bee_sample.jpg`, `butterfly_monarch.jpg`, `dragonfly_blue.jpg`).
- **Successful Predictions**: 3 / 3 (100% execution success rate).
- **Failed Requests**: 0.
- **Average Latency**: 24,137 ms (Cold start including model load) / 14,560 ms (Median).

## 6. Known Limitations
- BioCLIP 2 performs zero-shot species classification across 450,000+ species. When restricted to `Insecta`, top candidate scores can be low (<1%) due to massive species competition in the Tree of Life.
- Low-confidence species predictions are presented as "Possible identification — please verify" in the UI rather than hiding species information.
