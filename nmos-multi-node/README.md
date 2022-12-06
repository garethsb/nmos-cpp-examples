# Multi-nmos-cpp-node Launcher

This script enables scalability testing of [NMOS](https://specs.amwa.tv/nmos) systems with many Nodes.

It simply launches multiple subprocesses of the open-source `nmos-cpp-node` on the local host, each with unique configuration settings.

```
$ py nmos-multi-node.py -h
usage: nmos-multi-node.py [-h] [-c CONFIG] [-i OFFSET] [-n COUNT] [-x EXECUTABLE]

Multi-nmos-cpp-node Launcher

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        JSON settings template file
  -i OFFSET, --offset OFFSET
                        offset to apply to each process index
  -n COUNT, --count COUNT
                        number of processes to launch
  -x EXECUTABLE, --executable EXECUTABLE
                        path of executable to launch
```

## Prerequisites

* Python 3
* nmos-cpp-node (from the [Conan nmos-cpp package](https://conan.io/center/nmos-cpp) or built from [sony/nmos-cpp](https://github.com/sony/nmos-cpp) source)

To install the Python library dependencies:

```
$ pip3 install -r requirements.txt
```

## Setting up a configuration

`nmos-cpp-node` is configured via a JSON file, which is documented at [nmos-cpp-node/config.json](https://github.com/sony/nmos-cpp/blob/master/Development/nmos-cpp-node/config.json).

`nmos-multi-node.py` requires a config _template_ file.
This is simply passed through the [Jinja2](https://pypi.org/project/Jinja2/) template engine to generate the configuration for each `nmos-cpp-node` process.

For now, two variables are provided:

- a subprocess `index`, based on the command line `OFFSET` and `COUNT` arguments
- a repeatable `seed` UUID, based on the host MAC address and the `index`

Here's an example config template:

```
{
    "seed_id": "{{seed}}",
    "logging_level": -40,
    "domain": "local",
    "error_log": "node-{{index+1}}.txt",
    "http_port": {{5000+index}},
    "events_port": -1,
    "events_ws_port": -1,
    "how_many": 2,
    "label": "{{'My {} Node ({})'.format(['Foo', 'Bar', 'Baz'][index % 3], index+1)}}"
}
```

It's a very good idea to include `error_log`, or all the subprocesses will log to _STDOUT_!

## Start

To start 10 nodes, using `nmos-cpp-node` with the template file _config.json_:

```
$ py nmos-multi-node.py -c config.json -n 10 -x nmos-cpp-node
0: Launched 36452
2022-10-18 10:59:57.546: info: 39204: Starting nmos-cpp node
1: Launched 33240
2022-10-18 10:59:57.720: info: 30044: Starting nmos-cpp node
2: Launched 16400
2022-10-18 10:59:58.001: info: 34228: Starting nmos-cpp node
...
```

To start an additional node, alongside those ones:

```
$ py nmos-multi-node.py -c config.json -i 10 -n 1 -x nmos-cpp-node
10: Launched 38244
2022-10-18 11:02:37.201: info: 38244: Starting nmos-cpp node
```

## Stop 

Just interrupt the process, e.g. _Ctrl-C_, to terminate all its subprocesses.

```
0: Terminating 36452
1: Terminating 33240
2: Terminating 16400
...
```

Or use `taskkill` (on Windows) or `kill` (on Linux) to terminate specific subprocesses.

## Restart

If the config template renders repeatable `seed_id` values, for example using the `seed` variable, nodes can easily be restarted with the same resource identifiers.

## Scaling up

Each `nmos-cpp-node` instance takes approximately 10 MB of memory and uses negligible CPU.

I have tested running 200 Nodes with `how_many` set to 4, and therefore a total of 3200 Senders and 3200 Receivers.
