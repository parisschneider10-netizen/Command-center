# LiveKit Voice Agent (Phase 2)

Sovereign replacement for Vapi. Same SARA persona. Same Voice OS tools.

## Status: stub — enable when Vapi loop is proven

## Architecture

```text
Phone → Telnyx SIP → LiveKit SIP → Agent Worker (this folder)
                                         ↓
                              Voice OS /voice/tools/*
                                         ↓
                              vault · n8n · Command Center
```

## Prerequisites

- [ ] Voice OS deployed and working on VPS
- [ ] Vapi loop tested (you can skip Vapi cancel until this works)
- [ ] ElevenLabs voice chosen (or Piper for local TTS)
- [ ] Telnyx account + SIP trunk (or LiveKit Phone Numbers)
- [ ] LiveKit Server (self-hosted or Cloud)

## Environment variables (future)

```env
LIVEKIT_URL=wss://your-livekit-server
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
VOICE_OS_BASE_URL=https://your-domain.com
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
OPENAI_API_KEY=          # for LLM
DEEPGRAM_API_KEY=        # for STT (or use Whisper local)
```

## Tool mapping

The LiveKit agent calls the same endpoints Vapi uses:

| SARA action | HTTP endpoint |
|-------------|---------------|
| Create task | `POST /voice/tools/create_task` |
| Briefing | `POST /voice/tools/get_briefing` |
| Log note | `POST /voice/tools/log_note` |
| Dump to vault | `POST /voice/tools/dump_to_vault` |
| Queue decision | `POST /voice/tools/queue_decision` |
| Trigger workflow | `POST /voice/tools/trigger_workflow` |

## System prompt

Load from: `docs/prompts/sara-system-prompt.txt`

## Next step when ready

We will add:
- `agent.py` — LiveKit agent with SARA persona
- `tools.py` — HTTP client for Voice OS
- `Dockerfile` — deploy alongside api in docker-compose
- Uncomment `livekit-agent` service in docker-compose.yml

For now, use Vapi with the updated SARA config in `docs/vapi-assistant.json`.

See [VOICE_STACK.md](../VOICE_STACK.md) for the full comparison.
