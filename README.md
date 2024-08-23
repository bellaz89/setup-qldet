Setup QLDET
===========

This script is used to setup the [QLDET][1] component of the MSK/DESY LLRF system for
SRF cavities. It has also the ability to display the detuning and bandwidth traces
and obtain the parameter set in the component. The component works on single cavity
(SCAV) systems.

Prerequisites
-------------

* ChimeraTK python bindings
* docopt (installable via pip)
* numpy (installable via pip)
* matplotlib (installable via pip)

How to use
----------

```
Usage:
    setup_qldet.py set <dmap> <fs> [--hbw-ext=<bw>] [--dif--gain=<dg>] [--enable-sva]
    setup_qldet.py get <dmap> <fs>
    setup_qldet.py plot <dmap> <fs> [--bw-limits=<bl>] [--det-limits=<dl>] [--continuous]
    setup_qldet.py (-h | --help)
    setup_qldet.py --version

Options:
  -h --help         Show this screen.
  --version         Show version.
  <dmap>            LLRF controller .dmap file path
  <fs>              QLDET sample rate (Hz).
  --hbw-ext=<bw>    Cavity external half bandwidth (Hz).
  --diff-gain=<df>  Differential gain. Should be between 0 and 7.
  --enable-sva      Enable slow varying approximation.
  --hbw-limits=<hl> Half bandwidth limits in plots (Hz) [default: 0,500]
  --det-limits=<dl> Detuning limits in plots (Hz) [default: -500,500]
  --continuous      Continuously update the detuning plot
```

In all mode of operation, the script requires the LLRF control system .dmap file
and the [QLDET][1] sample rate in Hz. The latter parameter depends on the firmware
configuration of the used system. To compute the QLDET sample rate, the IQ sample rate
has to be divided by `C_QLDET_CIC_R` of the respective `PKG_APP_CONFIG` vhdl source.

Below a list of example configurations

| Configuration | QLDET sample rate (Hz) | IQ sample rate (Hz) | `C_QLDET_CIC_R` |
| ------------- | ---------------------- | ------------------- | --------------- |
| XFEL Gun-like | 141059.0               | 9027777.8           | 64              |
| HZB           | 141059.0               | 9027777.8           | 64              |
| HZDR          | 112847.2               | 1805555.5           | 16              |
| TARLA         | 112847.2               | 1805555.5           | 16              |
| MESA          | 141059.0               | 9027777.8           | 64              |

In general the `C_QLDET_CIC_R` should so QLDET has a sample rate in the order
100 kHz. However this value can vary depending on the physical characteristics of
the considered facility.


Mode of operation
-----------------

### set

This method of operation is used to configure the QLDET component. It is required
to known the cavity external half bandwidth (measured with decay for an overcoupled system).

The differential gain parameter differential gain can be set between 0 and 7.
Higher values for the differential gain mean higher estimation accuracy but also
a smaller range.

```math
   Q_f = \frac{f_s}{\pi 2^{16 + D_g}} \\
   R_f = 2^{16} \cdot Q_f
```

Where $f_s$ is th QLDET sampling rate, $D_g$ is the differential gain,
$Q_f$ is the frequency quantization and $R_f$ is the frequency range.

Example command using `set` on an XFEL-gun like system:

```bash
  /usr/bin/python3 setup_qldet.py /export/doocs/server/llrfCtrl_server/llrfctrl.dmap 141059.0 --hbw-ext=65.0 --differential-gain=6
```

### get

The `get` command returns the parameters set on the component

### plot

The `plot` command reads and converts the half bandwidth and detuning calculated
by QLDET and plots it. The flag `--continuous` makes the plot to be updated every
second.

K calculation
-------------

```math
  k = 4 \pi \frac{\omega_{1/2}^e 2^{24 + D_g}}{f_s}
```

$k$ is a factor set in hardware that sets the ratio between the forward and the probe
derivative signal. Refer to the relevant [literature for more information][2].

RF channel assignation
----------------------

This script assumes that the firmware `CH1` represents the probe, `CH0` the forward
and `CH2` represent the reflected RF signals. Change the assignement in the source accordingly.

Mantainers
----------

* Andrea Bellandi (andrea.bellandi@desy.de)

[1]: https://gitlab.desy.de/fpgafw/mod/llrf/llrf_qldet
[2]: https://ieeexplore.ieee.org/document/9381881
