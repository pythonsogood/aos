import speech_recognition
from speech_recognition.recognizers.whisper_local.whisper import recognize as recognize_whisper

# Monkey-patching due to try-except block in library
speech_recognition.Recognizer.recognize_whisper = recognize_whisper  # pyright: ignore[reportAttributeAccessIssue]

recognizer = speech_recognition.Recognizer()

with speech_recognition.Microphone() as source:
	audio = recognizer.listen(source)

try:
	text: str = recognizer.recognize_whisper(audio, model="tiny")  # pyright: ignore[reportAttributeAccessIssue]
except Exception as e:
	print(f"Failed to recognize {e.args}")
else:
	if len(text) > 0:
		print(f"You said: {text}")
	else:
		print("No words detected")
