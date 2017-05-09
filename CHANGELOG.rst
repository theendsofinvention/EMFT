(unreleased)
------------

New
~~~
- Path settings are now dependent on the current Windows GUID. [132nd-
  etcher]

  WARNING: all previous settings will be lost !
  Namely:
  - Saved Games path
  - Output folder for single miz re-ordering
  - Last miz file for single miz re-ordering
  - Source & output folder for automated miz re-ordering
  - active DCS installation of Skins tab
  - Last directory for the Roster tab
  - Custom DCS installation paths

  Fixes #12
- Roster tab detects position of aircrafts; (Tbilisi, Vaziani, Soganlug,
  Senaki, Kutaisi and any FARP) [132nd-etcher]
- Allow for one custom DCS installation. [132nd-etcher]
- "Roster" tab: displays client Groups from a MIZ file. [132nd-etcher]
- "Skins" tab: add button to refresh skins. [132nd-etcher]
- Add link to online changelog. [132nd-etcher]
- Using gitchangelog to maintain changelog. [132nd-etcher]

Changes
~~~~~~~
- Dev move ProgressAdapter to its own module. [132nd-etcher]
- Skin filters are now case insensitive. [132nd-etcher]
- Remove 'beta' and 'alpha' as update channels. [132nd-etcher]

Fix
~~~
- Scan for TRMT crash fixed when no local TRMT exists. [132nd-etcher]
- Fixed performances on skins tab update. [132nd-etcher]
- Saved_games path wasn't read from Config. [132nd-etcher]
- Show develop changelog on experimental versions. [132nd-etcher]


