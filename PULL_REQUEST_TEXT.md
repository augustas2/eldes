# Suggested Pull Request text

Title:

```text
Fix Home Assistant compatibility and add arm/disarm support
```

Description:

```text
Hi,

I have updated this integration to make it work again with recent Home Assistant versions.

Changes included:
- fixed recent Home Assistant compatibility issues;
- fixed Eldes cloud authentication / token refresh handling;
- added PIN code support to Eldes cloud API calls;
- added working arm/disarm support for alarm partitions;
- kept alarm status reading support;
- exposed alarm_control_panel, sensors, binary sensors and switches.

Tested with:
- Home Assistant;
- Eldes ESIM384;
- Eldes Cloud account;
- alarm status reading;
- arm away / disarm commands.

This is shared to help other users who still rely on this integration.

Thanks,
Danyct80
```
