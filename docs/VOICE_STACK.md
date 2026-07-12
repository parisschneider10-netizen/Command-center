# Voice Stack — Sovereign Options

Replace Vapi when you're ready. Same Voice OS backend. Same SARA persona. Different phone pipe.

## The split

```text
PHONE LAYER (replaceable)          YOUR STACK (you own)
─────────────────────────          ────────────────────
Vapi (now)                    →    Voice OS API
LiveKit (later)               →    same /voice/tools/*
Telnyx SIP + LiveKit          →    same webhooks, vault, n8n
```

Voice OS doesn't care who answers the phone. It exposes HTTP tools. Vapi and LiveKit both call them.

## Option comparison

| | Vapi | LiveKit (self-hosted) |
|---|------|----------------------|
| **Ownership** | Their platform | Apache 2.0, your VPS |
| **Phone calls** | Built-in number | SIP + Telnyx/Wavix/LiveKit numbers |
| **Complexity** | Low (you have this) | Medium — worth it for sovereignty |
| **Cost** | Per-minute pricing | VPS + SIP trunk (~cheaper at volume) |
| **TTS choice** | ElevenLabs, etc. | ElevenLabs, Piper, Cartesia, OpenAI — your pick |
| **Best for** | Phase 1, prove the loop | Phase 2+, full ownership |

**Recommendation:** Keep Vapi until the voice loop works (call → task → portal). Migrate to LiveKit when you're calling daily and want to own the stack.

## LiveKit migration path (Phase 2)

```text
Your phone number (Telnyx SIP trunk)
        ↓
LiveKit SIP service (on your VPS)
        ↓
LiveKit Agent worker (Python) — SARA persona
        ↓
Voice OS /voice/tools/* (same endpoints as Vapi)
        ↓
vault + n8n + Command Center
```

What you self-host:
- LiveKit Server (or LiveKit Cloud free tier to start)
- LiveKit Agents worker (`agents/livekit/`)
- SIP trunk from Telnyx (~$0.004/min) or similar

What stays the same:
- All Voice OS tools
- SARA system prompt (`docs/prompts/sara-system-prompt.txt`)
- Obsidian vault, n8n, portal

See `agents/livekit/README.md` for the stub.

## TTS — voice options (try before you pay)

### ElevenLabs (best quality, try free first)

| Plan | Cost | What you get |
|------|------|-------------|
| **Free** | $0, no credit card | 10,000 credits/mo (~10–20 min with Flash model) |
| Starter | $5/mo | 30k credits |

**Free tier tips for SARA:**
- Use **Flash v2.5** — 0.5 credits/char = ~20 min/mo of short responses
- SARA speaks ≤15 words → ~750 chars/call → **~25+ calls/month free**
- Pick a calm female voice from the library or use Voice Design
- No commercial license on free tier (fine for personal empire ops)

Sign up: https://elevenlabs.io — test voices before subscribing.

### Alternatives if ElevenLabs isn't right

| TTS | Sovereign? | Free? | Notes |
|-----|-----------|-------|-------|
| **Piper** | ✅ Fully local | ✅ Free | Runs on VPS, no API. Good enough for SARA. |
| **OpenAI TTS** | ⚠️ API | Pay-per-use | Cheap, reliable, not local |
| **Cartesia** | ⚠️ API | Trial available | LiveKit plugin, low latency |
| **Deepgram Aura** | ⚠️ API | Credits | Bundled with their STT |
| **Coqui XTTS** | ✅ Self-host | ✅ Free | Open source, GPU helps |

**Sovereign path:** Start ElevenLabs free trial → if you outgrow it, add Piper locally for TTS and keep ElevenLabs only for portal previews.

## STT (speech-to-text)

You need something to hear you. Options:

| STT | Notes |
|-----|-------|
| **Deepgram** | Fast, LiveKit plugin, free credits to start |
| **Whisper (local)** | Fully sovereign, runs on VPS |
| **AssemblyAI** | Good accuracy, API |

LiveKit Agents supports all of these as plugins — swap without rebuilding.

## Recommended phased approach

### Now (Vapi + ElevenLabs free)
1. Sign up ElevenLabs free — no credit card
2. Pick/design a SARA-like voice
3. Update `docs/vapi-assistant.json` with voice ID + SARA prompt
4. Test: call → yes/no flow → task in portal

### Later (LiveKit sovereign)
1. Deploy LiveKit Server on VPS (or Cloud free tier)
2. Get Telnyx SIP trunk + port your number
3. Deploy `agents/livekit/` worker with same SARA prompt
4. Point tools at same Voice OS URLs
5. Cancel Vapi

## Cost estimate (LiveKit sovereign, daily use)

Rough math for ~5 min/day of calls:

| Item | ~Monthly |
|------|----------|
| VPS (already have) | $0 marginal |
| Telnyx SIP | ~$2–5 |
| ElevenLabs free | $0 |
| Whisper local STT | $0 |
| **Total** | **~$2–5/mo** |

vs Vapi per-minute pricing at same volume — often $15–30+/mo.

## Legal note on "SARA" voice

Toonami SARA is a copyrighted character. Don't clone the actual voice without rights. **Persona** (concise, binary, co-pilot style) is fine. **Voice clone** of the actress — legally risky. Use Voice Design to get close in spirit, not a direct copy.
