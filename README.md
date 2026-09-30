# Fantastic Four: Sampling and Reliability

A presentation demo for our breast cancer biomarker prediction project. We compare random and spatially distributed patch sampling, then test whether prediction disagreement helps identify unreliable cases beyond confidence alone.

**All cases, tissue maps, labels, and results are simulated.** The demo uses a fitted logistic classifier and a fixed toy feature map. It does not use patient images or a pretrained pathology encoder. It does not establish clinical performance or research novelty.

## Run on a laptop

Python 3.10 or newer is the only requirement. No Python package installation, GPU, or model download is needed.

```sh
git clone https://github.com/lukeblevins/fantastic-four-demo.git
cd fantastic-four-demo
python3 app.py
```

Open http://127.0.0.1:8765. On macOS, you can also double-click `Start Demo.command`. Leave the terminal open while presenting. Press Control-C to stop. If the port is occupied, use `python3 app.py --port 8766` and open that port instead.

## Open in Colab

[Open the notebook](https://colab.research.google.com/github/lukeblevins/fantastic-four-demo/blob/main/demo.ipynb), connect to a CPU runtime, and run the cells in order. The notebook starts the Python server and displays the app in the output. A separate cell builds a downloadable offline copy. No access token, Drive mount, or tunnel is needed. The first cell downloads this repository, so it needs internet access.

## Keep an offline copy

```sh
python3 build_offline.py
```

Open `results/demo.html` in a browser. It contains every available setting and runs without a server or internet connection. The calculations are made when the file is built; changing settings selects the corresponding reproducible experiment. Source links still need internet access.

## A short walkthrough

1. Start with 32 patches, 20 repeated samples, and seed 42. Choose **Find an unstable case**, then **Play samples**. The white outlines move while the classifier stays fixed. The two probability traces share the same scale.
2. Open **Compare review flags**. Both rules flag 20% of the test cases. Compare the number of errors left among the remaining 80%. Change the review rate or sampling method.
3. Open **How it works**. Explain what is implemented and what still needs real pathology data. A smaller variance is not proof that a prediction is correct.

Presentation view reduces the page header. Press Escape to leave it. Download results saves the experiment settings, predictions, sample coordinates, review flags, and evaluation metrics as JSON.

## Experiment design

- Generate 240 simulated cases, each with a 24 × 16 patch grid and a binary ER label.
- Assign each case to exactly one split: 120 training, 40 validation, 80 test.
- Apply a fixed three-feature toy transformation to each patch and average the features per case.
- Fit a regularized logistic classifier on training cases. Select the classification threshold using validation cases only. Training and validation use all simulated patches; both test sampling methods use the same fitted model and threshold.
- At test time, compare uniform random sampling without replacement with one random patch per equal-area spatial region. Use identical patch counts and repeat counts.
- Average repeated probabilities for the case prediction. Confidence is `max(mean probability, 1 - mean probability)`. Disagreement is the sample variance of repeated probabilities.
- Rank low-confidence cases or high-variance cases for review. At each displayed review rate, flag exactly the same number of cases. Ties are resolved by case ID. This is a retrospective ranking comparison, not a validated deployment threshold.
- Report retained-case error, accuracy with a 95% Wilson interval, AUROC, Brier score, calibration bins, and errors by class. Accuracy intervals describe simulated test-case uncertainty only; no significance claim is made for the comparison.

The spatial signal is generated with smooth regional variation and patch noise. That design can favor spatial coverage. The demo does not force the disagreement rule to win. Do not use its results as evidence that our hypothesis is supported in real tissue.

## Move toward the proposed research

Replace `make_case` and the toy features with quality-controlled H&E patches and cached features from a frozen pathology encoder. Keep patient IDs through splitting and aggregation. Verify labels, dataset permissions, magnification, tissue masks, and multi-slide handling before training. Then evaluate the sampling methods with settings fixed on validation data and an untouched test set. PR and HER2 remain later extensions.

The current maps show feature values and selected regions. They are not pathology images, attention maps, or clinically validated explanations.

## Sources

- Atiya et al. (2026). *Benchmarking Open-Source Pathology Foundation Models for Breast Cancer Biomarker Prediction from H&E Whole-Slide Images.* https://doi.org/10.3390/cancers18152475
- Koyun et al. (2026). *Slide Selection Introduces Sampling-Induced Prediction Uncertainty in Digital Pathology AI: Evidence from Multi-Slide Breast Cancer Cohorts.* https://doi.org/10.3390/cancers18162540
- Dolezal et al. (2022). *Uncertainty-informed deep learning models enable high-confidence predictions for digital histopathology.* https://doi.org/10.1038/s41467-022-34025-x

These studies motivate the comparison. This demo does not reproduce their models or results.

## Check the implementation

```sh
python3 -m unittest discover -s tests -v
```

The tests check patient separation, equal patch counts, spatial coverage, matched review rates, error denominators, reproducibility, and input bounds.

## Interface

Material Web supplies the filled, tonal, outlined, and text buttons. The interface uses a teal Material 3 token set, Roboto Variable, rounded navigation indicators, and tonal surfaces. Native selects and canvas charts keep the rest of the app small. Bundled assets run offline; their licenses are in `licenses/` and `static/vendor/material.js.LEGAL.txt`.

There is no frontend framework or production build required to run the demo. `ui/material.js` lists the component imports. To rebuild the checked-in component bundle, run `npm install` and `npm run build`.
