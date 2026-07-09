# Running Ollama on a friend's machine (same network)

Goal: host `llama3.1:8b` on a friend's laptop/desktop, exposed on the local
network, so the planning-intelligence dashboard (running on your machine)
can call it for the AI chat feature — useful when the Jetson is busy
(e.g. mid-training) and you're both on the same WiFi for a showcase/demo.

This is the same pattern as `docs/jetson-ollama-setup.md`, just with a
laptop/desktop instead of the Jetson.

## 1. Friend installs Ollama

- macOS: download from https://ollama.com and install normally, or
  `brew install ollama`
- Windows: download the installer from https://ollama.com
- Linux: `curl -fsSL https://ollama.com/install.sh | sh`

## 2. Friend pulls the model

```bash
ollama pull llama3.1:8b
```

~4.7GB download (quantized). Confirm with `ollama list`.

## 3. Friend exposes Ollama on the local network

By default Ollama's API only listens on `127.0.0.1:11434` (unreachable
from other machines). To allow your machine to reach it, they need to
bind to all interfaces before starting the server.

**macOS/Linux:**
```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```
(If Ollama is already running via the menu-bar app, quit it first so this
foreground command can bind the port instead.)

**Windows (PowerShell):**
```powershell
$env:OLLAMA_HOST="0.0.0.0"
ollama serve
```

## 4. Friend finds their LAN IP

- macOS: `ipconfig getifaddr en0`
- Windows: `ipconfig` (look for "IPv4 Address" under the active adapter)
- Linux: `hostname -I`

They share this IP with you (e.g. `192.168.0.87`). Must be the same
WiFi/router as your machine.

## 5. Test reachability from your machine

```bash
curl http://<FRIEND_IP>:11434/api/tags
```

Should return JSON listing `llama3.1:8b`. If it times out, check both
machines are on the same network and the friend's firewall isn't blocking
port 11434.

## 6. Point the dashboard at it

In `.env`:

```bash
OLLAMA_BASE_URL=http://<FRIEND_IP>:11434
OLLAMA_MODEL=llama3.1:8b
```

Then restart the stack:

```bash
./scripts/start_stack.sh
```

`start_stack.sh` skips launching local Ollama when `OLLAMA_BASE_URL`
doesn't point at `localhost`/`127.0.0.1` — it just verifies the remote
host is reachable instead.

## Switching back afterward

Change `OLLAMA_BASE_URL` back to `http://localhost:11434` (or the Jetson's
IP) in `.env` and restart the stack. No code changes either way — the
chat feature only ever talks to whatever `OLLAMA_BASE_URL` points at.

## Security note

Don't expose port 11434 to the public internet — Ollama's API has no
built-in authentication. Local network only, for the duration of the demo.
