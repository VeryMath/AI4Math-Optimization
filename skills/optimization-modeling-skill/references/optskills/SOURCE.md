# OptSkills Reference Import

This directory imports the released optimization skill libraries from:

- Repository: `fujiwaranoM0kou/OptSkills`
- URL: https://github.com/fujiwaranoM0kou/OptSkills
- Imported branch: `main`
- Imported commit: `6fbfe62d4fb18a9576274e38a5f87b4b4930fc0e`
- License: MIT, copied in `OPTSKILLS_LICENSE`

Imported reference libraries:

- `skill_library/skill_library_cluster`
- `skill_library/skill_library_learned`
- `skill_library/skill_library_nanoco_learned`

These files are bundled as modeling references. They are not individual installed agent skills and should not be treated as automatically confirmed models for a new user problem. Let the coding agent inspect the library with `rg`, `index.json`, filenames, and targeted file reads. `../../scripts/search_archetypes.py` is only an optional helper for narrowing a large candidate set; always write a fresh modeling checkpoint with explicit assumptions and ambiguities.
