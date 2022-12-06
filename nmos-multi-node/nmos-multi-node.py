# SPDX-FileCopyrightText: Copyright (c) 2022 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import subprocess
import sys
import time
import uuid
from jinja2 import Template

SEED_SEED_NAMESPACE = uuid.UUID("a82dbccc-eb5f-40af-a6da-33de71cfa345")
SEED_NAMESPACE = uuid.uuid5(SEED_SEED_NAMESPACE, str(uuid.getnode()))

def parse_arguments():
    parser = argparse.ArgumentParser(description='Multi-nmos-cpp-node Launcher')
    parser.add_argument('-c', '--config', default='config.json', help="JSON settings template file")
    parser.add_argument('-i', '--offset', default=0, type=int, help="offset to apply to each process index")
    parser.add_argument('-n', '--count', default=2, type=int, help="number of processes to launch")
    parser.add_argument('-x', '--executable', default='nmos-cpp-node', help="path of executable to launch")

    return parser.parse_args()

def render_config(config_template, index):
    template = Template(config_template)
    render = template.render(seed=uuid.uuid5(SEED_NAMESPACE, str(index)), index=index)
   
    return render

def main(args):
    args = parse_arguments()

    config_template = open(args.config).read()

    processes = []

    for i in range(args.offset, args.offset + args.count):
        process = subprocess.Popen([args.executable, render_config(config_template, i)])
        print("{}: Launched {}".format(i, process.pid))
        processes.append((i, process))

    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass

    for (i, process) in processes:
        print("{}: Terminating {}".format(i, process.pid))
        process.terminate()

    sys.exit(0)

if __name__ == '__main__':
    main(sys.argv)
