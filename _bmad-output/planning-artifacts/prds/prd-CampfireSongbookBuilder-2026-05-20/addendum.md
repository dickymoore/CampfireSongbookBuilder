# PRD Addendum

## Technical Notes Captured During Discovery

- “Neat documents” should be interpreted operationally as readable output with limited wasted whitespace, not as a visual redesign problem.
- Agentic verification should happen before Dicky is asked to open generated output artifacts.
- Per-song scoring likely needs to compose with the existing Quality Signal system rather than bypass it.
- Backup-first remediation is a hard constraint for direct agent edits.
- A likely architectural fork to resolve later:
  - modify canonical cached content directly after backup, or
  - introduce a remediated-current-state layer above raw caches
- Document neatness may require artifact-level metrics such as whitespace density, sparse-page detection, song-fragmentation checks, or over-separated block detection.
- Remediation scope should probably start with structure-preserving cleanup rather than semantic rewriting:
  - whitespace normalization
  - section restructuring
  - removal of obvious scraper residue
  - normalization of repeated junk blocks
- A strong safety requirement for this slice is bounded retry behavior so agents do not repeatedly “improve” the same content without converging.
