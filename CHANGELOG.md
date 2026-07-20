# Changelog

## 0.2.1 - 2026-07-19

- Make the package self-contained by moving rendering, project selection,
  bundled-source expansion, and required conversion helpers under
  `tex2markdown`.
- Carry forward the validated source-native title handling for conditional,
  manual, custom-command, macro-expanded, accented, and compact-math titles.
- Restrict built distributions to the standalone `tex2markdown` package.

## 0.2.0 - 2026-07-17

- Replace metadata and result objects with `convert()` and `convert_path()`,
  which each return one Markdown string.
- Add recursive directory conversion with automatic or explicit main-file
  selection.
- Make titles and abstracts source-only and preserve `\today` literally.
- Simplify the command line to file, folder, or standard-input conversion.
- Remove public bundle, metadata, diagnostics, metrics, warnings, risk, and
  retrieval-status interfaces.

## 0.1.0

- Initial public extraction of the ClaimSpy retrieval conversion strategy.
