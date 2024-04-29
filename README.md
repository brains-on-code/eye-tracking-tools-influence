# Data Analysis Tools Affect Outcomes of Eye-Tracking Studies

This repository contains the replication package for our study "Data Analysis Tools Affect Outcomes of Eye-Tracking Studies".
We provide the extracted data and the extraction form of the systematic mapping study as well as the scripts that were used to perform the three case studies.

---

# SMS

## Structure

- [extracted_data.csv](extracted_data.csv) contains the data that was extracted from the 97 papers during the SMS study.
- [extraction_table.csv](extraction_table.csv) contains the extraction table that was used to extract the data during the SMS study.


---

# Case Studies

## Requirements

You will need the three data sets that were used for the study.

EMIP dataset: [link](https://osf.io/53kts/) (to be saved in [data/StudyEMIP](data/StudyEMIP)) \
Sharafi et al.: [link](https://web.eecs.umich.edu/~weimerw/fmri-resources/2018-Eye-Tracking-Data.zip) (to be saved in [data/StudySharafi](data/StudySharafi)) \
Peitek et al.: 
- [repository](https://github.com/brains-on-code/NoviceVsExpert) (Repository to be cloned in [data/StudyPeitek](data/StudyPeitek))
- [data](https://osf.io/4hjbd/) (Raw data that needs to be saved in 'data/StudyPeitek/dataEvaluation/data/') 



Download these replication packages and save them in the corresponding folder in the data folder.

Additionally, you will need:

```
Python 3/ Anaconda
 - Jupyter
 - requirements.txt
```

## Top Level Structure

### Requirements

The **requirements.txt** provides all the dependencies for the project.
It is recommended to use a separated environment to run the project. One can create suche a virtualenv with the command:

```properties
$ conda create -n your_env_name python=3.8
$ conda activate your_env_name
$ conda install pip
$ pip install -r requirements.txt
```
### Structure

- In [StudyEMIP](StudyEMIP), one can find the files for running the case study on the EMIP dataset, where we performed the same data analysis as [Aljehane et al .](https://doi.org/10.1145/3591135)
- In [StudyPeitek](StudyPeitek), one can find the files for running the case study on the replication package of [Peitek et al.](https://doi.org/10.1145/3540250.3549084) 
- In [StudySharafi](StudySharafi), one can find the files for running the case study on the replication package of [Sharafi et al.](http://dx.doi.org/10.1145/3434643) 

---

## Preprocessing

Only Peitek et al. needs preprocessing.
To do so, navigate into the dataEvaluation folder of StudyPeitek and execute the Preprocessing_.. jupyter notebooks.
If there are multiple notebooks with the same number, choose the one that has "PAPER" in it.
Once you have completed the Preprocessing05_PAPER_I2MC_fixxation_detection.ipynb jupyter notebook, you are finished with the data preprocessing.

## Data Evaluation

To start the data evaluation of Sharafi et al. or the EMIP dataset, enter the corresponding folder and execute the corresponding jupyter notebook.

As Peitek et al. provided their own jupyter notebooks to replicate the study, you will first need to execute [Analysis.ipynb](StudyPeitek/Analysis.ipynb).
This jupyter notebook will calculate the fixations with PyGaze and Ogama.

Afterwards, you will need to execute [RQ1_PAPER_Eyetracking_ogama.ipynb](StudyPeitek/RQ1_PAPER_Eyetracking_ogama.ipynb) and [RQ1_PAPER_Eyetracking_pygaze.ipynb](StudyPeitek/RQ1_PAPER_Eyetracking_pygaze.ipynb).
[RQ1_PAPER_Eyetracking.ipynb](StudyPeitek/RQ1_PAPER_Eyetracking.ipynb) can be executed achieve the original results, which may be a bit different than the original, as a non-deterministic fixation algorithm was used.

Once those are finished, you will need to run [ResultsAnalysis.ipynb](StudyPeitek/ResultsAnalysis.ipynb), which will yield the comparison of the experimental results between the different analysis tools.
