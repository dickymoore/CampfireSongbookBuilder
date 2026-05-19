# PRD Addendum

## Technical Notes Captured During Discovery

- Preferred output pipeline direction: Markdown source/intermediate representation, then `.docx`, then PDF.
- Open-source document formats are acceptable if they make the pipeline more reliable or easier to maintain.
- Intelligent layout is desired later, especially to avoid bad page breaks, unreadable tab/chord wrapping, and pages of low-value content.
- UI is not a priority for v1. The CLI/file interface is acceptable, especially when AI agents can operate it.
- Architecture should evaluate whether review state belongs in the existing JSONL cache records, a separate review/status file, or both. The PRD intentionally leaves that mechanism open because it affects migration, cache compatibility, and future refetch behavior.
- Architecture should evaluate local PDF conversion options only after Markdown and `.docx` outputs are stable. PDF failure should be recoverable and should not destroy earlier artifacts.
