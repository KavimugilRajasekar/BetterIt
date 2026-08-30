# Better It

A system-wide writing assistant for Windows. Select text in any application, press Ctrl+Space, and a floating window opens with a grammar-corrected version. Click Replace to paste it back.

## Demo

<video src="public/demo.mp4" controls width="600"></video>

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

If pip install -e . fails due to the keyboard library on Windows, run the terminal as Administrator.

## Configuration

```bash
copy .env.example .env
```

Edit .env to set your OPENAI_API_KEY. You may also modify MODEL or HOTKEY.

## Execution

```bash
python run.py
```

The application runs in the background with a tray icon. To exit, right-click the tray icon and select Quit.

## Usage

1. Select text in any application.
2. Press Ctrl+Space.
3. Click Correct Grammar.
4. Click Replace to paste the improved text.
5. Press Esc to dismiss the window.

## Application Pipeline

The application operates in a linear pipeline:

1. Trigger: The system monitors for the Ctrl+Space hotkey.
2. Extraction: Upon trigger, the application simulates a Ctrl+C command to capture the currently selected text from the active window.
3. Processing: The captured text is transmitted to the LLM API with a specific grammar correction prompt.
4. Presentation: The resulting text is rendered in an always-on-top floating window for user review.
5. Integration: Upon clicking Replace, the application sets the system clipboard to the new text and simulates a Ctrl+V command to insert it into the original application.

## Known Limitations

- Certain applications that block programmatic clipboard access may not work.
- Switching active windows between trigger and replacement can cause the paste to land in the wrong application.
- Centering is optimized for single-monitor setups.
- Responses are not streamed; the UI waits for the full API response.
- Windows only.

## Future Roadmap

- Live text synchronization.
- Additional actions such as Formal, Casual, Shorten, and Expand.
- Local LLM integration via Ollama.
- OS accessibility and UI Automation for direct replacement.
- Settings UI and autostart capabilities.
- Theme toggles.
- Cross-platform support for macOS and Linux.

## Troubleshooting

- Hotkey not working: Run as Administrator or check for hotkey conflicts.
- API Errors: Verify API key and internet connectivity.
- Paste failure: Some Electron applications may ignore simulated Ctrl+V.

## Collaboration

We welcome contributions. Please refer to the following files for more information:
- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
