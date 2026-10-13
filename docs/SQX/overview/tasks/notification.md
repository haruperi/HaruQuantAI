# Notification task

> Show a notification or send an email when the project reaches a certain point.

## What it does

The Notification task can display a notification or send you an email when the project gets to a
certain point in its flow. It can also optionally pause the project and wait until the user starts it
again — useful when you want to manually review generated strategies before continuing. A common use
is to get an email when a custom project finishes.

## Options

The source describes the following behaviors:

- **Display a notification** or **send an email** at this point in the pipeline.
- Optionally **pause the project** and wait for the user to resume it (for manual review).

## Typical use in a workflow

Place it at the end of a long unattended run to email you the result, or before a critical step so
the pipeline pauses for a manual review before continuing.

## Related

- [Custom Projects & the task model](../custom-projects.md)
- [Tasks reference](README.md)
- Sibling tasks: [Wait for](wait-for.md), [Stop & Start](stop-and-start.md)
