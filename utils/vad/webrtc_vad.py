import os
import wave
import webrtcvad
import contextlib
import collections

from utils import create_dir


def read_wave(path):
    """
    Reads a .wav file.
    Takes the path, and returns (PCM audio data, sample rate).
    """
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000, 48000)
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate


def write_wave(path, audio, sample_rate):
    """
    Writes a .wav file.
    Takes path, PCM audio data, and sample rate.
    """
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


class Frame(object):
    """
    Represents a "frame" of audio data.
    """
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """
    Generates audio frames from PCM audio data.
    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.
    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


def vad_collector(vad, frames, sample_rate, frame_duration_ms=30, padding_duration_ms=300):
    """
    Filters out non-voiced audio frames.
    Given a webrtcvad.Vad and a source of audio frames, yields only
    the voiced audio.
    Uses a padded, sliding window algorithm over the audio frames.
    When more than 90% of the frames in the window are voiced (as
    reported by the VAD), the collector triggers and begins yielding
    audio frames. Then the collector waits until 90% of the frames in
    the window are unvoiced to detrigger.
    The window is padded at the front and back to provide a small
    amount of silence or the beginnings/endings of speech around the
    voiced frames.

    Parameters
    ----------
    vad :
        An instance of webrtcvad.Vad.
    frames :
        a source of audio frames (sequence or generator).
    sample_rate : int
        The audio sample rate, in Hz.
    frame_duration_ms : int, default 30
        The frame duration in milliseconds.
    padding_duration_ms : int, default 300
        The amount to pad the window, in milliseconds.

    Returns
    -------
    out :
        A generator that yields PCM audio data.
    """

    num_padding_frames = int(padding_duration_ms / frame_duration_ms)

    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)

    # We have two states: TRIGGERED and NOTTRIGGERED. We start in the NOTTRIGGERED state.
    triggered = False

    voiced_frames = []
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])

            # If we're NOTTRIGGERED and more than 90% of the frames in the ring buffer are voiced frames,
            # then enter the TRIGGERED state.
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True

                # We want to yield all the audio we see from now until we are NOTTRIGGERED,
                # but we have to start with the audio that's already in the ring buffer.
                for f, s in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            # We're in the TRIGGERED state, so collect the audio data and add it to the ring buffer.
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])

            # If more than 90% of the frames in the ring buffer are unvoiced, then enter NOTTRIGGERED
            # and yield whatever audio we've collected.
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                triggered = False
                yield b''.join([f.bytes for f in voiced_frames])
                ring_buffer.clear()
                voiced_frames = []

    # If we have any leftover voiced audio when we run out of input, we yield it.
    if voiced_frames:
        yield b''.join([f.bytes for f in voiced_frames])


def vad_segments(file_path, out_folder=None, aggressiveness=0):
    audio, sample_rate = read_wave(file_path)
    file_name = next(reversed(file_path.rsplit('/', 1)))
    vad = webrtcvad.Vad(aggressiveness)
    frames = list(frame_generator(30, audio, sample_rate))
    segments = vad_collector(vad, frames, sample_rate)

    if out_folder:
        res = []
        for i, segment in enumerate(segments, 1):
            create_dir(out_folder)
            path = os.path.join(out_folder, f'{file_name}-segment-{i}.wav')
            write_wave(path, segment, sample_rate)
            res.append(path)
        return res

    return segments


if __name__ == '__main__':
    vad_segments('path/to/file', 'segments')