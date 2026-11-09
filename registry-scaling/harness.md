<!--
SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0
-->

# Registry Load Test Harness

Status: draft for discussion. Nothing described here is implemented yet.

The harness measures how an NMOS registry handles heartbeats, registrations
and recovery after network outages. It produces the baseline and the
before-and-after comparisons for the proposals in
[nmos-cpp Registry Write Scaling](https://github.com/garethsb/nmos-cpp/blob/docs/registry-write-scaling/Documents/Registry-Write-Scaling.md),
referred to below as the plan. It treats the registry as a black box over the
IS-04 APIs, so the same harness can measure nmos-cpp, a modified nmos-cpp, or
another registry.

## Components

- **Registry under test**, normally `nmos-cpp-registry` built in Release, with
  fixed settings and logging level for each run.
- **Real Nodes**: `nmos-cpp-node` processes started by
  [nmos-multi-node](../nmos-multi-node/README.md). These are the reference for
  realistic Node behaviour.
- **Load generator**: a Python asyncio program that simulates many Nodes in a
  few processes, with control over timing, resource mix and fault exposure.
- **Query clients**: a Python asyncio program that creates Query API
  subscriptions and records WebSocket events.
- **Fault injection**: Linux network namespaces, with `iptables` and `tc
  netem`, to cut or degrade the network between Nodes and registry.
- **Runner**: a script that runs a scenario file, starts and stops every
  component, applies faults at set times, and collects results.

## Load Generator

### Simulated Node Behaviour

Each simulated Node behaves as IS-04 specifies, with nmos-cpp Node defaults:

1. Registers its Node resource, then each sub-resource in dependency order
   (Devices, Sources, Flows, Senders, Receivers), one request at a time.
2. Sends a heartbeat every `heartbeat_interval` (default 5 seconds), with
   configurable phase and jitter.
3. On a 404 heartbeat response, re-registers every resource in order.
4. On a 5xx response, a connection failure, or a timeout, moves to the next
   configured registry, and makes a heartbeat its first request there. It
   re-registers only if that heartbeat returns 404.
5. When every configured registry has failed, waits a random time up to the
   current backoff, which starts at `backoff_min` and grows by `backoff_factor`
   up to `backoff_max` (defaults 1 second, 1.5 and 30 seconds).
6. Uses a heartbeat timeout of `heartbeat_timeout` (default 5 seconds) and a
   registration timeout of `request_timeout` (default 30 seconds).

Each simulated Node uses its own HTTP connections, so the registry handles as
many TCP connections as it would with real Nodes.

Resource IDs come from a repeatable seed, as in `nmos-multi-node`, so a
restarted generator re-registers the same resources. Version timestamps
increase on every change. Generated resources must validate against the IS-04
schemas; the generator's own tests check this.

Registries are configured by URL. DNS-SD is out of scope for the first version,
because it adds discovery timing that the scenarios do not need.

### Configuration

- Number of Nodes, and how they are spread over worker processes.
- Resource mix per Node, chosen from named templates, for example "small" (one
  Device, two Senders, two Receivers) and "large" (64 Senders and 64 Receivers
  with their Sources and Flows).
- IS-04 version.
- Heartbeat phase: spread evenly across the interval, random, or aligned so
  every Node heartbeats at once (the worst case).
- Timeouts and backoff, as above.
- Groups of Nodes, so that a fault can be applied to one group only.

### Architecture

A controller process starts K worker processes, each running one asyncio event
loop that simulates a share of the Nodes. Each worker records:

- every request: Node, resource, kind, start time, end time, status or error;
- its own CPU use and event-loop delay.

A run is invalid if any worker's event-loop delay exceeds a threshold (to be
set, around 50 ms), because the generator's timing would then distort the
measured latencies. The fix is more workers or more hosts.

### Validation Against Real Nodes

At small N (for example 50 Nodes), compare the generator with real
`nmos-cpp-node` processes running the same scenario:

- the sequence of requests for each Node after each fault;
- request timing relative to the fault;
- registry CPU per Node in steady state.

Differences are either fixed in the generator or recorded as known limitations.

## Query Clients

The query client creates S subscriptions and holds one WebSocket connection
open on each. The subscription mix is configurable:

- unfiltered subscriptions on each resource type and on all types;
- filtered subscriptions using basic queries;
- filtered subscriptions using RQL.

It records every event with its arrival time, resource ID and version, so that
notification delay can be computed by matching events against the generator's
request log.

## Fault Injection

The registry and each group of Nodes run in separate network namespaces,
joined by a bridge. The runner applies faults to a group's virtual interface:

- **Outage**: `iptables` rules that drop packets, so Nodes see timeouts. Killing
  processes or rejecting connections would produce a different Node behaviour.
- **Degraded network**: `tc netem` delay and packet loss.
- **Registry restart**: stop the registry process and start it again.

This needs root, or a container with `CAP_NET_ADMIN`.

## Scenarios

Each scenario runs with no subscriptions and with a configured subscription
load, and over a range of N (for example 100, 500, 1000, 2000 and 5000 Nodes).

| Scenario | Description | Main question |
|---|---|---|
| Steady state | N Nodes heartbeating, increasing N | At what N does heartbeat latency approach the timeout? |
| Aligned heartbeats | As steady state, all heartbeats at once | How much headroom does phase spreading give? |
| Cold start | All Nodes register at once | How long until every resource is registered? |
| Short outage | All Nodes cut off for less than the expiry interval (for example 8 seconds) | Does anything get expired or re-registered? |
| Long outage | All Nodes cut off for longer than the expiry interval (for example 30 and 120 seconds) | How long is recovery, and does the storm sustain itself? |
| Partial outage | One group (for example 25%) cut off for longer than the expiry interval | Are the other Nodes affected while that group re-registers? |
| Registry restart | Registry stopped and started | How long until every resource is registered again? |
| Degraded network | Added delay and loss | Do heartbeats start timing out? |

For the multi-instance options in the plan, the same scenarios also
run against each deployment. The section below adds the scenarios specific to
those deployments.

## Metrics

From the generator:

- heartbeat latency: p50, p99 and maximum, over time;
- registration latency: p50, p99 and maximum, over time;
- response codes, timeouts and connection failures;
- failovers between registries, and repeated discoveries;
- false expiries: 404 heartbeat responses for Nodes that had kept
  heartbeating;
- recovery time: from the end of a fault until every Node has every resource
  registered and is heartbeating.

From the query clients:

- notification delay: from the registration response to the matching
  WebSocket event;
- events missed or duplicated, compared with the generator's request log.

From the registry host:

- CPU, memory and thread count of the registry process.

From registry instrumentation (a patch to nmos-cpp, on its own branch):

- write lock wait time and hold time, by handler;
- read lock wait time for heartbeats;
- log messages discarded because the logging queue was full. The logging
  gateway attaches this count to the next message it queues, but
  `nmos::experimental::log_gate` does not currently read or report it.

## Multi-Instance Testing

Proposal, for the options in the plan that run more than one
registry instance with a shared store.

### Topology

Each registry instance and each etcd member runs in its own network
namespace, so the runner can cut off any one of them. The load generator is
configured with every instance's URL, in priority order, and fails over between
them as described above. One query client runs against each instance.

For the load balancer variant, a load balancer runs in its own namespace, and
the generator and query clients use only its address.

### Scenarios

| Scenario | Description | Main question |
|---|---|---|
| Instance cut off from Nodes | One instance unreachable from every Node for longer than the expiry interval | Do its Nodes fail over without re-registering? |
| Instance crash | One instance's process killed | How long is failover, and are any acknowledged registrations lost? |
| Leader change | The leader (active-passive, or one writer with many readers) killed or cut off | How long until writes are accepted again? Does the new leader expire anything early? |
| Instance cut off from etcd | One instance still reachable by Nodes, but not by etcd | Does it stop accepting writes and respond 5xx, so that its Nodes move elsewhere? |
| etcd member lost | One etcd member lost, quorum kept | Is there any effect on latency? |
| etcd quorum lost | A majority of etcd members lost, then restored | Do instances refuse writes cleanly, and recover without a storm? |
| Slow instance | One instance's CPU throttled | How far does its copy of the model fall behind, and does it rebuild correctly after etcd compaction? |
| Concurrent conflicting writes | The same resource registered through two instances at once (active-active only) | Does exactly one write win, with no corruption of the local copies? |

### Additional Metrics

- **Replication delay**: from the commit of a change to its arrival in each
  instance's copy of the model. Measured either by registry instrumentation,
  or by polling each instance's Query API for a resource version just written.
- **Agreement**: the resources and versions in each instance's Query API,
  compared periodically. Any lasting difference is a failure.
- **Failover time**: from the fault until writes are accepted again.
- **Lost writes**: registrations that received a success response but are
  missing after a failover.
- **Query WebSocket events around a failover or rebuild**: events missed,
  duplicated, or delivered out of order, per instance.

## Method

- Run the baseline on unmodified nmos-cpp first.
- Change one thing at a time, and run the same scenarios on the same hardware.
- Repeat each run at least three times and report the spread.
- Record with each result: nmos-cpp commit, registry settings, scenario file,
  generator version, host CPU and memory, and the number of generator
  workers.

## Results Format

- One scenario file (YAML) per run, listing components, settings, and fault
  times.
- Raw samples as JSON Lines, one file per component.
- A summary per run: the metrics above, as JSON, plus plots of latency over
  time with the fault times marked.

## Repository Layout

Proposal, in this repository:

```
registry-scaling/
  harness.md
  load-generator/     simulated Nodes
  query-client/       subscriptions and WebSocket recording
  runner/             scenario runner, network namespace setup, fault injection
  scenarios/          scenario files
```

## Open Questions

- Registry instrumentation: periodic log summaries, or a statistics endpoint?
- Should the generator also support DNS-SD, to test discovery behaviour during
  failover?
- Which hosts are available, and is one 32-core host enough for both the
  registry and the generator at the largest N?
- Should results be kept in this repository or elsewhere?
- Which load balancer should the load balancer variant use?
