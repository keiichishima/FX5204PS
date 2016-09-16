# Fujitsu Component FX5204PS Smart Power Strip module

## Overview

This software contains the Python module to access Fujitsu Component
FX5204PS Smart Power Strip.  The module uses the
[PyUSB](https://walac.github.io/pyusb/) package to access or retrieve
information from the smart power strip.

The code was written based on the ``usps`` driver shipped with OpenBSD.
I greatly appreciate the original driver author Yojiro UO for
suggestions he gave me while I was struggling to read the code.


## Usage

```python
import time

import fx5204ps

fx = fx5204ps.FX5204PS()
print('Firmware: {0}'.format(fx.firmware_version))
print('Serial #: {0}'.format(fx.serial_number))
fx.start()
try:
    while True:
        time.sleep(1)
        print('Volt:  {0}V'.format(fx.voltage))
        print('Freq:  {0}Hz'.format(fx.frequency))
        print('Watt:  {0}W@0, {1}W@1, {2}W@2, {3}W@3'.format(*fx.wattage))
        print('(Avg): {0}W@0, {1}W@1, {2}W@2, {3}W@3'.format(*fx.wattage_avg))
        print('(Max): {0}W@0, {1}W@1, {2}W@2, {3}W@3'.format(*fx.wattage_max))
except KeyboardInterrupt:
    fx.stop()
```


## Code

The source code is available at
https://github.com/keiichishima/FX5204PS


## Bug Reports

Please submit bug reports or patches through the GitHub interfaces.


## Author

Keiichi SHIMA
/ IIJ Innovation Institute Inc.
/ WIDE project
