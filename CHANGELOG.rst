(unreleased)
------------

Changes
~~~~~~~
- Dve: reqs: update reqs. [132nd-etcher]

Fix
~~~
- Fix bug in log tab: new records are now filtered. [132nd-etcher]

Other
~~~~~
- Use pefile instead of win32api to infer executable file version (#82)
  [132nd-etcher]

  [Finishes #148568267]


0.4.3 (2017-07-11)
------------------
- Create CODE_OF_CONDUCT.md. [132nd-etcher]


0.4.2 (2017-07-08)
------------------

New
~~~
- Add warning when leaving the radio presets tab without saving. [132nd-
  etcher]
- Add radio presets tab. [132nd-etcher]
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
- Set "Save" button as default in output folder edit dialog. [132nd-
  etcher]
- Re-worked the re-ordering system. [132nd-etcher]

  Added pre-selection of output folders, added the possibility to define a number of profiles (TRMT, SDCM, ...) to the auto-reordering, and started working on encapsulating all of this in a manageable framework to ease maintenance & growth.
  Finish #14_reorder-profiles
  Closes #14
- Changed layout margins. [132nd-etcher]
- Using single re-order button for both manual and auto mode. [132nd-
  etcher]
- Tab_reorder: branches are now sorted alphabetically, with "master" and
  "develop" always on top. [132nd-etcher]
- Reorder tab: add explicit error message on remote probing failure.
  [132nd-etcher]
- Shows red "error" text instead of staying stuck on "Probing..."
  [132nd-etcher]
- Redirect calls to Appveyor and Github to the new repo. [132nd-etcher]

  Following the transfer of ownership of the TRMT repo
- Dev move ProgressAdapter to its own module. [132nd-etcher]
- Skin filters are now case insensitive. [132nd-etcher]
- Remove 'beta' and 'alpha' as update channels. [132nd-etcher]

Fix
~~~
- Auto reorder: fixed bug when no branch is selected. [132nd-etcher]
- Fixed pending or failed AV build not detected. [132nd-etcher]
- Fix lag due to scanning of remote branch. [132nd-etcher]
- Fixed laggy progress dialog when downloading a MIZ file. [132nd-
  etcher]
- Fixed MIZ files being decoded twice during re-ordering. [132nd-etcher]
- Prevent double instantiation of EMFT. [132nd-etcher]

  closes #27
- Re-order scan for remote branches on GH during refresh. [132nd-etcher]

  closes #17
- Re-order tab: make an initial scan at startup. [132nd-etcher]
- Fixed config not initializing with corrupt config file. [132nd-etcher]
- Fixed Browse dialog adding "*.*" string after paths. [132nd-etcher]
- Fixed wrong appveyor project selected. [132nd-etcher]
- Fixed config file upgrade from v3 to v4. [132nd-etcher]
- Fixed opening the radio presets file in explorer. [132nd-etcher]
- Allow for spaces in a radio channel description. [132nd-etcher]
- Fixed opening of output path in re-order tab. [132nd-etcher]
- Fix bug in config file handling. [132nd-etcher]
- Scan for TRMT crash fixed when no local TRMT exists. [132nd-etcher]
- Fixed performances on skins tab update. [132nd-etcher]
- Saved_games path wasn't read from Config. [132nd-etcher]
- Show develop changelog on experimental versions. [132nd-etcher]

Other
~~~~~
- Dev: fix: remove default arg. [132nd-etcher]
- Update changelog. [132nd-etcher]
- Create README.md. [132nd-etcher]