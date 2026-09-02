# Updating the standalone OptSkills library

Run this workflow only after the user explicitly asks for an upstream update.

1. Read `SOURCES.md`, this file, and the current `skill_library/index.json`.
2. Fetch the official `fujiwaranoM0kou/OptSkills` repository.
3. Inspect the current NanoCO, learned, and cluster indexes. If their meaning,
   fields, or directory structure changed, stop and explain the change before
   applying the old selection rule.
4. Before any edit, preflight each selected upstream index and every file it
   names. Within each index, require unique non-empty `skill_id` values and
   unique `path` values. Accept a path only when it is a direct-child Markdown
   filename under that source library. Reject absolute paths, separators or
   nested paths, `.` or `..`, non-`.md` suffixes, missing files, and symlinks.
   Never follow an upstream path outside its source library.
5. Form the new selected set in this order: NanoCO first, learned only for IDs
   absent from NanoCO, and cluster only for IDs absent from both when cluster is
   still published as directly usable cards. Require the selected set itself
   to have unique non-empty IDs and unique paths.
6. Complete the comparison before writing. Compare the selected set with the
   local package by `skill_id` and ordinary text review. Report every addition,
   body change, source switch, path change, full upstream removal, path
   collision, and license or attribution change. Never rely only on the index
   `version` field.
7. Treat an ID moving from NanoCO to learned or cluster as a source switch, not
   a removal. Ask again for every current ID removed from all three upstream
   libraries. Resolve every approval before editing; if any removal is
   declined, leave the entire package unchanged.
8. Compare every proposed path with all currently occupied local paths,
   including paths owned by IDs that will move or disappear. A path occupied
   by a different current ID remains a collision until that ID's move or
   removal is approved. Stop on any unresolved collision, and never overwrite
   a current card while its removal is unresolved.
9. Treat any upstream license, copyright-holder, or attribution change as a
   separate stop. Do not import that release until redistribution compatibility
   is confirmed and the user explicitly approves it. If approved, update
   `LICENSE`, `SOURCES.md`, root `CONTRIBUTORS.md`, and any affected README
   claims together.
10. After all comparisons and approvals are complete, copy selected card text
    and index fields as published upstream. Follow each accepted upstream path;
    when an ID moves, remove its obsolete path. Update every affected card plus
    index, source, count wording, and the `SOURCES.md` upstream snapshot commit
    in `index.json`, `SOURCES.md`, and any affected package or root README files
    in the same reviewable Git change.
11. Validate every index path and run real problems for every affected card.
    Report file updates separately from solver execution and checked results.
    If final validation fails, do not publish the change; restore the pre-update
    state through the repository's normal review/rollback workflow. Do not
    create an old-content backup directory.

Do not add a synchronization script, retain old card copies, rewrite card
content into a local style, modify sibling skill packages, or add integrity,
receipt, manifest, authorization, or execution-unlock mechanisms.
