# Running Ollama + llama3.1:8b on Jetson AGX Orin

Goal: host `llama3.1:8b` on the Jetson via Ollama, exposed on the local
network so the planning-intelligence dashboard (running on your Mac) can
call it for the AI chat feature.

## 1. Install Ollama on the Jetson

Jetson AGX Orin runs aarch64 Linux (JetPack/L4T), which Ollama supports
directly — no Docker required.

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

This installs Ollama as a systemd service and starts it automatically.

Verify it's running:

```bash
systemctl status ollama
```

## 2. Confirm GPU is being used

Ollama on Jetson uses the CUDA backend built into L4T. Check the logs on
first model load to confirm GPU offload (not falling back to CPU-only):

```bash
journalctl -u ollama -f
```

You should see CUDA/GPU initialization lines when a model is loaded. If it
falls back to CPU, verify JetPack/CUDA is installed and up to date
(`nvidia-smi` or `tegrastats` should show the GPU).

## 3. Pull the model

```bash
ollama pull llama3.1:8b
```

This downloads roughly 4.7GB (quantized). Confirm it's available:

```bash
ollama list
```

## 4. Quick local test (on the Jetson itself)

```bash
ollama run llama3.1:8b "Reply with exactly the JSON: {\"ok\": true}"
```

Confirm it returns clean JSON-ish output. This is the behavior the chat
feature depends on (structured filter extraction).

## 5. Expose Ollama on the local network

By default, Ollama's API binds to `127.0.0.1:11434` — only reachable from
the Jetson itself. To let your Mac reach it, bind to all interfaces.

Edit the systemd override:

```bash
sudo systemctl edit ollama
```

Add:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Then reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

## 6. Find the Jetson's IP address

```bash
hostname -I
```

Note the LAN IP (e.g. `192.168.1.50`). This only works if the Jetson and
your Mac are on the same local network (same Wi-Fi/router). No port
forwarding or public exposure needed — and don't expose port 11434 to the
public internet, since Ollama's API has no built-in auth.

## 7. Test reachability from your Mac

```bash
curl http://<JETSON_IP>:11434/api/tags
```

Should return JSON listing `llama3.1:8b` among installed models. If this
times out:
- Check both devices are on the same network/subnet
- Check the Jetson's firewall (`ufw status`) isn't blocking port 11434
- Re-check `OLLAMA_HOST` took effect: `systemctl show ollama -p Environment`

## 8. Point the dashboard at it

Once reachable, set in the dashboard's environment (e.g. `.env` in the
worktree, or exported before running uvicorn):

```bash
LLM_BACKEND=ollama
OLLAMA_BASE_URL=http://<JETSON_IP>:11434
OLLAMA_MODEL=llama3.1:8b
```

Restart the dashboard (`uvicorn src.web.main:app --reload --port 8000`) and
the `/chat` page will route questions to the Jetson.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `curl` from Mac hangs/times out | Different subnets, or Jetson firewall blocking 11434 |
| Ollama falls back to CPU (slow) | JetPack/CUDA not properly installed or too old |
| Model responses aren't valid JSON | Expected sometimes even from 8B models — the chat feature has a fallback path for this, not a setup bug |
| `OLLAMA_HOST` change didn't apply | Confirm with `systemctl show ollama -p Environment`, restart again |
