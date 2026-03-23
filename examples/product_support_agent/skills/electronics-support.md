# Skill: Consumer Electronics Support

**Description:** Diagnose and resolve common consumer electronics problems including phones, tablets, laptops, monitors, headphones, and smart speakers.

## When to Use

Activate this skill when the user describes a problem with a consumer electronic device. Match their description to the closest symptom below and walk them through the corresponding fix. Always start by confirming the device type and symptom before jumping into steps.

## How to Use

1. Identify the symptom category (Power, Connectivity, Display, Battery, Audio).
2. Ask one clarifying question if the symptom could match multiple entries.
3. Present the likely cause, then guide the user through the numbered fix steps one at a time.
4. If the fix does not resolve the issue, advise escalation as noted.

---

## 1. Power Issues

### 1.1 Device Won't Turn On

**Likely cause:** The battery is fully depleted, or the power button is stuck or unresponsive due to a firmware hang.

**Fix:**
1. Connect the device to its original charger and wait at least 15 minutes before attempting to power on.
2. Perform a hard reset: hold the power button for 15-20 seconds, then release and press it again normally.
3. Try a different charging cable and power adapter to rule out faulty accessories.
4. If the device has a removable battery, remove it for 30 seconds, reinsert it, and try powering on.

**Escalate:** If the device still does not power on after trying all steps, the issue is likely a failed power IC or logic board fault. Recommend professional repair or manufacturer warranty service.

### 1.2 Random Shutdowns

**Likely cause:** Overheating, a degraded battery that cannot sustain voltage under load, or a software crash loop.

**Fix:**
1. Check that all ventilation openings are clear of dust and debris; clean them with compressed air.
2. Boot into safe mode (method varies by device) to determine whether a third-party app is causing crashes.
3. Update the operating system and all drivers or firmware to the latest version.
4. Monitor the device temperature using a built-in diagnostic or third-party tool; if it exceeds 90C under normal use, the thermal paste or cooling system may need service.

**Escalate:** If shutdowns continue in safe mode with updated software and adequate cooling, suspect a hardware fault (battery or motherboard). Advise professional diagnosis.

### 1.3 Device Won't Charge

**Likely cause:** A damaged charging cable, debris in the charging port, or a failing charging circuit.

**Fix:**
1. Inspect the charging port for lint, dust, or bent pins. Gently clean with a wooden toothpick or dry soft-bristle brush.
2. Test with a known-good cable and adapter.
3. Restart the device and attempt charging again.
4. If wireless charging is available, try that to isolate whether the port itself is the issue.

**Escalate:** If the device does not charge via any method, the charging IC or battery connector may be damaged. Recommend professional repair.

---

## 2. Connectivity

### 2.1 WiFi Won't Connect

**Likely cause:** Corrupted network configuration on the device, or the router is not assigning an IP address correctly.

**Fix:**
1. Toggle WiFi off, wait 10 seconds, then toggle it back on.
2. Forget the network on the device, then reconnect by entering the password fresh.
3. Restart the router by unplugging it for 30 seconds and plugging it back in.
4. Reset network settings on the device (this clears all saved networks and VPN configurations).
5. Verify that MAC address filtering or device limits on the router are not blocking the device.

**Escalate:** If the device cannot connect to any WiFi network (not just one), the WiFi antenna or radio chip may be faulty. Advise professional diagnosis.

### 2.2 Bluetooth Pairing Failures

**Likely cause:** The accessory is not in pairing mode, or stale pairing records on either device are causing a mismatch.

**Fix:**
1. Confirm the accessory is in discoverable/pairing mode (check the accessory manual for the correct button sequence).
2. On the main device, remove any existing entry for the accessory, then scan again.
3. Restart Bluetooth on both devices.
4. If pairing still fails, reset the accessory to factory defaults and retry.

**Escalate:** If the device cannot pair with any Bluetooth accessory, the Bluetooth module may be defective. Recommend service.

### 2.3 Weak WiFi or Bluetooth Signal

**Likely cause:** Physical distance or obstacles between the device and the router or accessory, or interference from other 2.4 GHz devices.

**Fix:**
1. Move closer to the router or accessory to confirm signal improves.
2. Switch the router to the 5 GHz band if the device supports it, to reduce interference.
3. Relocate the router away from microwaves, baby monitors, or thick walls.
4. Update router firmware and device network drivers.

**Escalate:** If signal is weak even at close range, the device antenna may be damaged or disconnected. Advise professional inspection.

---

## 3. Display

### 3.1 No Picture (Screen Is Black)

**Likely cause:** The display cable is loose, the backlight has failed, or the GPU is not outputting a signal.

**Fix:**
1. Press any key or move the mouse to rule out sleep mode or screensaver.
2. Connect an external monitor (or cast the screen) to determine if the GPU is outputting video.
3. Perform a hard reset (hold power 15-20 seconds).
4. For laptops, try closing and reopening the lid, or pressing the display-toggle key (e.g., Fn+F7).

**Escalate:** If an external display works but the built-in screen does not, the display panel, backlight, or ribbon cable likely needs replacement.

### 3.2 Flickering Screen

**Likely cause:** Incompatible refresh rate setting, a loose display cable, or a failing GPU.

**Fix:**
1. Lower the screen refresh rate in display settings (try 60 Hz).
2. Update or roll back the graphics driver.
3. Boot into safe mode; if flickering stops, a third-party application or driver is the cause.
4. For external monitors, try a different video cable (HDMI, DisplayPort, USB-C).

**Escalate:** If flickering persists in safe mode with updated drivers, the display panel or GPU may be failing. Recommend professional repair.

### 3.3 Dead Pixels

**Likely cause:** Manufacturing defect or physical pressure damage to individual sub-pixels on the LCD or OLED panel.

**Fix:**
1. Confirm it is a dead pixel (always black) versus a stuck pixel (always one color) by displaying a full-white screen.
2. For stuck pixels, try a pixel-exerciser tool that rapidly cycles colors for 20-30 minutes.
3. Gently apply pressure with a soft cloth over the stuck pixel while the exerciser runs (do not press hard).

**Escalate:** Dead pixels (always black) cannot be fixed with software. If the count exceeds the manufacturer's acceptable threshold (typically 3-5), request a warranty replacement.

### 3.4 Screen Too Dim

**Likely cause:** Auto-brightness is adjusting incorrectly, or the backlight is degrading.

**Fix:**
1. Disable auto-brightness and manually set brightness to maximum.
2. Check power-saving or battery-saver modes, which often reduce brightness. Disable them.
3. Restart the device to clear any transient sensor glitch.
4. Clean the ambient light sensor (usually near the front camera) with a soft cloth.

**Escalate:** If maximum brightness is noticeably dimmer than when the device was new, the backlight or OLED panel is degrading. Advise professional assessment.

---

## 4. Battery

### 4.1 Fast Battery Drain

**Likely cause:** A rogue background process consuming CPU, or the battery has degraded below 80% of its original capacity.

**Fix:**
1. Check the battery health or cycle count in device settings or a diagnostic tool.
2. Review battery usage stats to identify apps consuming the most power; close or uninstall them.
3. Disable unnecessary background services: location services, background app refresh, push email.
4. Reduce screen brightness and screen-on timeout.
5. If battery health is below 80%, plan for a battery replacement.

**Escalate:** If drain is extreme (0-100% in under 2 hours with light use) and battery health reads as normal, there may be a short circuit on the board. Advise professional diagnosis immediately.

### 4.2 Battery Not Charging

**Likely cause:** See also section 1.3 (Device Won't Charge). If the device powers on but the battery percentage does not increase, the battery itself may be failing.

**Fix:**
1. Follow all steps in section 1.3 first.
2. Check battery health; if it reports "Service" or capacity is very low, the battery needs replacement.
3. Try charging while the device is powered off to reduce load.
4. Calibrate the battery by draining it completely, then charging to 100% uninterrupted.

**Escalate:** If the battery is not recognized by the device or health cannot be read, the battery or its connector may be damaged. Recommend professional replacement.

### 4.3 Battery Swelling

**Likely cause:** Chemical decomposition inside the lithium-ion cell, often due to age, heat exposure, or a faulty charging circuit. This is a safety hazard.

**Fix:**
1. Stop using the device immediately. Do not attempt to charge it.
2. Do not puncture, crush, or attempt to remove a swollen battery yourself unless you have proper training.
3. Place the device in a cool, dry area away from flammable materials.
4. Contact the manufacturer or a certified repair center for safe battery removal and replacement.

**Escalate:** Always escalate. A swollen battery is a fire and chemical burn risk. The user should not attempt self-repair. Provide the manufacturer's support contact if available.

---

## 5. Audio

### 5.1 No Sound

**Likely cause:** Audio is routed to an unintended output (e.g., Bluetooth headset still connected), or the speaker driver has crashed.

**Fix:**
1. Check the volume level and confirm the device is not muted.
2. Disconnect all Bluetooth audio devices and remove any plugged-in headphones.
3. Verify the correct output device is selected in sound settings.
4. Restart the device to reset the audio subsystem.
5. Test with a different app or media file to rule out a file-specific issue.

**Escalate:** If there is no sound from the built-in speaker across all apps after a restart, the speaker or audio codec chip may be damaged. Recommend professional repair.

### 5.2 Audio Distortion or Crackling

**Likely cause:** A damaged speaker, audio driver bug, or electromagnetic interference from nearby components.

**Fix:**
1. Lower the volume to 70% and check if distortion disappears (speaker may be blown at high volume).
2. Update or reinstall the audio driver.
3. Test with headphones; if headphone audio is clean, the built-in speaker is likely damaged.
4. Disable audio enhancements or equalizer effects in sound settings.

**Escalate:** If distortion occurs at all volume levels and persists through headphones as well, the audio codec or DAC may be faulty. Advise professional diagnosis.

### 5.3 Microphone Not Working

**Likely cause:** App permissions are blocking microphone access, the mic port is obstructed, or the microphone hardware has failed.

**Fix:**
1. Check that the app has microphone permission in the device privacy settings.
2. Test the microphone with a different app (e.g., a voice recorder) to isolate the problem.
3. Inspect the microphone opening for debris and clean gently with a dry brush.
4. Restart the device and test again.
5. For external microphones, try a different port or adapter.

**Escalate:** If the microphone produces no input in any app after cleaning and restarting, the microphone element or its connection to the board may be broken. Recommend professional repair.
