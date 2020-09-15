import os
import re
import subprocess
import logging

from config import KALDI_PROJECT_PATH, KALDI_PROJECT_MODEL_PATH, KALDI_PATH, TMP_DIR, DATA_DIR, stt_config
from utils import create_dir, delete
from utils.convert import transform_audio_file


def kaldi_stt(file_path, transcript=None, std_bash=True, delete_source=False):
    """ Kaldi speech to text decoding """
    speaker_id = file_path.rsplit("/", 1)[1]
    speaker_dir = os.path.join(TMP_DIR, speaker_id)
    wav_data_dir = os.path.join(speaker_dir, "data")
    wav_path = os.path.join(wav_data_dir, speaker_id)
    decode_dir = os.path.join(KALDI_PROJECT_MODEL_PATH, speaker_id)

    create_dir(wav_data_dir)

    # file_path_old = file_path[-4] + ".old.wav"
    # os.rename(file_path, file_path_old)
    transform_audio_file(file_path, wav_path, rate=stt_config.get("sr", 8000))
    if delete_source:
        delete(file_path)

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

    export_vars = f"""
        export nj={stt_config.get('nj', 1)}
        export beam={stt_config.get('beam', 14)}
        export lat_beam={stt_config.get('lat_beam', 6)}
        export KALDI_ROOT={KALDI_PATH}
        export PROJECT_DIR={KALDI_PROJECT_PATH}
        export MODEL_DIR={KALDI_PROJECT_MODEL_PATH}
        export decode_res_dir={decode_dir}
        export decode_dir={speaker_dir}
    """
    export_path_sh = """
        . $KALDI_ROOT/tools/env.sh
        export PATH=$PROJECT_DIR/utils/:$KALDI_ROOT/tools/openfst/bin:$PWD:$PATH:$KALDI_ROOT/tools/sph2pipe_v2.5
        . $KALDI_ROOT/tools/config/common_path.sh
        export LC_ALL=C
    """
    make_features = """
        cd $PROJECT_DIR
        steps/make_mfcc.sh --nj $nj $decode_dir $decode_dir/log/mfcc
        steps/compute_cmvn_stats.sh $decode_dir $decode_dir/log/mfcc
    """

    decode = """
        if [ -d decode_res_dir ]; then
            rm -rf $decode_res_dir
        fi
        steps/decode.sh --skip-scoring {} --beam $beam --lattice-beam $lat_beam --nj $nj $MODEL_DIR/graph/ $decode_dir $decode_res_dir
    """.format("false" if transcript else "true")

    extract_res = """
        find  ${decode_res_dir}  -name lat*.gz -exec bash -c \
            'lattice-best-path  --acoustic-scale=0.085 --word-symbol-table=${MODEL_DIR}/graph/words.txt ark:"gunzip -c \
                {} |" ark,t:${decode_res_dir}/one-best.tra_$(basename ${0/gz/txt})' {} \;
        cat ${decode_res_dir}/one-best*.txt >> ${decode_res_dir}/all.txt
        utils/int2sym.pl -f 2- ${MODEL_DIR}/graph/words.txt ${decode_res_dir}/all.txt > ${decode_res_dir}/best_hyp.txt
    """

    p = subprocess.Popen(export_vars + export_path_sh + make_features + decode + extract_res,
                         shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    if transcript:
        with open(os.path.join(decode_dir, 'scoring_kaldi', 'best_wer')) as file_:
            wer = file_.readlines()
            wer = re.findall(r"(.*)\]\s+", wer[0])[0].strip() + ']'
        with open(os.path.join(decode_dir, 'scoring_kaldi', 'wer_details', 'per_utt')) as file_:
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
    [delete(folder) for folder in thrash_folders]

    try:
        res = res[0].split(" ", 1)[1]  # , "Success!"
    except IndexError:
        res = tb  # , "Failed!"
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
