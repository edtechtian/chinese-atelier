# Public learning edition

Open https://edtechtian.github.io/chinese-atelier/ in a modern browser.

The public edition runs the existing Python lesson, assessment, review and daily-learning engine inside a Web Worker using a pinned, self-hosted Pyodide 0.29.0 WebAssembly runtime. It does not expose the local Python HTTP server or student files. No server account, API key, paid service or install is needed. The first visit downloads about 13 MB of runtime and course data.

All 20 source-linked units, 100 microsteps, 268 vocabulary records, 162 formative questions and the published visual activities remain available. The publication copy still excludes original PPTX and the full original-image archive. No recorded course audio or speech recognition is added.

## Saved work

Progress, responses, review schedules and local curriculum edits are stored in IndexedDB in the current browser on the current device. Save completes only after the browser persistence callback succeeds. Clearing site data, private browsing expiry or changing devices can remove or separate records. Export a portfolio from the student view for a backup or to share with a teacher. There is no automatic cloud or cross-device synchronization.

One tab per browser profile may hold the learning record. A second tab receives an explanatory error rather than overwriting another tab's state. Modern browsers with WebAssembly, Workers, IndexedDB and JavaScript are required.

## Teacher view

Visit `site/#/teacher/overview` and choose **Open same-device teaching view**. It sees only records in this browser. This is a separate teaching interface, not an authentication boundary; reviewer identity is not authenticated. The local Python application retains its protected teacher key and original source-import controls. The browser edition does not upload original PowerPoints. Do not use browser feedback as an authenticated school assessment or official IB grade.

## Rebuild

Run `python3 scripts/build_browser_site.py` from the repository root after changing original application code or curriculum. It regenerates the static UI files and `site/course.zip` using the same source modules. The runtime files are pinned under `site/runtime/`; the timezone wheel hash is checked against `pyodide-lock.json`. Use the normal Python test suite and, with Node.js available, `node tests/browser_engine.mjs` to run the existing answer keys inside WebAssembly.

For local browser testing, run `python3 -m http.server 8012` and open `http://localhost:8012/site/`. This static server is separate from the original `python3 server.py` application. No student data is included in the published package.
