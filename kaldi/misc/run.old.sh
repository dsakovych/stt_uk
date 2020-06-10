#!/bin/bash

. ./path.sh || exit 1
. ./cmd.sh || exit 1

nj=1
stage=0

lm_order=2
oovSymbol='<UNK>'
lexicon=data/local/lexicon.txt

# Removing previously created data (from last run.sh execution)
rm -rf exp mfcc data/train/spk2utt data/train/cmvn.scp data/train/feats.scp data/train/split* data/test/spk2utt \
       data/test/cmvn.scp data/test/feats.scp data/test/split* data/local/lang data/lang data/local/tmp data/local/dict/lexiconp.txt

# Feature extraction
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
  utils/utt2spk_to_spk2utt.pl data/train/utt2spk > data/train/spk2utt
  utils/utt2spk_to_spk2utt.pl data/test/utt2spk > data/test/spk2utt
fi

# Language model
#if [ $stage -le 1 ]; then
#  echo
#  echo ---------------------------------------------------------------------
#  echo "Training language model"
#  echo ---------------------------------------------------------------------
#  echo
  # Needs to be prepared by hand (or using self written scripts):
  #
  # lexicon.txt           [<word> <phone 1> <phone 2> ...]
  # nonsilence_phones.txt [<phone>]
  # silence_phones.txt    [<phone>]
  # optional_silence.txt  [<phone>]
  # Preparing language data
#  utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang
#  utils/prepare_lang.sh  --share-silence-phones true data/local/dict $oovSymbol data/local/lang data/lang
#
#
#  loc=`which ngram-count`;
#  if [ -z $loc ]; then
#    if uname -a | grep 64 >/dev/null; then
#      sdir=$KALDI_ROOT/tools/srilm/bin/i686-m64
#    else
#      sdir=$KALDI_ROOT/tools/srilm/bin/i686
#    fi
#    if [ -f $sdir/ngram-count ]; then
#      echo "Using SRILM language modelling tool from $sdir"
#      export PATH=$PATH:$sdir
#    else
#      echo "SRILM toolkit is probably not installed."
#      exit 1
#    fi
#  fi
#  local=data/local
#  mkdir $local/tmp
#  ngram-count -order $lm_order -write-vocab $local/tmp/vocab-full.txt -wbdiscount -text $local/corpus.txt -lm $local/tmp/lm.arpa
#fi
#
#if [ $stage -le 2 ]; then
#  echo
#  echo ---------------------------------------------------------------------
#  echo "Making G.fst"
#  echo ---------------------------------------------------------------------
#  echo
#  lang=data/lang
#  arpa2fst --disambig-symbol=#0 --read-symbol-table=$lang/words.txt $local/tmp/lm.arpa $lang/G.fst
#fi



mkdir -p data/lang
if [[ ! -f data/lang/L.fst || data/lang/L.fst -ot $lexicon ]]; then
  echo ---------------------------------------------------------------------
  echo "Creating L.fst etc in data/lang on" `date`
  echo ---------------------------------------------------------------------
  utils/prepare_lang.sh \
    --share-silence-phones true \
    data/local $oovSymbol data/local/lang data/lang
fi

if [[ ! -f data/srilm/lm.gz || data/srilm/lm.gz -ot data/train/text ]]; then
  echo ---------------------------------------------------------------------
  echo "Training SRILM language models on" `date`
  echo ---------------------------------------------------------------------
  local/train_lms_srilm.sh  --oov-symbol "$oovSymbol"\
    --train-text data/train/text data data/srilm
fi

if [[ ! -f data/lang/G.fst || data/lang/G.fst -ot data/srilm/lm.gz ]]; then
  echo ---------------------------------------------------------------------
  echo "Creating G.fst on " `date`
  echo ---------------------------------------------------------------------
  local/arpa2G.sh data/srilm/lm.gz data/lang data/lang
fi







if [ $stage -le 3 ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Feature extraction"
  echo ---------------------------------------------------------------------
  echo
  mfccdir=mfcc
  utils/validate_data_dir.sh data/train     # script for checking prepared data - here: for data/train directory
  utils/validate_data_dir.sh data/test     # script for checking prepared data - here: for data/test directory
  utils/fix_data_dir.sh data/train          # tool for data proper sorting if needed - here: for data/train directory
  utils/fix_data_dir.sh data/test          # tool for data proper sorting if needed - here: for data/test directory
  steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" data/train exp/make_mfcc/train $mfccdir
  steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" data/test exp/make_mfcc/test $mfccdir
  steps/compute_cmvn_stats.sh data/train exp/make_mfcc/train $mfccdir
  steps/compute_cmvn_stats.sh data/test exp/make_mfcc/test $mfccdir
fi

#if [ $stage -le 4 ]; then
#  echo
#  echo ---------------------------------------------------------------------
#  echo "Starting monophone training in exp/mono"
#  echo ---------------------------------------------------------------------
#  echo
#  steps/train_mono.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/mono  || exit 1
#  touch exp/mono/.done
#fi













#mkdir -p data/local
#if [[ ! -f $lexicon || $lexicon -ot "$lexicon_file" ]]; then
#  echo ---------------------------------------------------------------------
#  echo "Preparing lexicon in data/local on" `date`
#  echo ---------------------------------------------------------------------
#  local/make_lexicon_subset.sh $train_data_dir/transcription $lexicon_file data/local/filtered_lexicon.txt
#  local/prepare_lexicon.pl  --phonemap "$phoneme_mapping" \
#    $lexiconFlags data/local/filtered_lexicon.txt data/local
#fi

mkdir -p data/lang
if [[ ! -f data/lang/L.fst || data/lang/L.fst -ot $lexicon ]]; then
  echo ---------------------------------------------------------------------
  echo "Creating L.fst etc in data/lang on" `date`
  echo ---------------------------------------------------------------------
  utils/prepare_lang.sh \
    --share-silence-phones true \
    data/local $oovSymbol data/local/tmp.lang data/lang
fi

if [[ ! -f data/train/wav.scp || data/train/wav.scp -ot "$train_data_dir" ]]; then
  echo ---------------------------------------------------------------------
  echo "Preparing acoustic training lists in data/train on" `date`
  echo ---------------------------------------------------------------------
  mkdir -p data/train
  local/prepare_acoustic_training_data.pl \
    --vocab $lexicon --fragmentMarkers \-\*\~ \
    $train_data_dir data/train > data/train/skipped_utts.log
fi

if [[ ! -f data/srilm/lm.gz || data/srilm/lm.gz -ot data/train/text ]]; then
  echo ---------------------------------------------------------------------
  echo "Training SRILM language models on" `date`
  echo ---------------------------------------------------------------------
  local/train_lms_srilm.sh  --oov-symbol "$oovSymbol"\
    --train-text data/train/text data data/srilm
fi

if [[ ! -f data/lang/G.fst || data/lang/G.fst -ot data/srilm/lm.gz ]]; then
  echo ---------------------------------------------------------------------
  echo "Creating G.fst on " `date`
  echo ---------------------------------------------------------------------
  local/arpa2G.sh data/srilm/lm.gz data/lang data/lang
fi


































echo
echo ---------------------------------------------------------------------
echo "Preparing data"
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
utils/utt2spk_to_spk2utt.pl data/train/utt2spk > data/train/spk2utt
utils/utt2spk_to_spk2utt.pl data/test/utt2spk > data/test/spk2utt

# Needs to be prepared by hand (or using self written scripts):
#
# lexicon.txt           [<word> <phone 1> <phone 2> ...]
# nonsilence_phones.txt [<phone>]
# silence_phones.txt    [<phone>]
# optional_silence.txt  [<phone>]
# Preparing language data
utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang


echo
echo ---------------------------------------------------------------------
echo "Feature extraction"
echo ---------------------------------------------------------------------
echo
# Making feats.scp files
mfccdir=mfcc
# Uncomment and modify arguments in scripts below if you have any problems with data sorting
utils/validate_data_dir.sh data/train     # script for checking prepared data - here: for data/train directory
utils/validate_data_dir.sh data/test     # script for checking prepared data - here: for data/test directory
utils/fix_data_dir.sh data/train          # tool for data proper sorting if needed - here: for data/train directory
utils/fix_data_dir.sh data/test          # tool for data proper sorting if needed - here: for data/test directory
steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" data/train exp/make_mfcc/train $mfccdir
steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" data/test exp/make_mfcc/test $mfccdir
# Making cmvn.scp files
steps/compute_cmvn_stats.sh data/train exp/make_mfcc/train $mfccdir
steps/compute_cmvn_stats.sh data/test exp/make_mfcc/test $mfccdir


echo
echo ---------------------------------------------------------------------
echo "Prepare language data"
echo ---------------------------------------------------------------------
echo
# Needs to be prepared by hand (or using self written scripts):
#
# lexicon.txt           [<word> <phone 1> <phone 2> ...]
# nonsilence_phones.txt [<phone>]
# silence_phones.txt    [<phone>]
# optional_silence.txt  [<phone>]
# Preparing language data
utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang

echo
echo ---------------------------------------------------------------------
echo "Creating language model"
echo ---------------------------------------------------------------------
echo
loc=`which ngram-count`;
if [ -z $loc ]; then
  if uname -a | grep 64 >/dev/null; then
    sdir=$KALDI_ROOT/tools/srilm/bin/i686-m64
  else
    sdir=$KALDI_ROOT/tools/srilm/bin/i686
  fi
  if [ -f $sdir/ngram-count ]; then
    echo "Using SRILM language modelling tool from $sdir"
    export PATH=$PATH:$sdir
  else
    echo "SRILM toolkit is probably not installed."
    exit 1
  fi
fi
local=data/local
mkdir $local/tmp
ngram-count -order $lm_order -write-vocab $local/tmp/vocab-full.txt -wbdiscount -text $local/corpus.txt -lm $local/tmp/lm.arpa

echo
echo ---------------------------------------------------------------------
echo "Making G.fst"
echo ---------------------------------------------------------------------
echo
lang=data/lang
arpa2fst --disambig-symbol=#0 --read-symbol-table=$lang/words.txt $local/tmp/lm.arpa $lang/G.fst


if [ ! -f exp/mono/.done ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (small) monophone training in exp/mono"
  echo ---------------------------------------------------------------------
  echo
  steps/train_mono.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/mono  || exit 1
  touch exp/mono/.done
fi

if [ ! -f exp/tri1/.done ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (small) triphone training in exp/tri1"
  echo ---------------------------------------------------------------------
  echo
  steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/mono exp/mono_ali || exit 1
  steps/train_deltas.sh --cmd "$train_cmd" 2000 30000 data/train data/lang exp/mono_ali exp/tri1 || exit 1
  touch exp/tri1/.done
fi

if [ ! -f exp/tri2/.done ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (medium) triphone training in exp/tri2"
  echo ---------------------------------------------------------------------
  echo
  steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/tri1 exp/tri1_ali || exit 1
  steps/train_deltas.sh --cmd "$train_cmd" 3000 50000 data/train data/lang exp/tri1_ali exp/tri2 || exit 1
  local/reestimate_langp.sh --cmd "$train_cmd" --unk "<UNK>" \
                            data/train data/lang data/local/ \
                            exp/tri2 data/local/dictp/tri2 data/local/langp/tri2 data/langp/tri2
  touch exp/tri2/.done
fi

if [ ! -f exp/tri3/.done ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (full) triphone training in exp/tri3 on"
  echo ---------------------------------------------------------------------
  echo
  steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/lang exp/tri2 exp/tri2_ali || exit 1
  steps/train_deltas.sh --cmd "$train_cmd" 4000 70000 data/train data/langp/tri2 exp/tri2_ali exp/tri3 || exit 1
  local/reestimate_langp.sh --cmd "$train_cmd" --unk "<UNK>" \
                            data/train data/lang data/local/ \
                            exp/tri3 data/local/dictp/tri3 data/local/langp/tri3 data/langp/tri3
  touch exp/tri3/.done
fi

if [ ! -f exp/tri4/.done ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (lda_mllt) triphone training in exp/tri4 on"
  echo ---------------------------------------------------------------------
  echo
  steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/langp/tri3 exp/tri3 exp/tri3_ali || exit 1
  steps/train_lda_mllt.sh --cmd "$train_cmd" 5000 90000 data/train data/langp/tri3 exp/tri3_ali exp/tri4 || exit 1
  local/reestimate_langp.sh --cmd "$train_cmd" --unk "<UNK>" \
                            data/train data/lang data/local \
                            exp/tri4 data/local/dictp/tri4 data/local/langp/tri4 data/langp/tri4
  touch exp/tri4/.done
fi

if [ ! -f exp/tri5/.done ]; then
  echo
  echo ---------------------------------------------------------------------
  echo "Starting (SAT) triphone training in exp/tri5"
  echo ---------------------------------------------------------------------
  echo
  steps/align_si.sh --nj $nj --cmd "$train_cmd" data/train data/langp/tri4 exp/tri4 exp/tri4_ali || exit 1

  steps/train_sat.sh --cmd "$train_cmd" 6000 110000 data/train data/langp/tri4 exp/tri4_ali exp/tri5
  local/reestimate_langp.sh --cmd "$train_cmd" --unk "<UNK>" \
                            data/train data/lang data/local \
                            exp/tri5 data/local/dictp/tri5 data/local/langp/tri5 data/langp/tri5
  touch exp/tri5/.done
fi


cp data/lang/G.fst data/langp/tri5/G.fst

utils/mkgraph.sh data/langp/tri5 exp/tri5_ali exp/tri5/graph || exit 1
steps/decode.sh --config conf/decode.config --nj $nj --cmd "$decode_cmd" exp/tri5/graph data/test exp/tri5/decode




#if [ ! -f exp/tri5_ali/.done ]; then
#  echo
#  echo ---------------------------------------------------------------------
#  echo "Starting exp/tri5_ali on"
#  echo ---------------------------------------------------------------------
#  echo
#  steps/align_fmllr.sh --nj $nj --cmd "$train_cmd" data/train data/langp/tri5 exp/tri5 exp/tri5_ali
#  local/reestimate_langp.sh --cmd "$train_cmd" --unk "<UNK>" \
#                            data/train data/lang data/local \
#                            exp/tri5_ali data/local/dictp/tri5_ali data/local/langp/tri5_ali data/langp/tri5_ali
#  touch exp/tri5_ali/.done
#fi
#
#if [ ! -f data/langp_test/.done ]; then
#  cp -R data/langp/tri5_ali/ data/langp_test
#  cp data/lang/G.fst data/langp_test
#  touch data/langp_test/.done
#fi
#
#if $tri5_only ; then
#  echo "Exiting after stage TRI5, as requested. "
#  echo "Everything went fine. Done"
#  exit 0;
#fi

################################################################################
# Ready to start SGMM training
################################################################################

#if [ ! -f exp/ubm5/.done ]; then
#  echo
#  echo ---------------------------------------------------------------------
#  echo "Starting exp/ubm5"
#  echo ---------------------------------------------------------------------
#  echo
#  steps/train_ubm.sh --cmd "$train_cmd" 400 data/train data/langp/tri5_ali exp/tri5_ali exp/ubm5
#  touch exp/ubm5/.done
#fi
#
#if [ ! -f exp/sgmm5/.done ]; then
#  echo ---------------------------------------------------------------------
#  echo "Starting exp/sgmm5"
#  echo ---------------------------------------------------------------------
#  steps/train_sgmm2.sh --cmd "$train_cmd" 7000 9000  data/train data/langp/tri5_ali exp/tri5_ali exp/ubm5/final.ubm exp/sgmm5
#  touch exp/sgmm5/.done
#fi
#
#if $sgmm5_only ; then
#  echo "Exiting after stage SGMM5, as requested. "
#  echo "Everything went fine. Done"
#  exit 0;
#fi
#
#
################################################################################
# Ready to start discriminative SGMM training
################################################################################
#
#if [ ! -f exp/sgmm5_ali/.done ]; then
#  echo
#  echo ---------------------------------------------------------------------
#  echo "Starting exp/sgmm5_ali"
#  echo ---------------------------------------------------------------------
#  echo
#  steps/align_sgmm2.sh --nj $nj --cmd "$train_cmd" --transform-dir exp/tri5_ali \
#                       --use-graphs true --use-gselect true \
#                       data/train data/lang exp/sgmm5 exp/sgmm5_ali
#  local/reestimate_langp.sh --cmd "$train_cmd" --unk "<UNK>" \
#                            data/train data/lang data/local \
#                            exp/sgmm5_ali data/local/dictp/sgmm5 data/local/langp/sgmm5 data/langp/sgmm5
#  touch exp/sgmm5_ali/.done
#fi
#
#
#if [ ! -f exp/sgmm5_denlats/.done ]; then
#  echo ---------------------------------------------------------------------
#  echo "Starting exp/sgmm5_denlats"
#  echo ---------------------------------------------------------------------
#  steps/make_denlats_sgmm2.sh --nj $nj --sub-split $nj  \
#                              --beam 10.0 --lattice-beam 6 --cmd "$decode_cmd" --transform-dir exp/tri5_ali \
#                              data/train data/langp/sgmm5 exp/sgmm5_ali exp/sgmm5_denlats
#  touch exp/sgmm5_denlats/.done
#fi
#
#
#if $denlats_only ; then
#  echo "Exiting after generating denlats, as requested. "
#  echo "Everything went fine. Done"
#  exit 0;
#fi
#
#
#if [ ! -f exp/sgmm5_mmi_b0.1/.done ]; then
#  echo ---------------------------------------------------------------------
#  echo "Starting exp/sgmm5_mmi_b0.1"
#  echo ---------------------------------------------------------------------
#  steps/train_mmi_sgmm2.sh --cmd "$train_cmd --max-jobs-run 1"  \
#                           --drop-frames true --transform-dir exp/tri5_ali --boost 0.1 \
#                           data/train data/langp/sgmm5 exp/sgmm5_ali exp/sgmm5_denlats \
#                           exp/sgmm5_mmi_b0.1
#  touch exp/sgmm5_mmi_b0.1/.done
#fi

#cp data/lang/G.fst data/langp/tri5_ali/G.fst
##utils/mkgraph.sh data/langp/sgmm5 exp/sgmm5_mmi_b0.1 exp/sgmm5_mmi_b0.1/graph || exit 1
##steps/decode.sh --config conf/decode.config --nj $nj --cmd "$decode_cmd" \
##                exp/sgmm5_mmi_b0.1/graph data/test exp/sgmm5_mmi_b0.1/decode
#
#utils/mkgraph.sh data/langp/tri5_ali exp/tri5_ali exp/tri5_ali/graph || exit 1
#steps/decode.sh --config conf/decode.config --nj $nj --cmd "$decode_cmd" exp/tri5_ali/graph data/test exp/tri5_ali/decode
#
#
#echo
#echo "===== run.sh script is finished ====="
#echo