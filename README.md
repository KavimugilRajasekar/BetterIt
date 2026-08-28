# AI Writer

A small system-wide writing assistant for Windows. Select text in any app, hit **Ctrl+Space**, and a tiny floating window opens with a grammar-corrected version. Click **Replace** to paste it back.

This is v1: clipboard-based, one action (Grammar), powered by the OpenAI API. No live text sync, no streaming, no per-app integrations — just the smallest honest end-to-end slice.

## Install

```bash
cd Make-It-Better
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

If `pip install -e .` complains about the `keyboard` library on Windows, try running your terminal as Administrator (the library uses a low-level keyboard hook).

## Configure

```bash
copy .env.example .env
```

Then edit `.env` and set your `OPENAI_API_KEY`. Optional: change `MODEL` or `HOTKEY`.

## Run

```bash
python run.py
```

The app starts in the background. There's no main window — just a tray icon. To quit, right-click the tray icon and choose **Quit**.

## Use

1. Type or paste text into any application (Notepad, Chrome, VS Code, Discord, Word, WhatsApp, etc.).
2. Select the text you want corrected.
3. Press **Ctrl+Space**. A small dark window appears centered on screen, showing your selected text. The original application keeps focus.
4. Click **Correct Grammar**. A spinner shows briefly, then the corrected text appears in the "Improved" pane.
5. Click **Replace**. The window hides and the corrected text is pasted into the original application.
6. Press **Esc** to dismiss the window without pasting.

## How it works

```
[any app] --select text--> Ctrl+Space
                              |
                              v
                       +-------------+
                       | read clip   |  (simulates Ctrl+C, then reads)
                       +------+------+
                              |
                              v
                       +-------------+
                       |  OpenAI LLM |  (gpt-4o-mini, grammar prompt)
                       +------+------+
                              |
                              v
                       +-------------+
                       |  show in UI |  (always-on-top floating window)
                       +------+------+
                              |
                       click Replace
                              |
                              v
                       +-------------+
                       |  paste back |  (sets clipboard, focuses source hwnd, simulates Ctrl+V)
                       +-------------+
```

## Known limitations

- **Won't work everywhere.** Apps that block programmatic copy of selected text (some terminals, some games) won't feed text to the assistant.
- **Alt-tabbing between trigger and Replace** can cause the paste to land in the wrong app. The assistant captures the foreground window's handle at trigger time, but if you switch apps, that handle is stale.
- **Single monitor assumed** for window centering.
- **No streaming** — the UI waits for the full response.
- **Windows only.** macOS and Linux would need a different `clipboard.py` (different `keybd_event` and clipboard APIs).

## What's not in v1

- Live text sync ("auto-reflect as I type" from any input field)
- More actions (Improve, Formal, Casual, Shorten, Expand, Translate, etc.)
- Local LLM (Ollama)
- OS accessibility / UI Automation for direct text replacement
- Streaming responses, history, custom prompts, settings UI, autostart
- Dark/light theme toggle
- macOS / Linux support

See the plan at `.claude/plans/` for the full phase-by-phase roadmap.

## Troubleshooting

- **Window doesn't appear on Ctrl+Space**: try running as Administrator, or check that another app (some games, some VMs) isn't capturing the hotkey.
- **"Improved" pane shows an error**: check your API key in `.env` and your internet connection. Errors are shown verbatim.
- **Replace doesn't paste**: some apps (notably some Electron apps with custom text fields) ignore simulated Ctrl+V. v1 accepts this.
