# Deployment Target Decision

**Date:** 2026-04-17  
**Status:** Current deployment decision for the present product stage

## Goal

Choose a realistic deployment approach that fits the app as it exists today:

- FastAPI backend plus React frontend
- fastest viable public cloud deployment path
- SQLite retained temporarily for low-friction persistence
- GitHub-connected automatic deployment

## Evaluated deployment options

| Option | Pros | Cons |
| --- | --- | --- |
| Single VM + Docker | Low complexity and good control over mounted storage | More manual operations and less frictionless delivery than the current cloud goal |
| **Render backend + Vercel frontend** | Fastest viable managed deployment path; easy GitHub auto deploys; minimal infrastructure work; keeps frontend/backend separation aligned with the app as built | SQLite remains a temporary compromise and requires explicit disk posture on Render |
| Fully managed multi-service cloud stack | Better long-term resilience and scaling potential | Higher setup cost and unnecessary complexity for the current phase |

## Selected approach

**Chosen target: Render for backend, Vercel for frontend**

## Reasoning for selection

This is the best fit for the app's current stage because:

1. The backend and frontend are already separated cleanly enough to deploy independently.
2. Render and Vercel provide the lowest-friction GitHub-connected deployment path for the current product stage.
3. SQLite can remain temporarily viable if Render uses a mounted disk and the storage path is explicit.
4. This path improves operational accessibility without forcing a database migration yet.
5. It preserves a straightforward future upgrade path toward managed databases and richer delivery workflows.

## What this decision does not imply yet

This document records the deployment **direction only**. It does not introduce:

- managed database migration
- autoscaling architecture redesign
- advanced secret-management posture beyond platform environment variables
- blue/green or staged rollout workflows

## Revisit triggers

Re-evaluate this choice if any of the following change:

- SQLite durability on Render becomes insufficient
- preview and production environments need stronger isolation
- operational complexity or team size justifies richer release automation
- uptime or resilience requirements exceed a single Render web service plus disk
