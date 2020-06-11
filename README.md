# Speech2text for Ukrainian language

This STT system trained using [Kaldi](https://github.com/kaldi-asr/kaldi) framework.  
System contains of g2p model and kaldi training recipe.

## Current project state:
**g2p**: https://github.com/kotestyle/g2p_uk  
g2p model was trained separately with tf. Details in its repo.

**asr model**: trained on 84 hour of voxforge and librivox data.  
[training recipe](kaldi/misc/run.sh)

Language model: **SRILM**  
Audio features: **MFCC** and **CMVN**  
Acoustic model: **HMM-GMM**  
Training:  **Delta+delta-delta**, **LDA-MLLT**, **SAT**  
Alignment: **fMLLR** 


## Metrics results

| Model                   | LM order (SRILM)| train/test, hours | WAcc, %|
| ----------------------- |:---------------:| ----------------: |-------:|
| mono                    | 2               |  1 / 0.1          |4     % |
| mono                    | 2               |  5 / 1            |9     % |
| Tri5 (LDA + MLLT + SAT) | 2-3             | 83 / 1            |31.13 % |


## Data source

| Source                | link                                                      |
| --------------------- |-----------------------------------------------------------|
| voxforge              | http://www.repository.voxforge1.org/downloads/uk/         |
| librivox              | https://www.caito.de/2019/01/the-m-ailabs-speech-dataset/ |
| youtube (in progress) | [youtube-data.xlsx](data/youtube-data.xlsx)               |

## How to run
* build [Kaldi](https://github.com/kaldi-asr/kaldi) from source
* prepare voxforge data with [sample notebook](notebooks/prepare_VoxForge.ipynb)
* prepare librivox data with [sample notebook](notebooks/prepare_Librivox.ipynb)
* prepare kaldi project with [project notebook](notebooks/prepare_kaldi_project.ipynb)  
* make changes to [configs](kaldi/misc/conf/mfcc.conf) and [recipe](kaldi/misc/run.sh)
* cross fingers and hope it will run w/o errors :-)  

## How to use:
* Place model to appropriate folder in kaldi project  
* fill [config.py](config.py)  
* run [decode_kaldi.py](utils/decode_kaldi.py) with file_path argument
