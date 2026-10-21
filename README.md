# Eldes Alarm - updated working fork

> Updated and revised by **Danyct80**.

This repository is an updated working fork of the original **Eldes Alarm** custom integration for Home Assistant.

The original project is no longer actively maintained. This fork is shared to help other Eldes users who still need a working Home Assistant integration.

## What has been fixed

This revised version includes:

- fixes for recent Home Assistant compatibility issues;
- fixes for cloud authentication / token refresh problems;
- PIN code support in Eldes cloud API calls;
- alarm status reading;
- working **arm** and **disarm** support from Home Assistant;
- support for alarm control panel, sensors, binary sensors and outputs/switches.

Tested by **Danyct80** with:

- Home Assistant;
- Eldes ESIM384;
- Eldes Cloud account access;
- alarm status reading;
- arm away / disarm commands.

## Important notes

This is an unofficial community fork.

Use it at your own risk. Alarm systems are security-critical devices: after installation, test every partition, zone, output and notification before relying on it.

The Home Assistant integration depends on Eldes Cloud APIs. If Eldes changes its cloud API, login, token handling or command endpoints, this integration may need further updates.

## Installation with HACS custom repository

1. Open Home Assistant.
2. Go to **HACS**.
3. Open the three-dot menu in the top right.
4. Select **Custom repositories**.
5. Add this repository URL:

```text
https://github.com/Danyct80/eldes
```

6. Select category:

```text
Integration
```

7. Click **Add**.
8. Install **Eldes Alarm** from HACS.
9. Restart Home Assistant.
10. Go to **Settings → Devices & services → Add integration**.
11. Search for **Eldes Alarm** and configure it with your Eldes Cloud account credentials and PIN code.

## Manual installation

Copy the integration folder to your Home Assistant `custom_components` directory:

```text
custom_components/eldes_alarm
```

The final path must be:

```text
/config/custom_components/eldes_alarm
```

Then restart Home Assistant and add the integration from **Settings → Devices & services**.

## Supported entities

Depending on your Eldes configuration, the integration can expose:

- alarm control panels / partitions;
- binary sensors;
- sensors;
- outputs as switches.

## Alarm control

This fork adds working control commands for the alarm panel:

- arm away;
- disarm;
- status reading.

In this revised version, Home Assistant exposes the main full-arm command and disarm command. The unreliable half-arm / stay mode button has been intentionally hidden from the default Home Assistant alarm dialog in this setup.

## Repository structure

```text
custom_components/eldes_alarm/
```

This is the Home Assistant custom integration folder.

## Credits

Original project by **augustas2**.

Updated and revised by **Danyct80** to keep the integration usable with newer Home Assistant versions and to add working alarm arm/disarm support.

## License

This fork follows the same license as the original project.
