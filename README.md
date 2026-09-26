# Bird Feeder Voice Assistant Portal (Home Assistant HACS Integration)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)

A dedicated Home Assistant custom integration and web portal that monitors your bird feeder in real-time using an external **Frigate NVR** and answers visitor questions with spoken voice audio via **Gemini / Home Assistant Assist** and **Nabu Casa Cloud TTS**.

---

## Features

- **Dedicated Web Portal**: Runs an async web server directly inside Home Assistant on your configured port (default `8095`).
- **External Frigate Integration**: Queries your external Frigate NVR (e.g. `http://192.168.1.90:5000`) over the LAN for live species sightings, visit counts, and snapshot imagery.
- **Native Voice & AI Intelligence**:
  - Leverages Home Assistant's conversational agent (`conversation.google_ai_conversation` / Gemini) grounded with real-time feeder statistics.
  - Generates spoken voice audio via Nabu Casa Cloud TTS (`tts.home_assistant_cloud` / `AmberNeural`).
  - No hardcoded access tokens or internet roundtrips needed for authentication.
- **Home Assistant Sidebar & Dashboard**: Automatically registers an iframe panel in the Home Assistant sidebar to view the interactive portal directly inside your HA UI.
- **Native HA Sensor Entities**:
  - `sensor.birdfeeder_today_views` (Page views today)
  - `sensor.birdfeeder_today_questions` (Voice queries answered today)
  - `sensor.birdfeeder_total_views` (All-time views)
  - `sensor.birdfeeder_total_questions` (All-time questions)
  - `sensor.birdfeeder_last_visitor` (Species name and attributes)
  - `sensor.birdfeeder_visits_today` (Total bird visits today with species breakdown)
- **Public Domain Ready**: Perfect for exposing to friends and family through a Cloudflare Tunnel at `https://birdfeeder.bcardi.org` without requiring Home Assistant user accounts.

---

## Installation via HACS

1. Open **HACS** in your Home Assistant UI.
2. Click the three dots in the top-right corner and select **Custom repositories**.
3. Paste the URL of this repository: `https://github.com/bcardi0427/ha-birdfeeder-portal`
4. Select category **Integration** and click **Add**.
5. Find **Bird Feeder Voice Portal** in the list and click **Download**.
6. Restart Home Assistant.

---

## Setup & Configuration

1. In Home Assistant, go to **Settings ➔ Devices & Services ➔ Add Integration**.
2. Search for **Bird Feeder Voice Portal**.
3. Configure the following parameters:

| Setting | Default | Description |
| :--- | :--- | :--- |
| **Frigate NVR URL** | `http://192.168.1.90:5000` | The LAN address and port of your Frigate NVR instance. |
| **Frigate Camera Name** | `feeder` | The camera name configured in Frigate for the feeder. |
| **Dedicated Port** | `8095` | Port on which Home Assistant serves the portal webpage and API. |
| **Conversation Agent** | `conversation.google_ai_conversation` | Home Assistant conversation entity (e.g. Gemini). |
| **TTS Engine** | `tts.home_assistant_cloud` | Nabu Casa Cloud or local TTS engine entity. |
| **TTS Voice** | `AmberNeural` | Voice model for audio synthesis. |

> **Note**: You can adjust these settings at any time by clicking **Configure** on the integration card.

---

## Cloudflare Tunnel Setup (Public Access)

If you are migrating from running on a Frigate LXC container to Home Assistant:

1. Open your Cloudflare Zero Trust Dashboard (or local `cloudflared` config).
2. Update the public hostname route for `birdfeeder.bcardi.org`:
   - **Old Origin**: `http://192.168.1.90:8095` (Frigate LXC)
   - **New Origin**: `http://192.168.1.79:8095` (Home Assistant)
3. Save changes. Visitors can now query the portal at `https://birdfeeder.bcardi.org` without needing HA login credentials.

---

## Architecture

```
[Public Visitor / Cloudflare] ──► http://192.168.1.79:8095 (Bird Feeder Portal Web Server)
                                            │
               ┌────────────────────────────┼───────────────────────────┐
               ▼                            ▼                           ▼
[External Frigate REST API]     [HA Conversation Agent]      [HA Cloud TTS Engine]
 http://192.168.1.90:5000         conversation.google_ai      tts.home_assistant_cloud
 (Events & Snapshots)             (Grounded with Context)     (Direct Audio Stream)
```

---

## License

This project is licensed under the [MIT License](LICENSE).
