# Agent instructions

Read both work orders before editing. The viewer may import only `lidar_sdk`; it must
not import `stl27l_driver`. Keep discovery, acquisition, rendering, and geometry
separate. Run focused tests before the full suite and test with the independent fixture
before claiming driver independence. Never claim hardware validation from emulation.
All source code, docstrings, inline comments, UI strings, and technical documentation
must be written in English. Do not add Spanish or other-language text to the codebase.

Visual validation boundary: Codex is not authorized to launch, control, or visually test
the Lidar-Shark UI. The human developer must perform all manual visual smoke tests and
capture screenshots. Codex may run non-visual automated tests and document the required
manual checks, but must not claim visual validation or produce screenshots.
