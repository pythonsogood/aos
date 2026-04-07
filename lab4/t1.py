import csv

import wmi

c = wmi.WMI()

devices = []

for device in c.Win32_PnPEntity():
	name = device.Name
	device_id = device.DeviceID

	if not name:
		continue

	device_type = "Unknown"
	interface = "Unknown"

	name_lower = name.lower()

	if any(keyword in name_lower for keyword in ["keyboard", "mouse", "scanner", "camera", "microphone"]):
		device_type = "Input Device"
	elif any(keyword in name_lower for keyword in ["monitor", "display", "speaker", "printer", "headphone"]):
		device_type = "Output Device"
	elif any(keyword in name_lower for keyword in ["usb", "storage", "disk", "drive"]):
		device_type = "Storage/Hybrid Device"

	if "USB" in device_id:
		interface = "USB"
	elif "BTH" in device_id:
		interface = "Bluetooth"
	elif "PCI" in device_id:
		interface = "PCI"
	elif "HID" in device_id:
		interface = "HID"
	else:
		interface = "Other"

	if device_type == "Unknown":
		continue

	devices.append([name, device_type, interface])

with open("device_list.csv", "w", newline="", encoding="utf-8") as file:
	writer = csv.writer(file)
	writer.writerow(["Device Name", "Type", "Connection Interface"])
	writer.writerows(devices)
