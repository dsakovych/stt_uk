import os
import sox
import logging


def transform_wav(input_path, output_path=None, sr=16000):
    conf = {
        "rate": sr,
        "bits": 16,
        "channels": 1
    }
    if output_path is None:
        output_path = input_path

    tfm = sox.Transformer()
    tfm.set_globals(dither=True, verbosity=0)
    tfm.set_output_format(rate=conf.get("rate"), bits=conf.get("bits"), channels=conf.get("channels"))

    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    try:
        tfm.build(input_path, output_path)
        return "Done!"
    except Exception as e:
        logging.error(f"Error occured for input_path={input_path}", exc_info=True)
        return "Failed!"


if __name__ == '__main__':
    transform_wav('/home/dima/Projects/stt_uk/data/recorded_samples/sample2.wav',
                  '/data/recorded_samples/sample2.wav')