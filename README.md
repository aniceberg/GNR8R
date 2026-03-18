# cummins_GNR8R

Home Assistant custom integration and ESPHome companion configuration for Cummins residential standby generators using a dual-backend design:

- Primary/default: ESPHome discrete I/O through opto-isolated inputs
- Secondary/optional: PCC1302 Modbus RTU over RS-485

This project is built around real field findings from a QuietConnect installation with a PCC1302 controller and HMI211 display. Discrete I/O is physically accessible now, and the PCC1302 operator instructions provide the primary hardware reference for the controller's TB15 Modbus/RS-485 connection and schematic guidance.

## Why Two Backends?

The inspected installation exposes discrete integration points now:

- `TB6` output
- `TB7` output 1 (N.O.)
- `TB10` SW B+ (switched 12 V, 10 A max source)
- `TB3` inputs return

The PCC1302 controller also supports Modbus RTU over `TB15`. On the PCC1302 board family used here, the lower-left 5-position low-voltage terminal is treated as the likely TB15 Modbus/service connector based on the operator manual and matching board photos. Because installation access and controller configuration can still vary, this repo is intentionally designed so users can:

1. Start immediately with discrete monitoring through ESPHome.
2. Upgrade later to direct Modbus telemetry once TB15 is safely identified, wired, and validated.

## Safety

- This project is read-only. It does not issue start/stop or other control commands.
- Do not connect generator outputs directly to ESP32 GPIO.
- Use an opto-isolated input module for all generator and ATS signals.
- Do not work on line-voltage ATS wiring unless you are qualified to do so.
- Power the ESP32 from `TB10` through an inline fuse and buck converter only.

## Supported Architecture

Visible branding:

- Integration name: `cummins_GNR8R`

Internal Home Assistant identifiers:

- Domain: `cummins_gnr8r`
- Package: `custom_components/cummins_gnr8r/`

## Features

- UI config flow with backend selection
- Default discrete backend using mapped ESPHome entities
- Optional PCC1302 Modbus backend using `pymodbus`
- Derived operational state synthesis for outage/transfer scenarios
- Core binary sensors for running/fault/utility/ATS state
- System-state text sensor
- Modbus telemetry when RS-485 is available
- Optional ATS and utility-state probing on Modbus endpoints that expose DMC/ATS registers
- Diagnostics with per-backend details and redacted serial information
- HACS-compatible repo layout
- ESPHome 4-input and 6-input starter YAML files

## Authoritative Sources

- PCC1302 operator instructions PDF for TB15 connector and Modbus schematic guidance
- Cummins PowerCommand Modbus register map PDF for protocol/register definitions

## Backend A: ESPHome Discrete I/O

This is the recommended starting point because it relies only on exposed field wiring.

### Expected Hardware

- ESP32 dev board
- 4-channel or 6-channel opto-isolated input board
- 12 V to 5 V buck converter
- 1 A inline fuse for the ESP32 supply branch
- Enclosure, terminals, and low-voltage wiring as appropriate

### Power Wiring

- `TB10 SW B+` -> inline 1 A fuse -> buck converter input +
- `TB3 Inputs Return` -> buck converter input - / ESP32 GND reference
- Buck converter 5 V output -> ESP32 5 V/VIN

### Signal Wiring

Use opto-isolated inputs for:

- `TB6`
- `TB7`
- ATS utility-available contact
- ATS on-generator contact
- ATS alarm contact (optional)
- spare/discrete inputs

Do not assume `TB6`/`TB7` are dry contacts. Treat them as unknown field signals until verified with a meter and wire them only through suitable isolation hardware.

### Included ESPHome Templates

- [`esphome/cummins_generator_4input.yaml`](/Users/isaac/Documents/GitHub/GNR8R/esphome/cummins_generator_4input.yaml)
- [`esphome/cummins_generator_6input.yaml`](/Users/isaac/Documents/GitHub/GNR8R/esphome/cummins_generator_6input.yaml)

They include:

- parameterized GPIO substitutions
- debounce filters
- inversion options
- descriptive names

Suggested signals:

- `generator_output_1`
- `generator_output_2`
- `ats_utility_available`
- `ats_on_generator`
- `ats_alarm`
- `spare_input`

## Backend B: PCC1302 Modbus

This backend is supported, but optional.

The PCC1302 operator manual is the primary source for this section. For this board family, the lower-left 5-position low-voltage terminal is treated as the likely `TB15` Modbus/service connector, but the installed unit still needs on-site verification for pin orientation and access.

Known PCC1302 RS-485 reference:

- `TB15-3` = RS485 A (+)
- `TB15-4` = RS485 B (-)
- `TB15-1` = Shield/Return

Field caveats:

- The board appears to expose `TB15` directly on the controller PCB
- Exact terminal numbering orientation must be confirmed on the installed unit
- Physical access may still be limited by enclosure layout or harness routing
- Modbus may need to be enabled in the controller
- service-mode, wake-up, or controller settings may still be required

### First-Pass Wiring Guidance

- Start only with the documented RS-485 pair and shield/return
- Leave any extra wake/system pin disconnected unless the manual or field testing proves it is required
- Meter-check the assumed TB15 pins before connecting a USB-RS485 adapter
- Treat no-response scenarios as possibly configuration-related, not just wiring-related

### Modbus Scope

- Serial RTU only
- Read-only only
- Typical settings: address `1`, baud `9600` or `19200`, parity `N`
- The backend always reads core genset telemetry and then probes for optional ATS/utility register support
- If ATS/utility registers are present on the selected Modbus endpoint, the backend synthesizes utility/transfer state without relying on ESPHome

### Implemented PCC1302 Telemetry

| Value | Register | Conversion |
| --- | --- | --- |
| NFPA bitmap | 40716 | raw |
| Extended bitmap | 40717 | raw |
| Battery voltage | 40735 | 0.1 V |
| Oil pressure | 40736 | 0.1 kPa |
| Coolant temperature | 40738 | 0.1 K -> C/F |
| Engine speed | 40742 | RPM |
| Total runs | 40743 | integer |
| Runtime | 40744/40745 | 32-bit |
| Frequency | 40750 | 0.1 Hz |

### Optional Modbus ATS and Utility Detection

When the selected Modbus endpoint exposes ATS and utility data, the backend also reads:

- ATS 1 mode/state/fault data from the `40257-40265` register block
- Utility LN average voltage from `40062`
- Utility frequency from `40084`

From those optional registers, the backend can derive:

- `utility_available`
- `ats_on_generator`
- `running_on_generator`
- `utility_outage_active`
- `transfer_in_progress`
- `generator_system_state`

If those registers are not implemented on the selected Modbus slave, the backend keeps core genset telemetry and alarm functionality and marks the ATS-specific entities unavailable rather than mixing in another backend.

## Home Assistant Entities

Core binary sensors provided by both backends:

- `generator_running`
- `generator_fault`
- `utility_available`
- `ats_on_generator`
- `running_on_generator`
- `utility_outage_active`
- `transfer_in_progress`

Core text state output:

- `generator_system_state`

Modbus-only sensors:

- battery voltage
- oil pressure
- coolant temperature (C)
- coolant temperature (F)
- engine speed
- total runs
- runtime
- frequency
- raw NFPA bitmap
- raw extended bitmap
- utility LN average voltage
- utility frequency
- ATS mode
- ATS state
- ATS fault code
- ATS fault type
- raw ATS NFPA bitmap
- raw ATS extended bitmap
- source 1/source 2 availability and connected-state diagnostics

## State Synthesis

The integration synthesizes generator state from the logical signals:

- utility off + ATS off -> `Outage detected, waiting for transfer`
- utility off + ATS on -> `Running on generator`
- utility on + ATS on -> `Utility restored, awaiting retransfer`
- utility on + ATS off -> `Normal utility power`
- fault active -> append `Fault active`
- missing/inconsistent signals -> `Transition / unknown`

## Installation

### HACS

1. In HACS, add `https://github.com/aniceberg/GNR8R` as a custom repository.
2. Choose category `Integration`.
3. Install `cummins_GNR8R`.
4. Restart Home Assistant.

### Manual

1. Copy [`custom_components/cummins_gnr8r`](/Users/isaac/Documents/GitHub/GNR8R/custom_components/cummins_gnr8r) into your Home Assistant `custom_components/` directory.
2. Restart Home Assistant.
3. Add `cummins_GNR8R` from `Settings -> Devices & services`.

## Setup

### Discrete backend

1. Flash one of the included ESPHome YAMLs to your ESP32 hardware.
2. Confirm the ESPHome binary sensors appear in Home Assistant.
3. Add the `cummins_GNR8R` integration.
4. Choose `ESPHome discrete`.
5. Map the HA entity IDs for:
   - utility available
   - ATS on generator
   - generator running
   - generator fault
6. Set inversion flags if the signal logic is reversed.

### Modbus backend

1. Confirm the lower-left 5-position terminal on the PCC1302 board is the installed unit's TB15 and verify pin orientation on the live controller.
2. Connect a USB-RS485 adapter to the generator controller.
3. Add or reconfigure `cummins_GNR8R`.
4. Choose `PCC1302 Modbus`.
5. Enter serial settings and validate connectivity.

## Upgrade Path: Discrete -> Modbus

The integration is designed so a single config entry can switch backends later.

Recommended path:

1. Start with `ESPHome discrete`.
2. Verify transfer/outage logic in HA.
3. Verify the installed controller's TB15 RS-485 terminal orientation and enablement.
4. Reconfigure the same integration entry to `PCC1302 Modbus`.
5. Keep the ESPHome hardware if you still want local fallback or bench diagnostics.

## Wiring Diagram (Conceptual)

```text
TB10 SW B+ ---- 1A fuse ---- buck converter ---- 5V ---- ESP32
TB3 Return ----------------- buck converter ---- GND --- ESP32 GND

TB6/TB7/ATS contacts ---- opto-isolated input board ---- ESP32 GPIOs
```

## Troubleshooting

### No signals in discrete mode

- Verify the opto input board has a common reference to `TB3`
- Verify the ESPHome entities are updating in HA before configuring the integration
- Confirm the mapped entity IDs are the correct ones

### Signals appear inverted

- Enable the per-signal inversion toggle in the integration
- Or invert the corresponding ESPHome GPIO input if you prefer to normalize at the source

### ESP32 keeps rebooting

- Check the buck converter output under load
- Confirm the 1 A fused supply branch is stable
- Separate noisy field wiring from the ESP32 power wiring

### Modbus does not respond

- Confirm the lower-left 5-position connector on the installed controller is TB15 and that pin orientation is correct
- Confirm only the documented RS-485 pair and shield are connected for first-pass testing
- Check controller settings for Modbus enablement
- Consider whether the port is in a service/protocol mode instead of normal Modbus operation
- Try address `1`, `9600`, `N`, `8`, `1` first, then `19200`
- Confirm A/B polarity

### Modbus connects but ATS/utility state stays unavailable

- The selected Modbus slave may expose only genset telemetry and not the ATS/DMC register family
- Verify whether the endpoint implements ATS registers around `40257-40265`
- Verify whether utility data registers such as `40062` and `40084` are readable on that endpoint
- Review diagnostics group health to see which optional register groups are supported

## Assumptions That Still Need Field Verification

- Exact electrical behavior of `TB6` and `TB7`
- Which ATS contacts are practically available in the installation
- Exact terminal numbering orientation and enablement state of `TB15` on the live unit
- Whether the installed Modbus endpoint exposes the optional ATS/utility registers used for standalone parity
- Whether PCC1302 runtime register units need additional field confirmation

## Development

Suggested local checks:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
pytest
```
