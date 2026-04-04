---
title: SQL Antigravity Env
emoji: 🛢️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - sql
  - reinforcement-learning
---

# SQL Antigravity Environment

A real-world OpenEnv environment where AI agents learn to review SQL queries for syntax errors, performance anti-patterns, and security vulnerabilities.

## Tasks
- **Easy**: Detect misspelled SQL keywords
- **Medium**: Identify SELECT * and missing WHERE clause on 50M row table  
- **Hard**: Detect SQL injection via f-string interpolation

## API Endpoints
- GET /health — health check
- GET /schema — action and observation schemas
- WebSocket /ws — main environment interface

## Quick Start
pip install git+https://huggingface.co/spaces/sakthi0706/sql-antigravity-env
