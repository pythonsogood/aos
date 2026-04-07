import keyboard

keys_record: list[str] = []
recording = True

def hook_callback(event: keyboard.KeyboardEvent) -> None:
	global recording

	keys_record.append(f"[{event.time:.03f}] {event.name}\n")

	if event.name == "esc":
		keyboard.unhook_all()

		with open("input.log", "w", encoding="utf-8") as f:
			f.writelines(keys_record)

		recording = False

keyboard.hook(hook_callback, False)

while recording:
	pass
