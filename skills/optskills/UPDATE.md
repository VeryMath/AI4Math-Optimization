# Updating the standalone OptSkills library

Run this workflow only after the user explicitly asks for an upstream update.

1. Read `SOURCES.md`, this file, and the current `skill_library/index.json`.
2. Fetch the official `fujiwaranoM0kou/OptSkills` repository.
3. Inspect the current NanoCO, learned, and cluster indexes. If their meaning,
   fields, or directory structure changed, stop and explain the change before
   applying the old selection rule.
4. Form the new selected set in this order: NanoCO first, learned only for IDs
   absent from NanoCO, and cluster only for IDs absent from both when cluster is
   still published as directly usable cards.
5. Compare that selected set with the local package by `skill_id` and ordinary
   text review. Report additions, body changes, source switches, path changes,
   full upstream removals, path conflicts, and license changes before editing.
6. Treat an ID moving from NanoCO to learned or cluster as a source switch, not
   a removal. Never use the index `version` field alone to decide that nothing
   changed.
7. After user confirmation, copy selected card text and selected index fields
   as published upstream. Follow the current upstream `path`; when a path
   changes, move the file and remove the obsolete path.
8. Stop if two IDs resolve to the same path. Do not overwrite either card.
9. Ask again before deleting a card removed from all three upstream libraries.
10. Update `index.json`, `SOURCES.md`, `LICENSE`, and count wording in the
    package or root README files when needed.
11. Validate every index path and run real problems for affected cards. Report
    file updates separately from solver execution and checked results.

Do not add a synchronization script, retain old card copies, rewrite card
content into a local style, or modify sibling skill packages.
