#!/usr/bin/python3
"""setup_qldet_nox.py

Usage:
    setup_qldet_nox.py set <dmap> <fs> [--hbw-ext=<bw>] [--dif--gain=<dg>] [--enable-sva]
    setup_qldet_nox.py get <dmap> <fs>
    setup_qldet_nox.py plot <dmap> <fs>
    setup_qldet_nox.py (-h | --help)
    setup_qldet_nox.py --version

Options:
  -h --help        Show this screen.
  --version        Show version.
  <dmap>           LLRF controller .dmap file path
  <fs>             QLDET sample rate (Hz).
  --hbw-ext=<bw>   Cavity external half bandwidth (Hz).
  --diff-gain=<df> Differential gain [0, 7].
  --enable-sva     Enable slow varying approximation.
"""

import deviceaccess as da
from docopt import docopt
import numpy as np
import matplotlib.pyplot as plt
import os

VERSION = "1.0.0"

class QLDetIO(object):
    def __init__(self, dmap_path):
        dmap_path = os.path.split(dmap_path)
        cwd = os.getcwd()
        os.chdir(dmap_path[0])
        da.setDMapFilePath(dmap_path[1])
        ctrl_board = da.Device("CtrlBoard")
        ctrl_board.open()
        self.ctrl_board = ctrl_board
        os.chdir(cwd)

        probe_idx_acc = ctrl_board.getScalarRegisterAccessor(np.int32, "/APP/WORD_PIEZO_PRO_SEL")
        vforw_idx_acc = ctrl_board.getScalarRegisterAccessor(np.int32, "/APP/WORD_PIEZO_FOR_SEL")
        vrefl_idx_acc = ctrl_board.getScalarRegisterAccessor(np.int32, "/APP/WORD_PIEZO_REF_SEL")

        self.probe_idx_acc.read()
        self.vforw_idx_acc.read()
        self.vrefl_idx_acc.read()

        # Assumed probe=CH1, vforw=CH0, vrefl=CH2
        self.probe_idx_acc.set(1)
        self.vforw_idx_acc.set(0)
        self.vrefl_idx_acc.set(2)

        self.probe_idx_acc.write()
        self.vforw_idx_acc.write()
        self.vrefl_idx_acc.write()

        self.sva_acc        = ctrl_board.getScalarRegisterAccessor(np.int32, "/LLRF_QLDET/BIT_SVA")
        self.beam_src_acc   = ctrl_board.getScalarRegisterAccessor(np.int32, "/LLRF_QLDET/BIT_BEAM_SRC")
        self.kcoeff_acc     = ctrl_board.getScalarRegisterAccessor(np.int32, "/LLRF_QLDET/WORD_K")
        self.bcoeff_acc     = ctrl_board.getScalarRegisterAccessor(np.int32, "/LLRF_QLDET/WORD_B")
        self.beam_ext_i_acc = ctrl_board.getScalarRegisterAccessor(np.int32, "/LLRF_QLDET/WORD_BEAM_EXT_I")
        self.beam_ext_q_acc = ctrl_board.getScalarRegisterAccessor(np.int32, "/LLRF_QLDET/WORD_BEAM_EXT_Q")
        self.diff_gain_acc  = ctrl_board.getScalarRegisterAccessor(np.int32, "/LLRF_QLDET/WORD_DIFF_GAIN")
        self.det_trace_acc  = ctrl_board.getScalarRegisterAccessor(np.int32, "/LLRF_QLDET/WORD_BEAM_EXT_Q")
        self.bw_trace_acc   = ctrl_board.getScalarRegisterAccessor(np.int32, "/LLRF_QLDET/WORD_DIFF_GAIN")

        self.sva_acc.read()
        self.beam_src_acc.read()
        self.kcoeff_acc.read()
        self.bcoeff_acc.read()
        self.beam_ext_i_acc.read()
        self.beam_ext_q_acc.read()
        self.diff_gain_acc.read()

        self.daq_samples_acc = ctrl_board.getOneDRegisterAccessor(np.int32, "/DAQ/WORD_SAMPLES")
        self.daq1_acc = ctrl_board.getTwoDRegisterAccessor(np.int32, "/app_daq/DAQ_FD_BUF0")

        self.daq_samples_acc.read()
        self.daq1_acc.read()

        self.beam_src_acc.set(0)
        self.bcoeff_acc.set(0)
        self.beam_ext_i_acc.set(0)
        self.beam_ext_q_acc.set(0)
        self.beam_src_acc.write()
        self.bcoeff_acc.write()
        self.beam_ext_i_acc.write()
        self.beam_ext_q_acc.write()

    def set_qldet_params(self, fs, hbw_ext, diff_gain, enable_sva=False):
        if fs <= 0.0:
            raise Exception("The sampling frequency fs should be positive")

        if hbw_ext <= 0.0:
            raise Exception("The half bandwidth hbw should be positive")

        if diff_gain < 0 or diff_gain > 7:
            raise Exception("The differential gain diff_gain should be in [0, 7]")

        kcoeff = int(4 * np.pi * hbw_ext / fs * 2**(24 + diff_gain))

        self.kcoeff_acc.set(k)
        self.kcoeff_acc.write()

        self.diff_gain_acc.set(diff_gain)
        self.diff_gain_acc.write()

    def get_qldet_params(fs, self):

        self.kcoeff_acc.read()
        self.diff_gain_acc.read()
        self.sva_acc.read()

        kcoeff = self.kcoeff_acc[0]
        hbw_ext = kcoeff * fs * 2**(24 + diff_gain) / (4 * np.pi)

        df_quantization = fs / (np.pi * 2**(16 + self.diff_gain_acc[0]))
        df_range = df_quantization * 2**16

        result = dict()
        result["df_quantization"] = df_quantization
        result["df_range"] = df_range
        result["hbw_ext"] = hbw_ext
        result["diff_gain"] = self.diff_gain_acc[0]
        result["enable_sva"] = bool(self.sva_acc[0])
        result["fs"] = fs

        return result

    def get_hbwdet_traces(self, fs):
        df_quantization = self.get_qldet_params(fs)["df_quantization"]
        self.daq1_acc.read()
        det_td = -self.daq1_acc[10,:self.daq_samples_acc[1]] * self.df_quantization
        hbw_td = self.daq1_acc[11,:self.daq_samples_acc[1]] * self.df_quantization
        return (hbw_td, det_td)

if __name__ == "__main__":

    args = docopt(__doc__, version=VERSION)
    dmap = args["<dmap>"]
    fs = args["<fs>"]
    hbw_ext = args["--hbw-ext"]
    diff_gain = args["--diff-gain"]
    enable_sva = args["--enable-sva"]

    qldetio = QLDetIO(dmap)

    if args["set"]:
        params = qldetio.get_qldet_params(fs)

        if hbw_ext is not None:
            params["hbw_ext"] = hbw_ext

        if diff_gain is not None:
            params["diff_gain"] = diff_gain

        if enable_sva is not None:
            params["enable_sva"] = enable_sva

        qldetio.set_qldet_params(fs,
                                 params["hbw_ext"],
                                 params["diff_gain"],
                                 params["enable_sva"])

    if args["get"]:
        params = qldetio.get_qldet_params(fs)
        print("Traces quantization (Hz):", params["df_quantization"])
        print("Traces range (Hz):", params["df_range"])
        print("External half bandwidth (Hz):", params["hbw_ext"])
        print("Differential gain:", params["diff_gain"])
        print("SVA enabled:", params["enable_sva"])
        print("Sample rate (Hz):", params["fs"])

    if args["plot"]:
        plt.ion()
        (hbw_td, det_td) = self.get_hbwdet_traces(fs)
        fig, (ax_hbw, ax_det) = plt.subplot(ncols=2)
        ax_hbw.set_xlabel("Sample")
        ax_hbw.set_ylabel("Half bandwidth (Hz)")
        ax_det.set_xlabel("Sample")
        ax_det.set_ylabel("Detuning (Hz)")

        ax_hbw.plot(hbw_td)
        ax_det.plot(det_td)
        fig.show()

        input("Press return..")

