import os
import subprocess
import logging

from config import s5_path, TMP_DIR
from utils import create_dir, delete_dir, transform_wav


def kaldi_vtt(file_path, std_bash=False, tmp_dir=TMP_DIR, model_dir=s5_path):
    """ Kaldi speech to text decoding function """
    nj = 1
    beam = 13
    lat_beam = 4
    sr = 8000

    file_path_old = file_path.replace(".wav", ".old.wav")

    os.rename(file_path, file_path_old)

    speaker_id = file_path.rsplit("/", 1)[1]
    speaker_dir = os.path.join(tmp_dir, speaker_id)
    wav_data_dir = os.path.join(speaker_dir, "data")
    wav_path = os.path.join(wav_data_dir, speaker_id)

    create_dir(wav_data_dir)

    transform_wav(file_path_old, wav_path, sr=sr)

    wavscp_path = os.path.join(speaker_dir, "wav.scp")
    with open(wavscp_path, "w") as scp_file:
        scp_file.write(f"{speaker_id} {wav_path}\n")

    utt2spk_path = os.path.join(speaker_dir, "utt2spk")
    with open(utt2spk_path, "w") as scp_file:
        scp_file.write(f"{speaker_id} {speaker_id}\n")

    spk2utt_path = os.path.join(speaker_dir, "spk2utt")
    with open(spk2utt_path, "w") as scp_file:
        scp_file.write(f"{speaker_id} {speaker_id}\n")

    decode_dir = f"{model_dir}/exp/tri5/decode_dir_{speaker_id}"
    plp_dir = f"{model_dir}/plp_{speaker_id}/"
    make_plp_pitch_dir = f"{model_dir}/exp/make_plp_pitch_{speaker_id}"

    export = f"""
        export nj={nj}
        export beam={beam}
        export lat_beam={lat_beam}
        export s5d_path={s5_path}
        export speaker_dir={speaker_dir}
        export decode_dir={decode_dir}
        export plp_dir={plp_dir}
        export make_plp_pitch_dir={make_plp_pitch_dir}
    """
    make_features = """
        cd ${s5d_path} &&  . ./cmd.sh && . ./path.sh
        steps/make_plp_pitch.sh --cmd "$decode_cmd" --nj $nj ${speaker_dir} ${make_plp_pitch_dir} ${plp_dir}
        steps/compute_cmvn_stats.sh ${speaker_dir} ${make_plp_pitch_dir} ${plp_dir}
    """
    decode = """
        steps/decode_fmllr_extra.sh --skip-scoring true --beam $beam --lattice-beam $lat_beam --nj $nj --cmd "$decode_cmd"  exp/tri5/graph ${speaker_dir} ${decode_dir}
    """
    extract_res = """
        find  ${decode_dir}  -name lat*.gz -exec bash -c \
        'lattice-best-path  --acoustic-scale=0.085 --word-symbol-table=exp/tri5/graph/words.txt ark:"gunzip -c {} |" ark,t:${speaker_dir}/one-best.tra_$(basename ${0/gz/txt})' {} \;
        cat ${speaker_dir}/one-best*.txt >> ${speaker_dir}/all.txt
        utils/int2sym.pl -f 2- exp/tri5/graph/words.txt ${speaker_dir}/all.txt > ${speaker_dir}/best_hyp.txt
    """

    p = subprocess.Popen(export + make_features + decode + extract_res,
                         shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    tb = "\n\n".join([stdout.decode(), stderr.decode()])
    if std_bash:
        print(tb)

    with open(f"{speaker_dir}/best_hyp.txt", 'r', encoding='utf-8') as f:
        res = f.readlines()

    thrash_folders = (speaker_dir, decode_dir, plp_dir, make_plp_pitch_dir, decode_dir + ".si")
    [delete_dir(folder) for folder in thrash_folders]

    try:
        res = res[0].split(" ", 1)[1], "Success!"
    except IndexError:
        res = tb, "Failed!"
        logging.error(f"Kaldi traceback:\n{tb}")
    return res


if __name__ == '__main__':
    kaldi_vtt("test_file")
