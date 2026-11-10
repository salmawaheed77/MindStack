# MindStack GUI (PySide6)

واجهة المستخدم لمشروع **Voice-Enhanced Linux**.
تعرض حالة النظام (Listening / Processing / Speaking)، الأمر اللي اتقال، النتيجة، وسجل الأوامر.

## التشغيل

```bash
pip install -r requirements.txt
python main.py
```

على Ubuntu ممكن تحتاجي مرة واحدة:

```bash
sudo apt install python3-pip libxcb-cursor0
```

الـ GUI بيشتغل **من غير ميكروفون** دلوقتي: بيستخدم `MockBackend` اللي بيحاكي الـ pipeline كله.
اكتبي أي أمر في خانة "Type a command" أو دوسي Start listening.

## الشاشات

| الشاشة | الملف | اختصار |
|---|---|---|
| Home (الحالة + الأمر + النتيجة + CPU/RAM/Disk) | `app/pages/home_page.py` | Ctrl+1 |
| Command log (بحث، فلترة، ترتيب، Export CSV) | `app/pages/log_page.py` | Ctrl+2 |
| Commands (الأوامر المدعومة + جرّب المثال) | `app/pages/commands_page.py` | Ctrl+3 |
| Settings (mic، لغة، صوت الرد، أمان، ثيم) | `app/pages/settings_page.py` | Ctrl+4 |
| Confirm dialog (قبل الأوامر الخطرة) | `app/dialogs/confirm_dialog.py` | |
| Mic test dialog | `app/dialogs/mic_test_dialog.py` | |
| About dialog | `app/dialogs/about_dialog.py` | |
| System tray | `app/main_window.py` | |

`Ctrl+L` = بدء/إيقاف الاستماع من أي شاشة.

## هيكل المشروع

```
main.py                  نقطة التشغيل (هنا بتبدّلي الـ backend)
app/
  backend.py             BaseBackend (العقد) + MockBackend
  controller.py          الوسيط الوحيد بين الـ GUI والـ backend
  models.py              سجل الأوامر + الإعدادات
  state.py               حالات النظام وألوانها
  theme.py               Dark / Light (QSS)
  commands_data.py       قايمة الأوامر المدعومة
  main_window.py         النافذة الرئيسية
  pages/  dialogs/  widgets/
```

## الربط مع باقي الفريق (أهم جزء)

الـ GUI **مبيكلمش Vosk ولا subprocess ولا pyttsx3 مباشرة**. بيكلم `BaseBackend` بس.
اللي على زمايلك: يعملوا class يرث من `BaseBackend` في `app/backend.py` ويطبّق:

| Methods (الـ GUI بينادي عليها) | Signals (الـ backend يطلّعها) |
|---|---|
| `start_listening(language, mic_device)` | `recognized(str)` بعد ما الـ STT يطلّع جملة |
| `stop_listening()` | `needs_confirmation(str)` لو الأمر خطر |
| `process(text)` | `executed(str, bool)` نص النتيجة + نجح/فشل |
| `confirm(accepted)` | `speaking_done()` بعد ما الـ TTS يخلّص |
| `speak(text, rate)` | `error(str)` لو الميكروفون مش شغال مثلاً |
| `start_mic_test()` / `stop_mic_test()` | `mic_level(float 0..1)` |
| `shutdown()` | |

بعدها في `main.py` غيّري سطر واحد:

```python
def create_backend():
    return RealBackend()   # بدل MockBackend()
```

ملحوظة مهمة: الـ STT والـ TTS والأوامر الطويلة لازم تشتغل في **Thread** (`QThread` أو `threading`)
وتبعت النتيجة بالـ signals، وإلا الواجهة هتهنّج.

## ملاحظات

- سجل الأوامر بيتحفظ تلقائياً في مجلد بيانات التطبيق، والإعدادات في `QSettings`.
- لو شغّلتيه على سيرفر من غير صوت (CI) ضيفي `MINDSTACK_SKIP_AUDIO=1` عشان تتجنبي فحص أجهزة الصوت.
- الواجهة والأوامر والنتائج كلها بالإنجليزي. لغة التعرف على الصوت الافتراضية English، وتقدري تغيّريها من Settings.
