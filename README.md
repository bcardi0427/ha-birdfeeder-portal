# Bird Feeder Voice Assistant Portal (Home Assistant HACS Integration)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)

A dedicated Home Assistant custom integration and interactive web portal that monitors your bird feeder in real-time using **Frigate NVR** (running either as a **Home Assistant Add-on** or on a **separate external server/LXC/Docker host**). It answers visitor questions with spoken voice audio powered by **Home Assistant Assist / Gemini** and **Text-to-Speech (TTS)**.

---

## 🌟 Key Features

- **Dedicated Web Portal**: Runs an async web server directly inside Home Assistant on your chosen port (default `8095`).
- **Flexible Frigate Connectivity**:
  - Works with the **Home Assistant Frigate Add-on** (`http://ccab4aaf-frigate:5000` or `http://127.0.0.1:5000`).
  - Works with **External Frigate Servers** (`http://<YOUR_FRIGATE_IP>:5000`, e.g. Docker, Proxmox LXC, TrueNAS, Unraid, Raspberry Pi, or bare-metal).
- **Native Voice & AI Intelligence**:
  - Leverages any Home Assistant conversation agent (Google Gemini AI, OpenAI ChatGPT, Anthropic Claude, or local LLMs like Ollama) grounded with live feeder visit data and species counts.
  - Synthesizes spoken voice audio through Nabu Casa Cloud TTS or local TTS engines (such as Piper).
  - No hardcoded API tokens or insecure credentials—uses native Home Assistant internal Python APIs.
- **Home Assistant Sidebar Panel**: Automatically adds an interactive **Bird Feeder** panel to your Home Assistant sidebar for quick viewing.
- **Native HA Sensor Entities**:
  - `sensor.birdfeeder_today_views` (Portal page visits today)
  - `sensor.birdfeeder_today_questions` (Voice questions answered today)
  - `sensor.birdfeeder_total_views` (All-time portal visits)
  - `sensor.birdfeeder_total_questions` (All-time questions asked)
  - `sensor.birdfeeder_last_visitor` (Species name and attributes including visit time, minutes ago, and Gemini description)
  - `sensor.birdfeeder_visits_today` (Total bird visits today with full species breakdown)
- **Optional Public Access**: Expose the portal to family, friends, or bird-watching clubs via Cloudflare Tunnel, Nginx, or reverse proxy without giving them access to your Home Assistant dashboard.

---

## 🏗️ Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │                HOME ASSISTANT HOST                     │
                               │                                                        │
[Public / Local Visitors] ────►│  Port 8095: Bird Feeder Voice Portal Web Server        │
                               │  ├── Serves responsive HTML5/JS frontend               │
                               │  ├── Tracks visitor & question statistics              │
                               │  └── Exposes native HA sensors (views, questions, etc) │
                               │                                                        │
                               │  Direct Internal Python Integration:                   │
                               │  ├── Conversation Agent (Gemini / ChatGPT / Claude)    │
                               │  └── Text-to-Speech (Nabu Casa Cloud TTS / Piper)      │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                                         LAN HTTP /api/events & snapshots
                                                          │
                                                          ▼
                        ┌───────────────────────────────────────────────────────────────┐
                        │                         FRIGATE NVR                           │
                        │                                                               │
                        │  Option A: Home Assistant Frigate Add-on                      │
                        │            (http://ccab4aaf-frigate:5000 or 127.0.0.1:5000)   │
                        │                                                               │
                        │  Option B: External Server / Docker / Proxmox LXC             │
                        │            (http://<YOUR_FRIGATE_IP>:5000)                    │
                        └───────────────────────────────────────────────────────────────┘
```

---

## 📦 Installation via HACS

1. In Home Assistant, open **HACS ➔ Integrations**.
2. Click the **three dots** in the top-right corner and select **Custom repositories**.
3. Add repository:
   - **URL**: `https://github.com/bcardi0427/ha-birdfeeder-portal`
   - **Type**: `Integration`
4. Click **Add**.
5. Locate **Bird Feeder Voice Portal** in the HACS store and click **Download**.
6. Restart Home Assistant (**Developer Tools ➔ Restart**).

---

## ⚙️ Configuration

1. In Home Assistant, navigate to **Settings ➔ Devices & Services ➔ Add Integration**.
2. Search for **Bird Feeder Voice Portal**.
3. Fill in your environment parameters:

| Setting | Example / Default | Description |
| :--- | :--- | :--- |
| **Frigate NVR URL** | `http://ccab4aaf-frigate:5000` *(Add-on)*<br>`http://192.168.1.100:5000` *(External)* | URL to your Frigate instance. See [Frigate Setup Options](#-frigate-setup-options) below. |
| **Frigate Camera Name** | `feeder` | The name of the camera tracking the feeder inside your Frigate `config.yml`. |
| **Dedicated Port** | `8095` | Local TCP port for the portal web server. |
| **Conversation Agent** | `conversation.google_ai_conversation` | The entity ID of your Home Assistant conversation agent (Gemini, ChatGPT, Ollama, etc.). |
| **TTS Engine** | `tts.home_assistant_cloud` | The entity ID of your TTS engine (Nabu Casa Cloud, Piper, etc.). |
| **TTS Voice** | `AmberNeural` | Desired voice name supported by your TTS engine. |

> [!TIP]
> You can change any of these settings at any time by navigating to **Settings ➔ Devices & Services ➔ Bird Feeder Voice Portal ➔ Configure**.

---

## 🔎 Frigate Setup Options

### Option 1: Frigate Running as a Home Assistant Add-on
If you use the official Home Assistant Frigate Add-on on the same machine:
- Set **Frigate NVR URL** to:
  ```
  http://ccab4aaf-frigate:5000
  ```
  *(or `http://127.0.0.1:5000` if port 5000 is mapped directly to the host)*.

### Option 2: Frigate on an External Machine (LXC, Docker, VM, NAS)
If Frigate runs on a dedicated mini-PC, Proxmox LXC container, Unraid server, or separate Docker host:
- Set **Frigate NVR URL** to the LAN IP and port of that machine, for example:
  ```
  http://192.168.1.100:5000
  ```
- Ensure port `5000` on the Frigate host is accessible across your local network from Home Assistant.

---

## 🌐 Public Access & Cloudflare Tunnel (Optional)

If you wish to make the web portal accessible to outside visitors without granting them access to your Home Assistant dashboard:

1. In Cloudflare Zero Trust (or your reverse proxy of choice), create a public hostname (e.g. `birdfeeder.yourdomain.com`).
2. Point the service URL directly to your Home Assistant's IP and the configured portal port:
   ```
   http://<YOUR_HA_IP>:8095
   ```
3. The portal serves a standalone responsive web application that allows visitors to ask questions, listen to TTS audio, and see the latest bird snapshot without requiring Home Assistant user authentication.

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).
