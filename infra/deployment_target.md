# Deployment Target Decision

**Date:** 2026-04-08  
**Status:** Current deployment decision for the present product stage

## Goal

Choose a realistic deployment approach that fits the app as it exists today:

- containerized with Docker
- single-user internal decision-support usage
- filesystem-based persistence for history and cache
- minimal operational complexity

## Evaluated deployment options

| Option | Pros | Cons |
| --- | --- | --- |
| Local-only analyst machine | Simplest to run; no infrastructure work; matches development flow | Not a stable shared runtime; depends on one workstation; weaker operational consistency |
| **Single VM + Docker** | Aligns with the current Dockerized app; supports mounted filesystem persistence; low operational overhead; suitable for controlled internal use | Single point of failure; manual operations; limited scaling and resilience |
| Managed container platform | Better long-term scaling and environment management potential | Adds infrastructure complexity, external storage design, secret management, and operational overhead not yet justified |

## Selected approach

**Chosen target: single VM + Docker**

## Reasoning for selection

This is the best fit for the app's current stage because:

1. The application already runs as a single containerized Python service.
2. The current user model is small-scale and internal, not public or multi-tenant.
3. History and cache are filesystem-based, which fits naturally on a VM with mounted local storage.
4. The team can get predictable deployment behavior without introducing premature platform complexity.
5. It preserves a clear path to evolve later if the product scope expands.

## What this decision does not imply yet

This document records the deployment **direction only**. It does not introduce:

- infrastructure-as-code
- cloud-specific deployment configuration
- orchestration or autoscaling
- authentication or broader access controls

## Revisit triggers

Re-evaluate this choice if any of the following change:

- the app moves beyond single-user or tightly controlled internal use
- uptime/resilience requirements increase materially
- persistence needs move beyond local filesystem storage
- operational ownership expands to a broader team or product environment
