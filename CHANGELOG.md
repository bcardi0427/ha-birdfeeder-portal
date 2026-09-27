# Changelog

All notable changes to the **Bird Feeder Voice Portal** integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.9] - 2026-09-26

### Changed
- **Privacy & Role-Based Analytics Visibility**: Restricted the "📊 Analytics" link to only show when viewing the portal inside Home Assistant (sidebar panel iframe or `?ha=1`). Public internet visitors to `bf.bcardi.org` will not see or access the analytics link.

---

## [1.0.8] - 2026-09-26

### Added
- **Dedicated Analytics & Stats Dashboard (`/stats`)**: Added a responsive, dark-mode real-time analytics web dashboard (`/stats` and `/stats.html`) featuring live KPI cards (Today Views, Total Views, Today Questions, Total Questions), visual referral source progress bars (Reddit, HA Community, Discord, Search, Direct) with Today/All-Time toggles, and daily historical visitor logs.
- **Portal Navigation**: Added a quick "📊 Analytics" link in the web portal footer connecting directly to the stats dashboard.

---

## [1.0.7] - 2026-09-26

### Added
- **HTTP Referrer Analytics & Tracking**: Captures incoming HTTP `Referer` headers from web visitors (identifying sources like `reddit.com`, `community.home-assistant.io`, `discord.com`, search engines, and direct visits).
- **Referrer Sensor Attributes**: Exposes daily and all-time referrer breakdowns directly in Home Assistant as extra state attributes on `sensor.birdfeeder_today_views` and `sensor.birdfeeder_total_views`.
- **API Analytics**: Adds `today_referrers` and `referrers` breakdown into `/api/stats` endpoint.

---

## [1.0.6] - 2026-09-26

### Added
- **Web Speech API Fallback**: Added automatic browser speech synthesis (`window.speechSynthesis`) fallback so the voice assistant speaks audibly even if browser iframe autoplay restrictions block the audio stream.

### Fixed
- **Modern Media Source TTS Generation**: Migrated TTS audio URL resolution to Home Assistant's modern `media_source` engine (`generate_media_source_id` + `async_resolve_media`), resolving silent audio caused by legacy unauthenticated endpoints.

---

## [1.0.5] - 2026-09-26

### Fixed
- **Sensor Dispatcher AttributeError**: Fixed `AttributeError: 'HomeAssistant' object has no attribute 'helpers'` in `sensor.py` by properly importing `async_dispatcher_connect`.
- **Sidebar 404 Resolution**: Registered internal Home Assistant HTTP view at `/api/birdfeeder_portal/redirect` to dynamically detect the browsing hostname/IP and cleanly load the portal in the left sidebar without 404 errors.

---

## [1.0.4] - 2026-09-26

### Changed
- **Default Port Changed to 8195**: Changed default web server port from `8095` to `8195` to avoid port collision with Music Assistant (which binds to `8095`).

---

## [1.0.3] - 2026-09-26

### Added
- **HTTP Basic Authentication**: Added optional username and password configuration support for secured or password-protected Frigate NVR instances.

---

## [1.0.2] - 2026-09-26

### Security
- **Sanitized Configurations**: Replaced private network references in documentation with generic placeholders and verified zero hardcoded credentials across the repository.

---

## [1.0.1] - 2026-09-26

### Documentation
- **Architecture & Setup Guides**: Added detailed setup guides for both the official Home Assistant Frigate Add-on and external Frigate hosts (Proxmox LXC, Docker, Unraid).

---

## [1.0.0] - 2026-09-26

### Added
- Initial release of the **Bird Feeder Voice Portal** custom integration for Home Assistant.
- Dedicated standalone aiohttp web server serving the responsive frontend.
- Frigate REST API client for querying live bird visitor events and snapshots.
- Native Home Assistant Conversation Agent (Gemini / ChatGPT / Claude / local LLM) grounding.
- Text-to-Speech (TTS) voice generation.
- Home Assistant left sidebar panel integration.
- Native Home Assistant sensor entities (`today_views`, `today_questions`, `total_views`, `total_questions`, `last_visitor`, `visits_today`).
