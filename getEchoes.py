#!/usr/bin/env python

# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

# Acknowledgement: Part of the codes are adapted from Unnat Jain 

import os
import numpy as np
import librosa
from scipy.io import wavfile
from scipy.signal import fftconvolve
from tqdm import tqdm
import soundfile as sf

FREQ = 44100
AMPLITUDE_SCALING_FACTOR = 10

def convolve_data(
        scene_rir_dir,
        scene_echoes_dir,
        source_audio_file,
        amplitude_scaling_factor
):
    sig, fs = sf.read(source_audio_file, dtype='int16')
    sig = librosa.util.fix_length(sig, FREQ)
    assert fs == FREQ

    for angle in os.listdir(scene_rir_dir):
        angle_scene_rir_dir = os.path.join(scene_rir_dir, angle)
        angle_scene_echoes_dir = os.path.join(scene_echoes_dir, angle)
        os.makedirs(angle_scene_echoes_dir, exist_ok=True)

        rir_files = os.listdir(angle_scene_rir_dir)
        last_rir_file = None
        for rir_file_name in tqdm(rir_files):
            rir_file = os.path.join(angle_scene_rir_dir, rir_file_name)
            echo_file = os.path.join(angle_scene_echoes_dir, rir_file_name)
            if os.path.exists(echo_file):
                last_rir_file = rir_file
                continue
            try:
                fs_imp, sig_imp = wavfile.read(rir_file)
            except ValueError:
                print('{} has wrong file format. Using {} as substitute.'.format(rir_file, last_rir_file))
                fs_imp, sig_imp = wavfile.read(last_rir_file)

            imp_full_length = np.zeros((FREQ,2))
            imp_full_length[:sig_imp.shape[0]-128, :] = sig_imp[128:, :] #remove the first 127 zero samples
            sig_imp = imp_full_length
            assert fs_imp == FREQ
            output_sig = []
            for ch_i in range(sig_imp.shape[-1]):
                output_sig.append(fftconvolve(sig, sig_imp[:, ch_i] / amplitude_scaling_factor, mode="full"))
            output_sig = np.array(output_sig).T
            output_sig = output_sig[:FREQ,:]
            output_sig_pcm = np.round(output_sig).astype("int16")
            wavfile.write(echo_file, FREQ, output_sig_pcm)
            last_rir_file = rir_file
 
def main():
    data_root_dir = '/YOUR_DATA_ROOT/'
    echolocation_RIR_dir = os.path.join(data_root_dir, 'echolocation_RIRs_navigable')
    echoes_dir = os.path.join(data_root_dir, 'echoes_navigable')
    sound_dir = os.path.join(data_root_dir, 'sweep_audio')
    sound_files = ['3ms_sweep.wav']

    scenes = ['apartment_0', 'apartment_1', 'apartment_2', 'frl_apartment_0', 'frl_apartment_1', 'frl_apartment_2',
              'frl_apartment_3',  'frl_apartment_4', 'frl_apartment_5', 'office_0', 'office_1', 'office_2',
              'office_3', 'office_4', 'hotel_0', 'room_0', 'room_1', 'room_2']

    for sound_file in sound_files:
        sound = sound_file.split('.')[0]
        source_audio_file = os.path.join(sound_dir, sound_file)
        for scene in scenes:
            scene_rir_dir = os.path.join(echolocation_RIR_dir, scene)
            scene_echoes_dir = os.path.join(echoes_dir, scene, sound)
            os.makedirs(scene_echoes_dir, exist_ok=True)
            convolve_data(scene_rir_dir, scene_echoes_dir, source_audio_file, AMPLITUDE_SCALING_FACTOR)

if __name__ == '__main__':
    main()
