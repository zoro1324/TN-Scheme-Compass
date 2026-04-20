# TN Welfare Schemes - RAG-Powered Chatbot

A locally-running, offline-first chatbot that helps Tamil Nadu residents identify welfare schemes they are eligible for. Supports both text and speech-based interaction with Tamil-English translation.

## Features

✨ **RAG-Powered Scheme Matching**
- Vector-based similarity search using ChromaDB
- Scheme eligibility scoring based on user criteria
- Displays all matching schemes with detailed explanations

🎤 **Speech Support (Offline)**
- Speech-to-text using OpenAI Whisper (local model)
- Text-to-speech using pyttsx3 (offline engine)
- Auto-detects Tamil and English speech
- One question per speech input

🌐 **Multilingual (Tamil & English)**
- Bidirectional translation using indic-nlp library
- Auto-detects input language
- Responds in same language as user input
- All processing happens locally

🚀 **Fully Offline**
- No cloud dependencies except GroqAPI (LLM)
- Whisper model downloads on first run
- Works without internet after initial setup
- All speech processing is local

## Requirements

### System Requirements
- Python 3.8+
- 4GB RAM (minimum)
- Microphone (for speech mode, optional)
- Windows/Mac/Linux

### Dependencies
See `chatbot/requirements_chatbot.txt`

## Installation

### Step 1: Install Python Dependencies

```bash
# Install chatbot-specific packages
pip install -r chatbot/requirements_chatbot.txt
```

**Note:** On Windows, `pyaudio` installation may require Visual C++ Build Tools. If installation fails:
1. Download Microsoft Visual C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Run the installer and select "Desktop development with C++"
3. Retry the pip install

### Step 2: Set Up Environment Variables

Create a `.env` file in the project root:

```
# Required: GroqAPI key for LLM processing
GROQ_API_KEY=your_groq_api_key_here

# Optional: Customize chatbot settings
GROQ_MODEL=mixtral-8x7b-32768
WHISPER_MODEL_SIZE=base        # tiny, base, small, medium, large
SPEECH_DURATION_SECONDS=10
ENABLE_SPEECH_MODE=true
ENABLE_TTS=true
SPEECH_RATE=150                 # Words per minute
SPEECH_VOLUME=0.9               # 0.0 to 1.0
```

### Step 3: Prepare Excel Data

Ensure `tn_welfare_schemes.xlsx` is in the project root with these columns:

```
scheme_id, scheme_name, government_type, government_level, department, 
category, sub_category, benefit_type, benefit_amount, eligibility_age_min, 
eligibility_age_max, eligible_gender, eligible_caste, eligible_religion, 
income_limit_annual, residence_requirement, occupation, marital_status, 
disability_required, education_required, other_conditions, application_mode, 
documents_required, official_portal, keywords
```

### Step 4: Download Whisper Model (Optional for Text Mode)

```bash
python -c "import whisper; whisper.load_model('base')"
```

This downloads the model (~140MB) for speech-to-text. This runs automatically on first speech input if not pre-downloaded.

## Usage

### Run Chatbot

```bash
python run_chatbot.py
```

Or directly:

```bash
python -m chatbot.cli
```

### Text Mode

```
🔍 TN Welfare Schemes Eligibility Assistant
============================================================

Choose interaction mode:
  1) 📝 Text-based (type your responses)
  2) 🎤 Speech-based (speak your responses)
  3) ❌ Exit

Enter your choice (1/2/3): 1
```

Then answer eligibility questions:
- Age
- Annual household income
- Gender
- Caste category
- Religion
- Occupation
- Education level
- Marital status
- Disability status
- Residence duration

The chatbot will find and display all matching schemes with explanations.

### Speech Mode

```
Enter your choice (1/2/3): 2

🎤 Speech Mode - Scheme Eligibility Assistant
────────────────────────────────────────────────

I'll ask you questions. Speak your answers (in Tamil or English).

❓ What is your age?
🎤 Listening... (speak for up to 10 seconds)
🔤 You said: I am 30 years old
✓ Response recorded
```

Speak in Tamil or English - the system auto-detects and translates.

## Architecture

```
chatbot/
├── __init__.py                 # Package init
├── cli.py                      # Main CLI orchestrator
├── rag_retriever.py            # Vector search & embeddings
├── llm_responder.py            # GroqAPI integration
├── translator.py               # Tamil ↔ English translation
├── whisper_stt.py              # Speech-to-text (Whisper)
├── offline_tts.py              # Text-to-speech (pyttsx3)
├── eligibility_matcher.py       # Question generation & scoring
└── requirements_chatbot.txt     # Python dependencies
```

### Component Interaction

1. **CLI** - User interface (text/speech input)
2. **Translator** - Language detection & bidirectional translation
3. **Whisper STT** - Converts speech to text (locally)
4. **Eligibility Matcher** - Asks questions, scores schemes
5. **RAG Retriever** - Vector search for relevant schemes
6. **LLM Responder** - GroqAPI for final recommendations
7. **Offline TTS** - Text-to-speech output

## Features in Detail

### Scheme Matching

The chatbot uses multi-criteria matching:
- Age range validation
- Income limit checking
- Gender eligibility
- Caste category compatibility
- Religion requirements
- Education prerequisites
- Disability status
- Residence duration

Each scheme receives a **similarity score (0-1)** based on how many criteria match.

### Display Format

```
1. Scheme Name
   Category: Category Name
   Type: Benefit Type
   Benefit: ₹Amount
   Match Score: 95%

   Why this matches you:
   ✓ Age 25-45 (your age: 30)
   ✓ Income limit ₹500000 (your income: ₹300000)
   ✓ Caste: OBC
   ...

   Application Mode: Online/Offline
   Portal: Website URL
   Documents Needed: List of documents
```

### Offline Capabilities

- **Translator:** indic-nlp (offline)
- **STT:** Whisper (local model)
- **TTS:** pyttsx3 (offline)
- **Embeddings:** ChromaDB (in-memory)
- **Scheme Matching:** Local Python logic

Only GroqAPI (LLM) requires internet.

## Troubleshooting

### Issue: PyAudio Installation Fails

**Windows:**
```
1. Install Microsoft Visual C++ Build Tools
2. pip install pipwin
3. pipwin install pyaudio
```

**Mac:**
```
brew install portaudio
pip install pyaudio
```

**Linux:**
```
sudo apt-get install portaudio19-dev
pip install pyaudio
```

### Issue: "No module named 'openai-whisper'"

```bash
pip install --upgrade openai-whisper
```

### Issue: Microphone Not Detected

The chatbot will fall back to text mode automatically. Check:
- Microphone is connected and enabled
- No other application is using the mic
- Try a different USB port

### Issue: Whisper Model Download Stuck

```bash
# Pre-download the model
python -c "import whisper; whisper.load_model('base')"
```

If it takes too long, use a smaller model:
```
WHISPER_MODEL_SIZE=tiny  # ~39MB, faster but less accurate
```

### Issue: "GROQ_API_KEY not found"

Ensure `.env` file has:
```
GROQ_API_KEY=your_actual_key_here
```

Don't include quotes around the key.

### Issue: No Matching Schemes Found

- User criteria might be too restrictive
- Check that Excel data has proper values for matching fields
- Some schemes may only match if all criteria are met

## Configuration

### Whisper Model Sizes

| Size   | Parameters | RAM    | Accuracy | Speed   |
|--------|-----------|--------|----------|---------|
| tiny   | 39M       | 1GB    | 60%      | 100ms   |
| base   | 74M       | 1GB    | 75%      | 2s      |
| small  | 244M      | 2GB    | 85%      | 10s     |
| medium | 769M      | 4GB    | 92%      | 30s     |
| large  | 1550M     | 8GB    | 99%      | 60s     |

Set via `.env`:
```
WHISPER_MODEL_SIZE=base  # Default
```

### Speech Parameters

```
SPEECH_RATE=150           # Words per minute (100-200 typical)
SPEECH_VOLUME=0.9         # 0.0 (mute) to 1.0 (max)
SPEECH_DURATION_SECONDS=10  # Max recording duration
```

## Logging

Chatbot logs are saved to `chatbot.log` in the current directory.

View logs:
```bash
tail -f chatbot.log
```

Enable debug logging:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Performance Optimization

### Text Mode (Fastest)
- No audio processing
- ~1-2 seconds per question
- Ideal for quick lookups

### Speech Mode (Slower)
- Whisper transcription: 2-10s (depends on model size)
- Translation: ~1s
- Total: 3-11s per question

### Optimize Speech Speed
1. Use smaller Whisper model: `WHISPER_MODEL_SIZE=tiny`
2. Disable TTS: `ENABLE_TTS=false`
3. Use text mode for faster interaction

## API Costs

- **Whisper:** ✅ Free (local)
- **Translation:** ✅ Free (local)
- **TTS:** ✅ Free (local)
- **GroqAPI:** ~$0.005 per conversation (depends on usage)

Total cost per conversation: ~$0.005 USD

## Limitations

1. **Translation Quality:** indic-nlp transliteration is basic. May not handle all Tamil/English code-mixing perfectly.
2. **Scheme Matching:** Limited to criteria in Excel. Complex eligibility rules need LLM support.
3. **Speech Accuracy:** Depends on audio quality and background noise.
4. **Tamil Support:** Limited to Tamil script. Regional dialects may not transcribe perfectly.

## Future Enhancements

- [ ] Support for more Indian languages
- [ ] Integration with official gov APIs for real-time scheme updates
- [ ] Chatbot fine-tuning on Tamil Nadu welfare schemes
- [ ] Web interface (in addition to CLI)
- [ ] Persistent conversation history
- [ ] Context-aware follow-up questions

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check troubleshooting section above
2. Review `chatbot.log` for error details
3. Open an issue on GitHub with:
   - Python version
   - OS (Windows/Mac/Linux)
   - Error message
   - Steps to reproduce

## Contact

For questions about welfare schemes, contact:
- **Tamil Nadu Social Welfare Department:** https://www.swd.tn.gov.in/
- **Local Welfare Office:** Contact your nearest office

---

**Last Updated:** April 2026
**Version:** 0.1.0
