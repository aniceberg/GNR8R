# Cummins Generator

Home Assistant custom integration for Cummins PowerCommand / PCC1301-family generators over local Modbus RTU on RS-485.

This integration is designed for HACS custom-repository installation and UI-based configuration. It is intentionally read-only in this first release.

## Features

- Local-only polling over USB-to-RS485 serial adapters
- UI config flow and options/reconfigure flow
- Coordinator-based polling with graceful availability handling
- Typed, data-driven register map for PCC1301 / PowerCommand 1.x
- Raw NFPA status bitmaps plus decoded binary sensors
- Diagnostics with redacted connection details
- HACS-compatible repository layout and CI workflow

## Safety Warning

This version is read-only. It does not write Modbus registers, issue control commands, or implement Save Trims. It is intended for monitoring only.

## Supported Scope

Primary target:

- Cummins residential standby generator
- PowerCommand HMI211 display
- PCC1301 / PowerCommand 1.x register family
- Local Modbus RTU over RS-485

Because Cummins controller families vary, some installations may require register-map adjustments before every entity is valid.

## Supported Entities

| Entity | Type | Register / Bit | Notes |
| --- | --- | --- | --- |
| Average line frequency | Sensor | 40044 | Scale 0.1 Hz |
| Battery voltage | Sensor | 40061 | Scale 0.1 V |
| Oil pressure | Sensor | 40062 | kPa |
| Coolant temperature | Sensor | 40064 | Scale 0.1 °C |
| Engine speed | Sensor | 40068 | rpm |
| Total runs | Sensor | 40069 | Integer counter |
| Raw NFPA bitmap 1 | Sensor | 40016 | Diagnostic raw value |
| Raw NFPA bitmap 2 | Sensor | 40017 | Diagnostic raw value |
| Common alarm | Binary sensor | 40016 bit 15 | Problem indicator |
| Genset supplying load | Binary sensor | 40016 bit 14 | Status |
| Genset running | Binary sensor | 40016 bit 13 | Running state |
| Not in auto | Binary sensor | 40016 bit 12 | Problem indicator |
| Low battery voltage alarm | Binary sensor | 40016 bit 10 | Problem indicator |
| Charger AC failure | Binary sensor | 40016 bit 9 | Problem indicator |
| Fail to start | Binary sensor | 40016 bit 8 | Problem indicator |
| High engine temperature | Binary sensor | 40016 bit 5 | Heat problem |
| Low oil pressure | Binary sensor | 40016 bit 3 | Problem indicator |
| Overspeed | Binary sensor | 40016 bit 2 | Problem indicator |
| Low fuel level | Binary sensor | 40016 bit 0 | Problem indicator |
| Check genset | Binary sensor | 40017 bit 15 | Problem indicator |
| Ground fault | Binary sensor | 40017 bit 14 | Safety problem |
| High AC voltage | Binary sensor | 40017 bit 13 | Problem indicator |
| Low AC voltage | Binary sensor | 40017 bit 12 | Problem indicator |
| Under frequency | Binary sensor | 40017 bit 11 | Problem indicator |
| Overload | Binary sensor | 40017 bit 10 | Problem indicator |
| Overcurrent | Binary sensor | 40017 bit 9 | Problem indicator |
| Short circuit | Binary sensor | 40017 bit 8 | Problem indicator |
| Emergency stop | Binary sensor | 40017 bit 0 | Safety problem |

## Installation via HACS

1. Push this repository to GitHub.
2. In Home Assistant, open HACS.
3. Open the three-dot menu, choose `Custom repositories`.
4. Add your GitHub repository URL and choose category `Integration`.
5. Find `Cummins Generator` in HACS and install it.
6. Restart Home Assistant.

## Manual Installation

1. Copy `custom_components/cummins_generator/` into your Home Assistant `custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration from `Settings > Devices & services > Add integration`.

## Setup in Home Assistant

1. Add `Cummins Generator`.
2. Enter the serial path, slave address, baud rate, byte size, parity, stop bits, poll interval, and optional scan throttle.
3. The integration validates connectivity by reading safe monitoring registers.
4. On success, entities are created under one generator device.
5. Use `Configure` on the config entry later to update serial or polling settings.

## Diagnostics

Diagnostics export includes:

- Redacted serial connection details
- Last update success state
- Last exception category and message
- Per-register-group health snapshot

## Troubleshooting

- `cannot_connect`: Verify the USB-RS485 adapter path, wiring polarity, and slave address.
- `timeout`: Confirm the controller is responding at the configured baud/parity/stop-bit settings.
- `modbus_error`: Check wiring, bus termination, and whether the target controller exposes the PCC1301 register family.
- Some entities unavailable: Your controller may not implement one of the grouped register ranges yet. The integration leaves unaffected entities active where possible.

## Known Limitations

- Read-only monitoring only
- One generator per config entry
- No automatic register-family detection in v1
- No ATS entities yet

## Roadmap

- Additional PowerCommand registers
- Optional automatic transfer switch support
- Better model/firmware identification
- Optional derived health summary sensors
- Broader controller-family coverage

## Example Screenshots

Placeholder images live in `docs/screenshots/` and can be replaced before publication.

## Repository Publish Notes

1. Create a GitHub repository and push this tree.
2. Update `manifest.json` URLs to your actual repository and issue tracker.
3. Replace placeholder branding assets.
4. Tag a release that matches the integration version.
5. Add the repository to HACS as a custom integration repository.
