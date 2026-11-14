---
name: system-design
description: Reads and maintains SystemDesign.md, the single file holding this project's intended system design - what each stage of the pipeline is for, the contracts between them, and the decisions behind them. Use before changing how components talk to each other, when a design question comes up, when something in the code contradicts the design, and after a design decision is made so the file stays current. Also use when asked what the system is supposed to do, as opposed to what the code currently does.
---

# Intended system design

`SystemDesign.md` at the repo root holds what this system is *meant* to be.
The code says what it currently does; those two drift apart, and when they do
it is often the code that is wrong. Keeping one shared description of the
intent is what makes that drift visible instead of invisible.

Read it before changing anything that crosses a boundary between components.

## Reading it

Quote what the file says and cite the section. If the answer is not in there,
say so plainly rather than inferring intent from the code - the whole point of
the file is to be the place where intent is recorded, and an inferred answer
presented as design quietly turns one person's guess into everybody's
assumption.

## When code and design disagree

Say so explicitly, and do not quietly change either one. Show both sides -
what the design says, what the code does, with file and line. Either the code
has a bug or the design is out of date, and that is a call for the team, not
something to resolve by editing whichever is closer to hand.

## Updating it

Update the file when a decision is actually made, not when one is being
discussed. Write what was decided and why. The reasoning matters more than the
decision: six weeks later the decision is visible in the code anyway, but the
constraint that forced it is not, and that is what someone needs in order to
judge whether it still holds.

Keep it current rather than keeping a history. This is one living document, not
a log of every decision ever made. When something is superseded, replace it -
git already holds the history, and a file that accumulates dead sections stops
being worth reading.

Mark genuinely open questions as open. A design file that pretends to be
complete is less useful than one that admits where the team has not decided yet.

## Structure

Keep the file organised around the pipeline stages, so a reader can find the
part they are touching. For each stage: what it is for, what it receives, what
it produces, and anything load-bearing about how it behaves.

Record the contracts between stages - the message shapes, key names, units,
field names. Those are what break when two people change things independently,
and they break silently, which makes them worth writing down even when they
feel obvious.

Keep it short enough that people actually read it before making changes.
