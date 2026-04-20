# Quick Start Guide - TN Welfare Schemes Chatbot

## 🚀 Get Started in 3 Steps

### Step 1: Install

```bash
python setup_chatbot.py
```

This wizard will:
- Install all dependencies
- Download Whisper speech model
- Configure your API keys
- Test audio and imports

### Step 2: Configure

Add your GroqAPI key to `.env`:

```
GROQ_API_KEY=your_key_here
```

Get a free key: https://console.groq.com/

### Step 3: Run

```bash
python run_chatbot.py
```

Choose your mode:
- **Text Mode** - Type your answers (works everywhere)
- **Speech Mode** - Speak in Tamil or English (requires microphone)

---

## 💡 Usage Examples

### Text Mode - Finding a Scheme

```
🔍 TN Welfare Schemes Eligibility Assistant
============================================================

Choose interaction mode:
  1) 📝 Text-based
  2) 🎤 Speech-based
  3) ❌ Exit

Enter your choice: 1

📝 Text Mode - Scheme Eligibility Assistant
────────────────────────────────────────────

❓ What is your age?
Your answer: 28

✓ Response recorded

❓ What is your annual household income?
Your answer: 300000

✓ Response recorded

[More questions...]

============================================================
🔍 Finding matching schemes...
============================================================

✅ Found 3 matching scheme(s):

1. Scheme Name
   Category: Social
   Type: Monthly Assistance
   Benefit: ₹5000
   Match Score: 95%

   Why this matches you:
   ✓ Age 25-45 (your age: 28)
   ✓ Income limit ₹500000 (your income: ₹300000)
   ✓ Gender: All

   Application Mode: Online
   Portal: https://...
   Documents Needed: Aadhaar, Income Certificate

────────────────────────────────────────────

2. Another Scheme
   ...
```

### Speech Mode - Tamil Input

```
Enter your choice: 2

🎤 Speech Mode
────────────────────────────────────────────

❓ What is your age?
🎤 Listening...

🔤 You said: நான் முப்பது வயது
📢 Detected Tamil, translating...
✓ Response recorded

[System processes in English, responds in Tamil]
```

---

## 🎯 Key Features

| Feature | Mode | Support |
|---------|------|---------|
| Text Input | Both | ✅ |
| Speech Input | Speech | ✅ |
| Tamil Queries | Both | ✅ |
| English Queries | Both | ✅ |
| Automatic Translation | Both | ✅ |
| Offline Processing | Text | ✅ |
| Speech Recognition | Speech | ✅ (local) |
| Scheme Matching | Both | ✅ |

---

## 🔧 Troubleshooting

### Q: "ModuleNotFoundError: No module named 'whisper'"

```bash
pip install openai-whisper
```

### Q: "Microphone not detected in speech mode"

- Check microphone is connected
- Try another USB port
- Use text mode instead (works everywhere)

### Q: "GROQ_API_KEY not found"

Make sure `.env` has:
```
GROQ_API_KEY=your_actual_key
```

### Q: "Audio recording failed"

Try:
```bash
# Check audio input
python -c "import pyaudio; p = pyaudio.PyAudio(); print(p.get_device_count())"
```

### Q: "Excel file not found"

Ensure `tn_welfare_schemes.xlsx` is in project root.

---

## 📊 What's Being Matched?

The chatbot matches schemes based on:

- 📅 **Age** - Min/max age eligibility
- 💰 **Income** - Annual income limit
- 👤 **Gender** - Male/Female/All
- 📚 **Caste** - General/OBC/SC/ST
- 🙏 **Religion** - Hindu/Muslim/Christian/etc
- 💼 **Occupation** - Professional category
- 🎓 **Education** - Education level required
- 👰 **Marital Status** - Single/Married/etc
- ♿ **Disability** - If scheme requires disability status
- 🏠 **Residence** - Duration in Tamil Nadu

---

## 🗣️ Language Support

### Supported Languages
- ✅ Tamil (தமிழ்)
- ✅ English

### How It Works
1. User speaks/types in Tamil or English
2. System auto-detects language
3. Translates to English for processing
4. Translates response back to Tamil if needed

### Example

```
User: என் வயது 35 (Tamil: "My age is 35")
↓
System detects: Tamil
↓
Translates: "My age is 35"
↓
Processes and matches schemes
↓
Response generated in English
↓
Translates to Tamil if input was Tamil
↓
User receives response in Tamil
```

---

## ⚡ Performance Tips

### Make Text Mode Faster
- Use concise answers (e.g., "28" instead of "I am 28 years old")
- Answer relevant questions only
- Close other applications

### Make Speech Mode Faster
1. **Reduce Whisper Model Size**
   ```
   WHISPER_MODEL_SIZE=tiny  # Faster, less accurate
   ```

2. **Disable TTS (Text-to-Speech)**
   ```
   ENABLE_TTS=false
   ```

3. **Speak clearly** with minimal background noise

### Expected Times
- Text question: 1-2 seconds
- Speech question: 5-10 seconds (Whisper processing)
- Scheme lookup: 2-3 seconds
- Total per question: 6-15 seconds

---

## 🔐 Privacy & Security

✅ **What stays local:**
- All audio/speech processing (Whisper)
- All translation (indic-nlp)
- All scheme matching logic
- Your user responses

❌ **What goes to cloud:**
- GroqAPI calls for LLM assistance
- Only when you ask follow-up questions

> **Note:** Read GroqAPI privacy policy: https://groq.com/

---

## 📚 More Help

- **Full docs:** See `CHATBOT_README.md`
- **Troubleshooting:** See CHATBOT_README.md → Troubleshooting
- **API Setup:** https://console.groq.com/

---

## 🎓 Understanding Output

### Scheme Match Score

```
Match Score: 85%
```

Means 85% of your criteria match this scheme's requirements.

### Matching Criteria Display

```
✓ Age 25-45 (your age: 28)       ← You match
✗ Income ₹300000 (yours: ₹500000) ← You don't match
✓ Caste: OBC                      ← You match
```

Green checkmark (✓) = Criterion met
Red X (✗) = Criterion not met

---

## 🚀 Next Steps

1. Run `python setup_chatbot.py` to complete setup
2. Run `python run_chatbot.py` to start chatbot
3. Choose Text or Speech mode
4. Answer eligibility questions
5. View matching schemes with details
6. Visit official portals to apply

---

**Ready? Let's get started!** 🎉

```bash
python setup_chatbot.py
```

Then:

```bash
python run_chatbot.py
```
