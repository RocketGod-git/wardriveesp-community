# WardriveESP community firmware

Firmware made by the community for ESP32 boards that [WardriveESP](https://rocketgod.dev/WardriveESP/) doesn't support.
Everything merged here shows up on the WardriveESP flasher under **Don't see your board? Try community firmware**,
where anyone can flash it from Chrome or Edge in about a minute. No tools, no command line.

> Community firmware isn't made or tested by the WardriveESP team. Each one belongs to its author.

## Flash one

1. Open [rocketgod.dev/WardriveESP](https://rocketgod.dev/WardriveESP/) in Chrome or Edge on a computer.
2. Under the board picker, open **Don't see your board?** and pick the firmware for your board.
3. Read its card (author, boards, source), press **Flash**, and pick your board's port.

The flasher checks that your board's chip matches the firmware before it erases anything.

## Submit your firmware

You need a GitHub account and one merged image of your firmware. That's it.

### 1. Build one merged image

The flasher writes a single file at address `0x0`, so the bootloader, partition table and app must be in one image.

- **ESP-IDF:** `idf.py merge-bin` (IDF 5.3+), or
  `esptool.py --chip <chip> merge_bin -o firmware.bin @flash_args` from your build folder.
- **Arduino / PlatformIO:** `esptool.py --chip <chip> merge_bin -o firmware.bin 0x<bootloader offset> bootloader.bin 0x8000 partitions.bin 0x10000 firmware.bin`

Bootloader offsets: `0x1000` on the ESP32, `0x2000` on the ESP32-C5, `0x0` on the C3, C6 and S3.

### 2. Add a folder

Fork this repo and add one folder under `firmware/`. Its name is your firmware's id: lowercase letters, digits and
dashes, like `marauder-xyz-board`.

```
firmware/
  marauder-xyz-board/
    manifest.json    copy it from template/manifest.json
    firmware.bin     your merged image, at most 8 MB
    README.md        optional: anything people should know
```

One folder per chip. Firmware for two chips is two folders, like `my-fw-c5` and `my-fw-s3`.

### 3. Fill in manifest.json

```json
{
  "name": "Marauder for the XYZ Board",
  "author": "your-handle",
  "chip": "ESP32-C5",
  "boards": ["XYZ Board v2", "XYZ Board Mini"],
  "version": "1.2.0",
  "description": "Marauder with the XYZ Board's screen and buttons.",
  "notes": "Hold BOOT while plugging in if the flasher can't connect.",
  "source": "https://github.com/your-handle/your-firmware",
  "website": "https://example.com",
  "license": "GPL-3.0"
}
```

| Field | Needed | What it is |
|---|---|---|
| `name` | yes | What people see in the picker. Up to 60 characters. |
| `author` | yes | Your name or handle. |
| `chip` | yes | `ESP32`, `ESP32-C3`, `ESP32-C5`, `ESP32-C6` or `ESP32-S3`. It must match the image. |
| `boards` | yes | The boards it runs on, as people would search for them. |
| `version` | yes | Your firmware's version. Bump it with every new image. |
| `description` | yes | One or two sentences, up to 300 characters. |
| `source` | yes | An `https://` link to the source code. |
| `license` | yes | Its license, like `MIT` or `GPL-3.0`. |
| `notes` | no | Anything to know before flashing, up to 300 characters. |
| `website` | no | An `https://` link to your project page. |

### 4. Open a pull request

A check runs on your pull request within a minute and lists anything to fix: a missing field, an image built for
another chip, a file too big. Once it passes and the firmware is reviewed, it's merged and appears on the flasher
within a few minutes.

**Updating:** replace `firmware.bin`, bump `version`, open another pull request.

### Check it yourself first (optional)

```
python tools/check.py
```

## Rules

- Your own work, or work you're allowed to share, with its source public.
- It runs on the boards listed and doesn't harm them.
- No malware, nothing that hides what it does, nothing built to attack networks or people you don't have permission to test.

## How it's published

On every merge, `tools/check.py --index` checks every folder again and builds `index.json`, which GitHub Pages
publishes at `rocketgod.dev/wardriveesp-community/` beside the flasher. The flasher reads that list, downloads the
image you pick and checks its SHA-256 before writing it.
