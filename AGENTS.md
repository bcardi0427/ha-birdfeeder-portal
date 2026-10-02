# Agent Directives & Workspace State Guardrails

## Overview
This workspace uses the `update-state-log` plugin to maintain structural memory and architectural continuity across agent sessions in `.agents/state_log.json` and `.agents/history.log`.

## Guidelines for Agents
1. **Check State Before Action**: Always check `.agents/state_log.json` to review recent objectives, active blockers, and solved milestones.
2. **Record Fixes & Milestones**: When solving issues, fixing integrations, or achieving milestones, log them using the `update-state-log` skill:
   `python "C:\Users\Bcardi\.gemini\config\plugins\state-tracker-plugin\skills\index.py" --workspace "f:\AntiGravity Sources\ha-birdfeeder-portal" ...`
3. **Do Not Regress Solutions**: Review historical resolutions documented in `.agents/history.log` before altering redirect logic, port mappings, CORS/iframe headers, or referrer tracking.
