# Speech2text for Ukrainian language

This STT system trained using [Kaldi](https://github.com/kaldi-asr/kaldi) framework.  
System contains of g2p model and kaldi training recipe.

## Current project state:
**g2p**: built on basic rules and will be further improved.  
[G2P function](utils/g2p.py)  
TODO: try https://github.com/sequitur-g2p/sequitur-g2p

**acoustic model**: trained on X hour of voxforge data.  
[training recipe](kaldi_baseline/run.sh)  
As it is a baseline, current purpose is just to make it work.


## Metrics results

| Model         | LM order      | train/test, hours | WAcc, %|
| ------------- |:-------------:| ----------------: |-------:|
| mono          | 2             |  1 / 0.1          |4     % |
| mono          | 2             |  5 / 1            |9     % |


## Data source

| Source                | link                                              |
| --------------------- |---------------------------------------------------|
| voxforge              | http://www.repository.voxforge1.org/downloads/uk/ |
| youtube (in progress) | [youtube-data.xlsx](data/youtube-data.xlsx)  |

## How to run
* build [Kaldi](https://github.com/kaldi-asr/kaldi) from source
* prepare data with [sample notebook](prepare_voxforge_data.ipynb)  
* prepare kaldi project with [project notebook](prepare_voxforge_kaldi.ipynb)  
* make changes to [configs](kaldi_baseline/conf/mfcc.conf) and [recipe](kaldi_baseline/run.sh)
* cross fingers and hope it will run w/o errors :-)  

## How to use:
* Place model to appropriate folder in kaldi project  
* fill [config.py](config.py)  
* run [stt_decode.py](utils/stt_decode.py) with file_path argument
* if necessary, modify scoring script [score.sh](kaldi_baseline/local/score.sh)  
