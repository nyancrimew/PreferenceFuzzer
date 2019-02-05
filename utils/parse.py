#
# Copyright (C) 2019 Lawnchair Launcher
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import numpy as np

def parse_range(str):
    parts = str.split("..", 1)
    start = parts[0]
    stop = parts[1]
    parts = stop.split(";", 1)
    stop = parts[0]
    step = "1"
    if len(parts) > 1:
        step = parts[1]
    if "." in start or "." in stop or "." in step:
        step = float(step)
        start = float(start)
        stop = float(stop) + step
        return np.arange(start, stop, step).tolist()
    else:
        step = int(step)
        start = int(start)
        stop = int(stop) + step
        return list(range(start, stop, step))