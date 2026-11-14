---
name: tool-docs
description: Looks up how the third-party tools in this project work - Eclipse Leda, Eclipse Zenoh, Eclipse Kuksa, COVESA VSS, Google Cloud Pub/Sub and Splunk. Use whenever a question is about what one of these tools does, what a config option or port means, what a VSS signal path is, or why a tool is behaving a certain way. Also use when adding documentation to ToolDocumentation/. Not for questions about this repo's own Python code, which should be read directly.
---

# Tool documentation lookup

Questions about the tools we build on are easy to answer badly. The tools move
fast, versions differ, and an answer that is right for Zenoh 1.x may be wrong
for the version we pin. So the point of this skill is to answer from something
real and say where it came from, rather than from memory.

## Where to look, in order

**1. `ToolDocumentation/`** - documentation we have saved into the repo.
One folder per tool, lowercase: `leda/`, `zenoh/`, `kuksa/`, `vss/`.
Search it first. It matches the versions we actually run, and it works offline.

The folder may be empty or only partly filled. That is expected, not an error.

**2. The official docs on the web** - when the local folder has nothing.

| Tool | Docs |
|---|---|
| Eclipse Leda | https://eclipse-leda.github.io/leda/ |
| Eclipse Zenoh | https://zenoh.io/docs/ |
| Eclipse Kuksa | https://eclipse-kuksa.github.io/kuksa-website/ |
| COVESA VSS | https://covesa.github.io/vehicle_signal_specification/ |

When you use the web, check the version matches what we pin. If the docs
describe a different version, say so rather than quietly assuming it carries over.

## Say where the answer came from

Cite the local path (`ToolDocumentation/zenoh/config.md`) or the URL. Someone
reading the answer needs to know whether to trust it for our version, and they
cannot judge that without the source.

If neither source answers the question, say so. A guess about a port number or
a config key is worse than "I could not find this" because it looks just as
confident and sends someone debugging in the wrong direction.

## This repo's own code is not in scope

`leda/README.md` already documents our pipeline - the signals, the ports, the
setup steps, the payload format. For questions about how *our* code works, read
that and the source directly. Use this skill for the tools underneath it.

## Adding documentation to the folder

When saving a doc: put it in the tool's lowercase folder, give it a name that
says what it covers, and note the version it describes and where it came from.
A saved doc with no version is hard to trust later, because nobody can tell
whether it has gone stale.

Prefer the pages we actually reach for over a full mirror of a docs site. A
small folder people trust beats a large one they have to wade through.
