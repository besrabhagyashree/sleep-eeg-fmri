# 📚 References

Every published method, metric, dataset, standard and software package this project uses or builds on. Each entry was checked against Crossref (the DOI registry) or the publisher on 22 October 2026. "Used in" points to where the work is applied.

## Dataset and data standards

| Reference | Used in |
|---|---|
| Gu, Y., Han, F., Sainburg, L. E., Schade, M. M., Buxton, O. M., Duyn, J. H., & Liu, X. (2022). An orderly sequence of autonomic and neural events at transient arousal changes. *NeuroImage*, 264, 119720. [doi:10.1016/j.neuroimage.2022.119720](https://doi.org/10.1016/j.neuroimage.2022.119720) | The paper describing the dataset; preprint: [doi:10.1101/2022.02.05.479238](https://doi.org/10.1101/2022.02.05.479238) |
| Dataset: Gu, Y., et al. *Simultaneous EEG and fMRI signals during sleep from humans.* OpenNeuro ds003768, v1.0.13. [doi:10.18112/openneuro.ds003768.v1.0.0](https://doi.org/10.18112/openneuro.ds003768.v1.0.0) | All data, sleep-stage labels and metadata |
| Markiewicz, C. J., Gorgolewski, K. J., Feingold, F., Blair, R., Halchenko, Y. O., Miller, E., et al. (2021). The OpenNeuro resource for sharing of neuroscience data. *eLife*, 10, e71774. [doi:10.7554/eLife.71774](https://doi.org/10.7554/eLife.71774) | Data source |
| Gorgolewski, K. J., Auer, T., Calhoun, V. D., Craddock, R. C., Das, S., Duff, E. P., et al. (2016). The brain imaging data structure, a format for organizing and describing outputs of neuroimaging experiments. *Scientific Data*, 3, 160044. [doi:10.1038/sdata.2016.44](https://doi.org/10.1038/sdata.2016.44) | Dataset layout; metadata checks (`quality.py`) |
| Pernet, C. R., Appelhoff, S., Gorgolewski, K. J., Flandin, G., Phillips, C., Delorme, A., & Oostenveld, R. (2019). EEG-BIDS, an extension to the brain imaging data structure for electroencephalography. *Scientific Data*, 6, 103. [doi:10.1038/s41597-019-0104-8](https://doi.org/10.1038/s41597-019-0104-8) | EEG metadata checks (`quality.py`) |

## MRI artefact removal

| Reference | Used in |
|---|---|
| Allen, P. J., Josephs, O., & Turner, R. (2000). A method for removing imaging artifact from continuous EEG recorded during functional MRI. *NeuroImage*, 12(2), 230–239. [doi:10.1006/nimg.2000.0599](https://doi.org/10.1006/nimg.2000.0599) | Scanner (gradient) artefact subtraction (`mr_artifacts.py`) |
| Allen, P. J., Polizzi, G., Krakow, K., Fish, D. R., & Lemieux, L. (1998). Identification of EEG events in the MR scanner: the problem of pulse artifact and a method for its subtraction. *NeuroImage*, 8(3), 229–239. [doi:10.1006/nimg.1998.0361](https://doi.org/10.1006/nimg.1998.0361) | Heartbeat (ballistocardiogram) artefact subtraction (`mr_artifacts.py`) |
| Niazy, R. K., Beckmann, C. F., Iannetti, G. D., Brady, J. M., & Smith, S. M. (2005). Removal of FMRI environment artifacts from EEG data using optimal basis sets. *NeuroImage*, 28(3), 720–737. [doi:10.1016/j.neuroimage.2005.06.067](https://doi.org/10.1016/j.neuroimage.2005.06.067) | Planned next cleaning step (residual artefact) |

## Heartbeat (R-peak) detection

| Reference | Used in |
|---|---|
| Gramfort, A., Luessi, M., Larson, E., Engemann, D. A., Strohmeier, D., Brodbeck, C., et al. (2013). MEG and EEG data analysis with MNE-Python. *Frontiers in Neuroscience*, 7, 267. [doi:10.3389/fnins.2013.00267](https://doi.org/10.3389/fnins.2013.00267) | `find_ecg_events`: the standard detector of the *cleaned (MNE)* arm; also all EEG input/output and filtering |
| Pan, J., & Tompkins, W. J. (1985). A real-time QRS detection algorithm. *IEEE Transactions on Biomedical Engineering*, BME-32(3), 230–236. [doi:10.1109/TBME.1985.325532](https://doi.org/10.1109/TBME.1985.325532) | Detector comparison (`compare_qrs_detectors.py`) |
| Hamilton, P. (2002). Open source ECG analysis. *Computers in Cardiology*, 29, 101–104. [doi:10.1109/CIC.2002.1166717](https://doi.org/10.1109/CIC.2002.1166717) | Detector comparison |
| Elgendi, M., Jonkman, M., & De Boer, F. (2010). Frequency bands effects on QRS detection. *Proceedings of the 3rd International Conference on Bio-inspired Systems and Signal Processing (BIOSIGNALS)*, 428–431. [doi:10.5220/0002742704280431](https://doi.org/10.5220/0002742704280431) | Detector comparison |
| Engelse, W. A. H., & Zeelenberg, C. (1979). A single scan algorithm for QRS-detection and feature extraction. *Computers in Cardiology*, 6, 37–42. (No DOI registered.) | Detector comparison (original of the modified Engzee detector) |
| Lourenço, A., Silva, H., Leite, P., Lourenço, R., & Fred, A. (2012). Real time electrocardiogram segmentation for finger based ECG biometrics. *Proceedings of BIOSIGNALS 2012*, 49–54. [doi:10.5220/0003777300490054](https://doi.org/10.5220/0003777300490054) | Detector comparison (modified Engzee) |
| Christov, I. I. (2004). Real time electrocardiogram QRS detection using combined adaptive threshold. *BioMedical Engineering OnLine*, 3, 28. [doi:10.1186/1475-925X-3-28](https://doi.org/10.1186/1475-925X-3-28) | Detector comparison |
| Brammer, J. C. (2020). biopeaks: a graphical user interface for feature extraction from heart- and breathing biosignals. *Journal of Open Source Software*, 5(54), 2621. [doi:10.21105/joss.02621](https://doi.org/10.21105/joss.02621) | Validation reference given by NeuroKit2 for its default ("neurokit") detector, used in the comparison |
| Kim, K. H., Yoon, H. W., & Park, H. W. (2004). Improved ballistocardiac artifact removal from the electroencephalogram recorded in fMRI. *Journal of Neuroscience Methods*, 135(1–2), 193–203. [doi:10.1016/j.jneumeth.2003.12.016](https://doi.org/10.1016/j.jneumeth.2003.12.016) | Teager-energy detector in the comparison |
| Makowski, D., Pham, T., Lau, Z. J., Brammer, J. C., Lespinasse, F., Pham, H., Schölzel, C., & Chen, S. H. A. (2021). NeuroKit2: A Python toolbox for neurophysiological signal processing. *Behavior Research Methods*, 53(4), 1689–1696. [doi:10.3758/s13428-020-01516-y](https://doi.org/10.3758/s13428-020-01516-y) | Implementations of the published detectors above |

## Data-quality control

| Reference | Used in |
|---|---|
| Bigdely-Shamlo, N., Mullen, T., Kothe, C., Su, K.-M., & Robbins, K. A. (2015). The PREP pipeline: standardized preprocessing for large-scale EEG analysis. *Frontiers in Neuroinformatics*, 9, 16. [doi:10.3389/fninf.2015.00016](https://doi.org/10.3389/fninf.2015.00016) | Bad-channel detection (`quality.py`, via PyPREP) |
| Jas, M., Engemann, D. A., Bekhti, Y., Raimondo, F., & Gramfort, A. (2017). Autoreject: Automated artifact rejection for MEG and EEG data. *NeuroImage*, 159, 417–429. [doi:10.1016/j.neuroimage.2017.06.030](https://doi.org/10.1016/j.neuroimage.2017.06.030) | Epoch rejection threshold (`quality.py`) |
| Tong, S., Bezerianos, A., Paul, J., Zhu, Y., & Thakor, N. (2001). Removal of ECG interference from the EEG recordings in small animals using independent component analysis. *Journal of Neuroscience Methods*, 108(1), 11–17. [doi:10.1016/S0165-0270(01)00366-1](https://doi.org/10.1016/S0165-0270(01)00366-1) | INPS metric for heartbeat-artefact removal (`quality.py`, `compare_qrs_detectors.py`) |
| Abreu, R., Leite, M., Jorge, J., Grouiller, F., van der Zwaag, W., Leal, A., & Figueiredo, P. (2016). Ballistocardiogram artifact correction taking into account physiological signal preservation in simultaneous EEG-fMRI. *NeuroImage*, 135, 45–63. [doi:10.1016/j.neuroimage.2016.03.034](https://doi.org/10.1016/j.neuroimage.2016.03.034) | Rationale for checking physiological signal preservation |
| Gallego-Rudolf, J., Corsi-Cabrera, M., Concha, L., Ricardo-Garcell, J., & Pasaye-Alcaraz, E. (2022). Preservation of EEG spectral power features during simultaneous EEG-fMRI. *Frontiers in Neuroscience*, 16, 951321. [doi:10.3389/fnins.2022.951321](https://doi.org/10.3389/fnins.2022.951321) | Alpha-contrast preservation check (`compare_arms.py`) |
| Perrin, F., Pernier, J., Bertrand, O., & Echallier, J. F. (1989). Spherical splines for scalp potential and current density mapping. *Electroencephalography and Clinical Neurophysiology*, 72(2), 184–187. [doi:10.1016/0013-4694(89)90180-6](https://doi.org/10.1016/0013-4694(89)90180-6) | Bad-channel interpolation (`stages.py`) |
| Berry, R. B., et al. *The AASM Manual for the Scoring of Sleep and Associated Events*. American Academy of Sleep Medicine. (No DOI.) | Mastoid reference convention for sleep EEG (`stages.py`) |

## Signal processing and features

| Reference | Used in |
|---|---|
| Welch, P. (1967). The use of fast Fourier transform for the estimation of power spectra: a method based on time averaging over short, modified periodograms. *IEEE Transactions on Audio and Electroacoustics*, 15(2), 70–73. [doi:10.1109/TAU.1967.1161901](https://doi.org/10.1109/TAU.1967.1161901) | All power spectra and band powers (`spectral.py`, `quality.py`) |
| Hjorth, B. (1970). EEG analysis based on time domain properties. *Electroencephalography and Clinical Neurophysiology*, 29(3), 306–310. [doi:10.1016/0013-4694(70)90143-4](https://doi.org/10.1016/0013-4694(70)90143-4) | Hjorth mobility and complexity features (`spectral.py`) |
| Vallat, R., & Walker, M. P. (2021). An open-source, high-performance tool for automated sleep staging. *eLife*, 10, e70092. [doi:10.7554/eLife.70092](https://doi.org/10.7554/eLife.70092) | Reference design for sleep-staging features (band powers, ratios, Hjorth parameters, temporal context); its code is not used |

## Machine learning and statistics

| Reference | Used in |
|---|---|
| Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830. (JMLR assigns no DOI.) [jmlr.org/papers/v12/pedregosa11a](https://jmlr.org/papers/v12/pedregosa11a.html) | Logistic regression, gradient boosting, metrics (`compare_arms.py`) |
| Friedman, J. H. (2001). Greedy function approximation: a gradient boosting machine. *The Annals of Statistics*, 29(5), 1189–1232. [doi:10.1214/aos/1013203451](https://doi.org/10.1214/aos/1013203451) | Gradient-boosted trees (`compare_arms.py`) |
| Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*, 20(1), 37–46. [doi:10.1177/001316446002000104](https://doi.org/10.1177/001316446002000104) | Cohen's kappa, the agreement score |
| Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159–174. [doi:10.2307/2529310](https://doi.org/10.2307/2529310) | Kappa agreement bands and table colours (`participant_table.py`) |
| Wilcoxon, F. (1945). Individual comparisons by ranking methods. *Biometrics Bulletin*, 1(6), 80–83. [doi:10.2307/3001968](https://doi.org/10.2307/3001968) | Paired comparisons between arms (`compare_arms.py`) |
| Spearman, C. (1904). The proof and measurement of association between two things. *The American Journal of Psychology*, 15(1), 72–101. [doi:10.2307/1412159](https://doi.org/10.2307/1412159) | Rank correlation between heart rate and predictions in the residual-heartbeat check (`hr_check.py`) |
| Efron, B. (1979). Bootstrap methods: another look at the jackknife. *The Annals of Statistics*, 7(1), 1–26. [doi:10.1214/aos/1176344552](https://doi.org/10.1214/aos/1176344552) | Bootstrap 95% confidence intervals (`compare_arms.py`) |

## Scientific software

| Reference | Used in |
|---|---|
| Harris, C. R., Millman, K. J., van der Walt, S. J., Gommers, R., Virtanen, P., Cournapeau, D., et al. (2020). Array programming with NumPy. *Nature*, 585(7825), 357–362. [doi:10.1038/s41586-020-2649-2](https://doi.org/10.1038/s41586-020-2649-2) | Throughout |
| Virtanen, P., Gommers, R., Oliphant, T. E., Haberland, M., Reddy, T., Cournapeau, D., et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. *Nature Methods*, 17(3), 261–272. [doi:10.1038/s41592-019-0686-2](https://doi.org/10.1038/s41592-019-0686-2) | Filters, spectra, statistics |
| McKinney, W. (2010). Data structures for statistical computing in Python. *Proceedings of the 9th Python in Science Conference*, 56–61. [doi:10.25080/Majora-92bf1922-00a](https://doi.org/10.25080/Majora-92bf1922-00a) | pandas: tables throughout |
| Hunter, J. D. (2007). Matplotlib: a 2D graphics environment. *Computing in Science & Engineering*, 9(3), 90–95. [doi:10.1109/MCSE.2007.55](https://doi.org/10.1109/MCSE.2007.55) | All figures |
| PyPREP (software): Appelhoff, S., et al. [github.com/sappelhoff/pyprep](https://github.com/sappelhoff/pyprep) | Python implementation of PREP (`quality.py`) |
| NiBabel (software): Brett, M., et al. [nipy.org/nibabel](https://nipy.org/nibabel/) | Reading MRI files (`example_figures.py`) |
