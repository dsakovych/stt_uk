import os
import re
import shutil
import subprocess
import logging

from config import s5_path, TMP_DIR, KALDI_PATH, DATA_DIR
from utils import create_dir, delete_dir
from utils.convert import transform_audio_file


def kaldi_stt(file_path, transcript=None, std_bash=False, tmp_dir=TMP_DIR, model_dir=s5_path):
    """ Kaldi speech to text decoding """
    nj = 1
    beam = 14
    lat_beam = 6
    sr = 8000

    file_path_old = file_path[-4] + ".old.wav"

    os.rename(file_path, file_path_old)

    speaker_id = file_path.rsplit("/", 1)[1]
    speaker_dir = os.path.join(tmp_dir, speaker_id)
    wav_data_dir = os.path.join(speaker_dir, "data")
    wav_path = os.path.join(wav_data_dir, speaker_id)

    create_dir(wav_data_dir)

    transform_audio_file(file_path_old, wav_path, rate=sr)

    wavscp_path = os.path.join(speaker_dir, "wav.scp")
    with open(wavscp_path, "w") as scp_file:
        scp_file.write(f"{speaker_id} {wav_path}\n")

    utt2spk_path = os.path.join(speaker_dir, "utt2spk")
    with open(utt2spk_path, "w") as scp_file:
        scp_file.write(f"{speaker_id} {speaker_id}\n")

    spk2utt_path = os.path.join(speaker_dir, "spk2utt")
    with open(spk2utt_path, "w") as scp_file:
        scp_file.write(f"{speaker_id} {speaker_id}\n")

    if transcript:
        text_path = os.path.join(speaker_dir, "text")
        with open(text_path, "w") as scp_file:
            scp_file.write(f"{speaker_id} {transcript}\n")

    speaker_dir = f"{TMP_DIR}/{speaker_id}"
    decode_dir = f"{model_dir}/exp/tri5_ali/{speaker_id}"

    export = f"""
        export nj={nj}
        export beam={beam}
        export lat_beam={lat_beam}
        export KALDI_ROOT={KALDI_PATH}
        export s5_path={model_dir}
        export decode_dir="{TMP_DIR}/{speaker_id}"
        export model_dir="{model_dir}/exp/tri5_ali"
        export decode_res_dir="{model_dir}/exp/tri5_ali/{speaker_id}"

        [ -f $KALDI_ROOT/tools/env.sh ] && . $KALDI_ROOT/tools/env.sh
        export PATH=$PWD/utils/:$KALDI_ROOT/tools/openfst/bin:$PWD:$PATH
        [ ! -f $KALDI_ROOT/tools/config/common_path.sh ] && echo >&2 "The standard file $KALDI_ROOT/tools/config/common_path.sh is not present -> Exit!" && exit 1
        . $KALDI_ROOT/tools/config/common_path.sh
        export LC_ALL=C
    """
    make_features = """
        cd $s5_path
        steps/make_mfcc.sh --nj $nj $decode_dir $decode_dir/log/mfcc
        steps/compute_cmvn_stats.sh $decode_dir $decode_dir/log/mfcc
    """
    if transcript:
        decode = """
            if [ -d decode_res_dir ]; then
                rm -rf $decode_res_dir
            fi
            steps/decode.sh --skip-scoring false --beam $beam --lattice-beam $lat_beam --nj $nj $model_dir/graph/ $decode_dir $decode_res_dir
        """
    else:
        decode = """
            if [ -d decode_res_dir ]; then
                rm -rf $decode_res_dir
            fi
            steps/decode.sh --skip-scoring false --beam $beam --lattice-beam $lat_beam --nj $nj $model_dir/graph/ $decode_dir $decode_res_dir
        """
    extract_res = """
    find  ${decode_res_dir}  -name lat*.gz -exec bash -c \
    'lattice-best-path  --acoustic-scale=0.085 --word-symbol-table=exp/tri5_ali/graph/words.txt ark:"gunzip -c {} |" ark,t:${decode_res_dir}/one-best.tra_$(basename ${0/gz/txt})' {} \;
    cat ${decode_res_dir}/one-best*.txt >> ${decode_res_dir}/all.txt
    utils/int2sym.pl -f 2- exp/tri5_ali/graph/words.txt ${decode_res_dir}/all.txt > ${decode_res_dir}/best_hyp.txt
    """

    p = subprocess.Popen(export + make_features + decode + extract_res,
                         shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    if transcript:
        with open(os.path.join(model_dir, "exp", "tri5_ali", speaker_id, 'scoring_kaldi', 'best_wer')) as file_:
            wer = file_.readlines()
            wer = re.findall(r"(.*)\]\s+", wer[0])[0].strip() + ']'
        with open(os.path.join(model_dir, "exp", "tri5_ali", speaker_id, 'scoring_kaldi', 'wer_details', 'per_utt')) as file_:
            wer_details = file_.readlines()
            wer_details = [item.split(" ", 1)[1] for item in wer_details]
            tmp = wer_details[1].split(" ", 1)[1]
            wer_details = ["\t".join(item.split(" ")) for item in wer_details]
            wer_details = "<br>".join(wer_details)

    tb = "\n\n".join([stdout.decode(), stderr.decode()])
    if std_bash:
        print(tb)

    with open(f"{decode_dir}/best_hyp.txt", 'r', encoding='utf-8') as f:
        res = f.readlines()

    thrash_folders = (speaker_dir, decode_dir)
    [delete_dir(folder) for folder in thrash_folders]

    try:
        res = res[0].split(" ", 1)[1]#, "Success!"
    except IndexError:
        res = tb#, "Failed!"
        logging.error(f"Kaldi traceback:\n{tb}")
    if transcript:
        if res.strip() != tmp.strip():
            res = "<b>hyp_1: </b>" + res + "<br><br>" + '<b>hyp_2: </b>' + tmp.replace("*", '')
        return res, wer, wer_details
    else:
        return res


if __name__ == '__main__':

    path_file = os.path.join(DATA_DIR, 'test_uk.wav')
    print(kaldi_stt(path_file))
