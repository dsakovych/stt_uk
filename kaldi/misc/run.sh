#!/bin/bash

. ./path.sh || exit 1
. ./cmd.sh || exit 1

nj=6
stage=0

lm_order=2
oovSymbol='<UNK>'
lexicon=data/local/lexicon.txt
# Note: --boost-silence $boost_sil   is not used

numLeavesTri1=2000
numGaussTri1=25000
numLeavesTri2=3000
numGaussTri2=35000
numLeavesTri3=4000
numGaussTri3=50000
numLeavesTri4=5000
numGaussTri4=70000
numLeavesTri5=6000
numGaussTri5=90000

# Data prepare
if [ $stage -le 0 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Preparing data on" `date`
  echo ---------------------------------------------------------------------
  echo
  # Needs to be prepared by hand (or using self written scripts):
  #
  # spk2gender  [<speaker-id> <gender>]
  # wav.scp     [<uterranceID> <full_path_to_audio_file>]
  # text        [<uterranceID> <text_transcription>]
  # utt2spk     [<uterranceID> <speakerID>]
  # corpus.txt  [<text_transcription>]
  # Making spk2utt files
  rm -rf data/train/spk2utt data/test/spk2utt

  utils/utt2spk_to_spk2utt.pl data/train/utt2spk > data/train/spk2utt
  utils/utt2spk_to_spk2utt.pl data/test/utt2spk > data/test/spk2utt
fi


# Language model
if [ $stage -le 1 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Training language model on" `date`
  echo ---------------------------------------------------------------------
  echo
  # Needs to be prepared by hand (or using self written scripts):
  #
  # lexicon.txt           [<word> <phone 1> <phone 2> ...]
  # nonsilence_phones.txt [<phone>]
  # silence_phones.txt    [<phone>]
  # optional_silence.txt  [<phone>]
  rm -rf data/local/lang data/lang data/local/tmp data/local/dict/lexiconp.txt

  mkdir -p data/lang
  if [[ ! -f data/lang/L.fst || data/lang/L.fst -ot $lexicon ]]; then
    echo
    echo ---------------------------------------------------------------------
    echo "Creating L.fst etc in data/lang on" `date`
    echo ---------------------------------------------------------------------
    echo
    utils/prepare_lang.sh \
      --share-silence-phones true \
      data/local $oovSymbol data/local/lang data/lang
  fi

  if [[ ! -f data/srilm/lm.gz || data/srilm/lm.gz -ot data/train/text ]]; then
    echo
    echo ---------------------------------------------------------------------
    echo "Training SRILM language models on" `date`
    echo ---------------------------------------------------------------------
    echo
    local/train_lms_srilm.sh  --oov-symbol "$oovSymbol"\
                              --train-text data/train/text data data/srilm
  fi

  if [[ ! -f data/lang/G.fst || data/lang/G.fst -ot data/srilm/lm.gz ]]; then
    echo
    echo ---------------------------------------------------------------------
    echo "Creating G.fst on " `date`
    echo ---------------------------------------------------------------------
    echo
    local/arpa2G.sh data/srilm/lm.gz data/lang data/lang
  fi

fi


# Extract audio features
if [ $stage -le 2 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Making feature extraction on " `date`
  echo ---------------------------------------------------------------------
  echo
  mfccdir=mfcc
  rm -rf data/train/cmvn.scp data/train/feats.scp data/train/split* \
         data/test/cmvn.scp data/test/feats.scp data/test/split* \
         mfcc
  utils/validate_data_dir.sh data/train     # script for checking prepared data - here: for data/train directory
  utils/validate_data_dir.sh data/test     # script for checking prepared data - here: for data/test directory
  utils/fix_data_dir.sh data/train          # tool for data proper sorting if needed - here: for data/train directory
  utils/fix_data_dir.sh data/test          # tool for data proper sorting if needed - here: for data/test directory
  steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" data/train exp/make_mfcc/train $mfccdir
  steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" data/test exp/make_mfcc/test $mfccdir
  steps/compute_cmvn_stats.sh data/train exp/make_mfcc/train $mfccdir
  steps/compute_cmvn_stats.sh data/test exp/make_mfcc/test $mfccdir
fi


# train mono
if [ $stage -le 3 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (small) monophone training in exp/mono on " `date`
  echo ---------------------------------------------------------------------
  echo
  rm -rf exp/mono
  steps/train_mono.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/mono  || exit 1
fi


# train tri1
if [ $stage -le 4 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (small) triphone training in exp/tri1 on" `date`
  echo ---------------------------------------------------------------------
  echo
  rm -rf exp/mono_ali exp/tri
  steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/mono exp/mono_ali || exit 1
  steps/train_deltas.sh --cmd "$train_cmd" $numLeavesTri1 $numGaussTri1 data/train data/lang exp/mono_ali exp/tri1 || exit 1
fi


# train tri2
if [ $stage -le 5 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (medium) triphone training in exp/tri2 on" `date`
  echo ---------------------------------------------------------------------
  echo
  rm -rf exp/tri1_ali exp/tri2 data/local/dictp/tri2 data/local/langp/tri2 data/langp/tri2
  steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/tri1 exp/tri1_ali || exit 1
  steps/train_deltas.sh --cmd "$train_cmd" $numLeavesTri2 $numGaussTri2 data/train data/lang exp/tri1_ali exp/tri2 || exit 1
  local/reestimate_langp.sh --cmd "$train_cmd" --unk "$oovSymbol" \
                            data/train data/lang data/local/ \
                            exp/tri2 data/local/dictp/tri2 data/local/langp/tri2 data/langp/tri2
fi


# train tri3
if [ $stage -le 6 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (full) triphone training in exp/tri3 on" `date`
  echo ---------------------------------------------------------------------
  echo
  rm -rf exp/tri2_ali exp/tri3 data/local/dictp/tri3 data/local/langp/tri3 data/langp/tri3
  steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/tri2 exp/tri2_ali || exit 1
  steps/train_deltas.sh --cmd "$train_cmd" $numLeavesTri3 $numGaussTri3 data/train data/langp/tri2 exp/tri2_ali exp/tri3 || exit 1
  local/reestimate_langp.sh --cmd "$train_cmd" --unk "$oovSymbol" \
                            data/train data/lang data/local/ \
                            exp/tri3 data/local/dictp/tri3 data/local/langp/tri3 data/langp/tri3
fi


# train tri4
if [ $stage -le 7 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (lda_mllt) triphone training in exp/tri4 on" `date`
  echo ---------------------------------------------------------------------
  echo
  rm -rf exp/tri3_ali exp/tri4 data/local/dictp/tri4 data/local/langp/tri4 data/langp/tri4
  steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/langp/tri3 exp/tri3 exp/tri3_ali || exit 1
  steps/train_lda_mllt.sh --cmd "$train_cmd" $numLeavesTri4 $numGaussTri4 data/train data/langp/tri3 exp/tri3_ali exp/tri4 || exit 1
  local/reestimate_langp.sh --cmd "$train_cmd" --unk "$oovSymbol" \
                            data/train data/lang data/local \
                            exp/tri4 data/local/dictp/tri4 data/local/langp/tri4 data/langp/tri4
fi


# train tri5
if [ $stage -le 8 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (SAT) triphone training in exp/tri5 on" `date`
  echo ---------------------------------------------------------------------
  echo
  rm -rf exp/tri4_ali exp/tri5 data/local/dictp/tri5 data/local/langp/tri5 data/langp/tri5
  steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/langp/tri4 exp/tri4 exp/tri4_ali || exit 1
  steps/train_sat.sh --cmd "$train_cmd" $numLeavesTri5 $numGaussTri5 data/train data/langp/tri4 exp/tri4_ali exp/tri5 || exit 1
  local/reestimate_langp.sh --cmd "$train_cmd" --unk "$oovSymbol" \
                            data/train data/lang data/local \
                            exp/tri5 data/local/dictp/tri5 data/local/langp/tri5 data/langp/tri5
fi


if [ $stage -le 9 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting exp/tri5_ali on" `date`
  echo ---------------------------------------------------------------------
  echo
  rm -rf exp/tri5_ali data/local/dictp/tri5_ali data/local/langp/tri5_ali data/langp/tri5_ali
  steps/align_fmllr.sh --nj $nj --cmd "$train_cmd" data/train data/langp/tri5 exp/tri5 exp/tri5_ali || exit 1
  local/reestimate_langp.sh --cmd "$train_cmd" --unk "$oovSymbol" \
                            data/train data/lang data/local \
                            exp/tri5_ali data/local/dictp/tri5_ali data/local/langp/tri5_ali data/langp/tri5_ali
fi


if [ $stage -le 10 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Evaluating exp/tri5_ali on" `date`
  echo ---------------------------------------------------------------------
  echo
  cp -R data/langp/tri5_ali/ data/langp_test
  cp data/lang/G.fst data/langp_test

  utils/mkgraph.sh data/langp_test exp/tri5_ali exp/tri5_ali/graph || exit 1
  steps/decode.sh --config conf/decode.config --nj $nj --cmd "$decode_cmd" exp/tri5_ali/graph data/test exp/tri5_ali/decode
fi


echo
echo "===== run.sh script is finished ====="
echo