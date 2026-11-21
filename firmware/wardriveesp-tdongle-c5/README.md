# WardriveESP for the LilyGO T-Dongle C5

RocketGod's WardriveESP 1.7.11, with support for the T-Dongle C5's own hardware. It links to Wardrive Go and scans
like any WardriveESP board.

- **Screen:** the 0.96" display shows a dashboard. The header shows where the data goes (phone, USB, SD card or not
  linked). The middle shows what's around now and what this run has sent. The bottom line shows what the radio is
  doing and on which channel. App alerts take over the screen in the app's colors.
- **LED:** stays dark, and lights only while an alert plays, in the app's pattern and color. Brightness is set in
  the app, or with a double tap.
- **BOOT button:** tap to switch between the dashboard and the details page, or to dismiss an alert. Double tap to
  step the LED brightness. Hold for 1 s to toggle stealth (screen and LED off).

No GPS on this board: the phone stamps locations. Source, pins and build steps:
https://github.com/Aediliss/wardriveesp-tdongle-c5
