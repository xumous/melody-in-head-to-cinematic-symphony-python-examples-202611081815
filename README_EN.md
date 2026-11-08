# A Melody in My Head → Cinematic Epic Symphony (4 Minutes)

**Language**: [中文](README.md) · [English](README_EN.md) · [日本語](README_JA.md) · [Français](README_FR.md)

Turning a humming little numbered-notation tune "stuck in my head" into a 4-minute, streaming-ready cinematic epic
score: rendered entirely in Python, sampled with the Sonatina Symphonic Orchestra (SSO) through `pysfizz`, and
mixed/mastered with hand-written NumPy + SciPy DSP — no DAW involved.

Final deliverable: **240.00 s / −15.35 LUFS / −1.02 dBTP / LRA 15.0 LU**, 8 sections, 6 stems, format-1 MIDI.

---

## 1. Where the Deliverables Are

| File                               | Description                                                                                          |
|------------------------------------|------------------------------------------------------------------------------------------------------|
| `epic_final.flac`                  | Final master (lossless, from a 24-bit source)                                                        |
| `epic_final.mp3`                   | Final master (streaming distribution version)                                                        |
| `epic_final.mid`                   | Format 1 / 6 tracks / 480 TPQ; ch0 lead brass, ch1 low brass, ch2 percussion, ch3 strings, ch4 choir |
| `premaster.flac` / `premaster.mp3` | Pre-master version (no limiting, no loudness alignment)                                              |
| `spectrogram_final.png`            | Spectrogram + average spectrum (for acceptance checks)                                               |
| `loudness_report.txt`              | Auto-generated render report (loudness, peaks, bands, per-section RMS, stems, acceptance verdict)    |
| `stems/*.flac` / `stems/*.mp3`     | 6 stems: `melody_lead` / `brass` / `low_brass_bass` / `strings` / `percussion` / `choir_hybrid`      |
| `probe.flac` / `probe.mp3`         | Sample-availability audition: brass major triad + timpani + bass drum/snare + string tremolo + choir |

The `renders（就是喇叭从弱到强）/` folder keeps the complete artifacts of every version from v1 to
v5 (`epic_final.wav`, `premaster.wav`, stems, spectrograms, reports), so you can compare the "crescendo" evolution
directly. `v2（最好听）` ("best sounding") is the subjectively nicest take, and `v5` is the delivery version that
satisfies every objective criterion and the dynamic-step ladder.

---

## 2. Quick Start

### 2.1 Requirements

```
Python 3.14 (tested)
numpy  scipy  soundfile  matplotlib  pyloudnorm  requests  pysfizz==0.1.3
ffmpeg (only for cross-verification and transcoding; optional)
```

`pysfizz` is the Python binding of the sfizz sampler engine and renders SFZ instruments offline from MIDI events.
Without it, `epic_engine.py` falls back to `Synth = None` (only the stub-sampler pipeline in `tools_selftest.py` remains
runnable).

### 2.2 Sample Library

- The library ships inside the repo at `soundfonts/Sonatina Symphonic Orchestra/` (641 files, ~283 MB — an **on-demand
  subset** of the 1.39 GB full package).
- **Known trap**: `pysfizz` only accepts pure ASCII paths. A non-ASCII project directory raises
  `No mapping for the Unicode character exists in the target multi-byte code page`.
  Fix it with an ASCII junction pointing at the library:

  ```powershell
  cmd /c mklink /J D:\_sso "D:\MasterXu2026091\melody-in-head-to-cinematic-symphony-python-examples-202611081815\soundfonts\Sonatina Symphonic Orchestra"
  ```

  `epic_engine.SSO_ROOT` prefers `D:/_sso` and falls back to the in-repo path only when the junction is missing.

### 2.3 Render & Archive

```powershell
# 1) Full-pipeline self-test (no samples needed, stub sampler, ~1 minute)
python tools_selftest.py

# 2) Minimal source validation (writes probe.wav; check that it sounds like real brass)
python probe_sso.py
python tools_check_probe.py

# 3) Render the final version (v5, written into renders/v5)
python v5_epic_orchestrator.py

# 4) Copy v5 artifacts to the repo root and run final checks
python tools_package.py v5

# 5) Cross-verify loudness with ffmpeg (appends to loudness_report.txt)
python tools_ffmpeg_verify.py
```

> Note: `v1..v5` and `tools_package.py` hardcode the output path `renders/vN`, while the archived folder has been
> renamed to `renders（就是喇叭从弱到强）`. Re-rendering therefore creates a **new** `renders/` directory instead of
> overwriting the archive; change the path first if you want to overwrite it.

---

## 3. Directory Layout

```
melody-in-head-to-cinematic-symphony-python-examples-202611081815/
├── epic_engine.py                  # ★ Core library: sampler + orchestrator + mixer + DSP + mastering + MIDI + report
├── v1_epic_orchestrator.py         # v1: four-act skeleton (baseline PROFILE)
├── v2_epic_orchestrator.py         # v2: spectrum & balance (inherits v1 PROFILE)
├── v3_epic_orchestrator.py         # v3: brightness & texture (inherits v2)
├── v4_epic_orchestrator.py         # v4: dynamic contrast & mastering (inherits v3)
├── v5_epic_orchestrator.py         # v5: final delivery (inherits v4) ★ recommended entry point
├── original_script.py              # Byte-identical read-only copy of the original 4-min symphony script (44.1 kHz synth version)
├── RESEARCH_NOTES.md               # 30 executable "why it is epic" rules + mix values + measured constraints
│
├── first/                          # Project origin: three single-file scripts and their outputs
│   ├── 我脑海里的一段旋律_python_20261107_65b3ca.py/.exe        # Piano single melody + WAV/MIDI
│   ├── 我脑海里的一段旋律扩展4分钟_python_20261108_050346.py/.exe  # 4-minute piano version (pickup handling)
│   ├── 我脑海里的一段旋律扩展4分钟最初交响版_python_20261108_f84da8.py/.exe # Original symphony version (= original_script.py)
│   └── piano.flac/.mid/.mp3  piano_4min.*  piano_epic_4min.*    # Renders of the scripts above
│
├── soundfonts/Sonatina Symphonic Orchestra/   # On-demand SSO v4.0 subset (Brass/Strings/Woodwinds/Percussion/Chorus + Samples*)
├── logs/                           # Download and self-test logs
│   ├── download.log / download.err         # Whole-zip approach (BadZipFile, abandoned)
│   ├── fetch.log / fetch_samples.log       # SFZ and sample fetching (including failed retries)
│   ├── sample_list.json                    # Final list of 702 samples to download (priority-sorted)
│   └── selftest.log                        # Stub-sampler self-test output (finishes in 47 s)
│
├── renders（就是喇叭从弱到强）/    # Full artifact archive per version
│   ├── selftest/                   # Stub-sampler outputs
│   ├── v1/ v2（最好听）/ v3/ v4/ v5/   # Per version: epic_final.* / premaster.* / stems/ / spectrogram / report
│
├── stems/                          # Final 6 stems (flac + mp3)
├── __pycache__/                    # Python bytecode cache
└── README*.md                      # This documentation (ZH/EN/JA/FR)
```

### 3.1 Tool Scripts (`tools_*.py` — standalone diagnostics and file-moving helpers)

| Script                   | Purpose                                                                                                                                                                                                                                                   |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `tools_download_sso.py`  | Whole-package download: gh-proxy mirror + Range resume + zip validation. It stalls at 348 MB in practice, so it was abandoned but kept as a fallback                                                                                                      |
| `tools_probe_mirrors.py` | Concurrently benchmarks 6 GitHub accelerators (ghfast / gh-proxy / moeyy / gitmirror / kgithub / ghproxy.net) and prints kB/s                                                                                                                             |
| `tools_fetch_subset.py`  | Fetches whitelisted SFZ text → recursively resolves `#include` → collects `sample=` paths → downloads samples with 16 workers; it preserves the repo layout so sfizz can resolve relative paths                                                           |
| `tools_fetch_samples.py` | **The working solution**: imports `epic_engine.INST` to download only samples actually used; rotates multiple jsDelivr CDNs + reuses a `requests` Session + Range resume + three-level priority (perc → brass → strings → winds → choir) + 3 retry rounds |
| `tools_move_samples.py`  | Fixes samples mistakenly placed inside per-instrument subfolders (SSO's `sample=../Samples/...` resolves relative to the main SFZ directory)                                                                                                              |
| `tools_status.py`        | Loads each SFZ in `epic_engine.INST`, reports success and playable key range (confirms the subset is sufficient)                                                                                                                                          |
| `probe_sso.py`           | Minimal audition: C major triad (trumpet/horn/trombone/tuba) + timpani + bass drum/snare + string tremolo + choir → `probe.wav`                                                                                                                           |
| `tools_check_probe.py`   | Analyzes per-segment RMS, peak and spectral centroid of `probe.wav`, proving it is sampled, not sinusoidal                                                                                                                                                |
| `tools_selftest.py`      | Runs the whole chain with a stub sampler (noise instead of SSO): orchestration → stems → DSP → mastering → MIDI → report in 47 s, validating code paths and memory                                                                                        |
| `tools_diagnose.py`      | Stem peak/RMS, 8-section RMS curve, full-track band distribution                                                                                                                                                                                          |
| `tools_bands.py`         | Per-stem and final-mix band energy shares (locates the "missing high end")                                                                                                                                                                                |
| `tools_check_midi.py`    | Parses MIDI header, track count, TPQ, note-ons per channel, last-tick duration                                                                                                                                                                            |
| `tools_ffmpeg_verify.py` | Cross-verifies LUFS / True Peak / LRA with `ffmpeg loudnorm` and appends to `loudness_report.txt`                                                                                                                                                         |
| `tools_sample_bands.py`  | Analyzes raw SSO sample spectra directly (library vs render chain; path hardcoded to `D:/_sso`)                                                                                                                                                           |
| `tools_hf_test.py`       | Stage-by-stage spectrum comparison: raw sample / HP+EQ / compression / master chain, locating where the high end is lost                                                                                                                                  |
| `tools_package.py`       | Copies the final mix, report, spectrogram and stems of a given version (default v5) to the repo root and runs final checks                                                                                                                                |

---

## 4. Music Design (hard rules encoded in code)

### 4.1 Structure: 8 sections × 30 s (96 beats @ 192 BPM)

| # | Section | Time      | Scoring and function                                                                                                             |
|---|---------|-----------|----------------------------------------------------------------------------------------------------------------------------------|
| 0 | Intro   | 0:00–0:30 | String tremolo + low celli pad + sub bass + heartbeat bass drum + distant timpani + harp + flute theme teaser + roll riser       |
| 1 | A1      | 0:30–1:00 | **Horn solo lead melody** (first statement) + warm strings + low-brass pad + timpani heartbeat + light snare                     |
| 2 | B       | 1:00–1:30 | **Flute lead melody** (lightly doubled by oboe) + brass retreats to harmonic pads; the only "breathing" section                  |
| 3 | A2      | 1:30–2:00 | **Trumpet takes the melody** + horn counterpoint + low-brass eighth-note ostinato + denser snare                                 |
| 4 | C1      | 2:00–2:30 | **Trumpet section in unison** + string ostinato + tremolo + full percussion; from bar 20 it modulates to **D♭ (Neapolitan ♭II)** |
| 5 | C2      | 2:30–3:00 | **Full brass octave unison + choir + high winds + electronic kick**; triplet ostinato; ends V→Cm                                 |
| 6 | Outro1  | 3:00–3:30 | Horn returns to the theme (ebb tide), layers recede, brass harmony closes                                                        |
| 7 | Outro2  | 3:30–4:00 | Solo violin/flute echoes, two-stage crescendo on V (G) → **C major (Picardy third) final hit** + 3.5 s natural decay             |

The same theme is stated four times with an ascending force ladder and brass grouping: horn → trumpet → brass unison →
full brass + choir.

### 4.2 Melody and Harmony

- The melody is stored as numbered-notation tables: `PICKUP` (2-beat anacrusis) + `MAIN` (77-beat body). Notation rules
  are documented at the top of `first/我脑海里的一段旋律_python_20261107_65b3ca.py` (`-` extends beats, `【】` halves
  durations, `{}` means legato, `————>` is a fading ending).
- C harmonic minor; core progression `Cm – A♭ – Fm – G` (changes every 2 bars, 12 cycles); `D♭` is inserted at the end
  of C1, and Outro2 closes `G → C`.
- The melody sits in the most brilliant brass register (trumpet F4–C5 range), so simply re-orchestrating the same line
  naturally makes it sound "bigger".

---

## 5. Engine Architecture

```
SSO samples (pysfizz / SFZ)
        │  Sampler.note(inst, pitch, vel, on_dur, tail)  → single-note render with disk cache
        ▼
Orchestrator (8 sec_* methods) ──► Mixer (6 buses + 2 reverb sends + kick sidechain key)
        │                          MIDI events recorded in sync
        ▼
process_buses (per-stem DSP) ──► mix_down (sum + reverb wet curve) ──► premaster.wav
        │
        ▼
master_chain: ① 20 Hz HP ② light 2–4 kHz cut ③ 6 kHz shelf ④ glue compression GR≤3
              ⑤ tanh saturation THD 1–2% ⑥ loudness alignment + true-peak limiting iterations ⑦ 3.5 s fade-out
        │
        ▼
epic_final.wav + epic_final.mid + spectrogram_final.png + loudness_report.txt
```

- **Every musical parameter lives in the `PROFILE` dict**: instrument choice, velocities, textures, percussion density,
  bus levels, reverb, mastering targets. The v1–v5 scripts only change `PROFILE`, never the engine.
- **6 buses**: `lead` (lead brass/flute/violin), `brass` (brass harmony), `low` (low brass + sub + low
  strings), `strings`, `perc`, `choir`.
- **Hybrid layer**: `synth_harp` / `synth_bass_inst` / `synth_choir` / `synth_bass_drum` are synthesizer timbres
  inherited from the original script, layered on top of samples for electronic kick punch and choir weight.
- **Sample cache**: `Sampler` caches by `inst|pitch|vel|on_dur|tail` into `cache/*.npz`, so repeated notes are never
  re-rendered.

### 5.1 Per-Bus Processing (values tuned by measurement)

| Bus              | Processing                                                                                                                                                                                       |
|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `brass` / `lead` | HP 80 Hz (18 dB/oct) → 200–400 Hz −1.5 dB (de-boxiness) → 2–5 kHz +2.5 dB (presence) → 5 kHz shelf +3.5 dB (air) → optional harmonic exciter → 2:1 / 30 ms / 250 ms glue compression (GR 1–2 dB) |
| `low`            | **No HP**, preserve 40–100 Hz → kick sidechain ducking (−18 dB / 3:1 / 5 ms / 120 ms, 5–6.5 dB depth) → 2:1 compression                                                                          |
| `strings`        | HP 80 Hz → 150–350 Hz −2 dB → 4 kHz shelf +1.5 dB → exciter (4 dB lower than brass) → 1.5:1 compression                                                                                          |
| `perc`           | 300–500 Hz dynamic cut −2 dB (avoid low-mid brass) → HP 28 Hz → 3–6 kHz +2 dB                                                                                                                    |
| `choir`          | HP 60 Hz → 300–600 Hz −1.5 dB → 4 kHz shelf +1 dB                                                                                                                                                |
| `reverb`         | Long IR for brass/strings/choir (2.8–3.3 s), short IR for percussion (1.2–1.6 s); C2 wet is **25–28% lower** than A1 (the climax must stay "dry" to keep impact)                                 |

### 5.2 Master Chain

20 Hz HP (24 dB/oct) → 2–4 kHz −0.8 dB → 6 kHz shelf +1.5 dB → glue compression 1.8:1 / 35 ms / 250 ms / GR ≤ 3 dB →
light `tanh` saturation (THD 1–2%) → loudness alignment + true-peak limiting (4× oversampled block measurement, ≤3
iterations) → 3.5 s natural fade-out.

---

## 6. Version Evolution (why there are 5 orchestrators)

| Version | Goal                              | Key changes                                                                                            | Objective result                                                                                               |
|---------|-----------------------------------|--------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| v1      | Get the four-act skeleton running | SSO samples + hybrid layers from the original script; 8-section scoring table; D♭ lift; Picardy ending | Duration/LUFS/TP pass, but spectrum is dark and the lead is buried by strings (lead −43.6 vs strings −35.2 dB) |
| v2      | Spectrum and balance              | Presence/air EQ, lead bus +7.6 dB, strings −2.5 dB, perc +5.1 dB, strings HP 80 Hz                     | 120–300 Hz share 41.9%→27.2%, lead rises                                                                       |
| v3      | Brightness and texture            | Harmonic exciter; A2 horn counterpoint; C2 triplet ostinato; C1 sixteenth-note snare; density +15%     | 5–10 kHz 0.03%→0.09%, melody −33.7 dB                                                                          |
| v4      | Dynamic contrast and mastering    | intro 0.78, climax 1.15, −14.5 LUFS, 3.3 s reverb                                                      | Intro→C2 contrast 13.3 dB, THD 1.96%                                                                           |
| **v5**  | Final polish                      | Fixed velocity ladder, exciter −17 dB, climax 1.2, TP measured with 4× oversampled blocks              | Contrast **14.3 dB**, TP **−1.02 dBTP**, consistent with ffmpeg                                                |

---

## 7. Objective Acceptance (v5)

| Item                | Result                                                                                  |
|---------------------|-----------------------------------------------------------------------------------------|
| Duration            | 240.00 s (PASS, 240 ± 2)                                                                |
| Integrated loudness | −15.35 LUFS (PASS, −16…−14)                                                             |
| True Peak           | −1.02 dBTP (PASS, ≤ −1.0)                                                               |
| Loudness Range      | 15.0 LU (film/classical dynamics, not squashed 3–6 LU)                                  |
| 50–100 Hz energy    | −48.3 dB (low brass/timpani doing their job)                                            |
| 2–5 kHz energy      | −69.7 dB (brass has bite)                                                               |
| Stems               | All 6 non-empty                                                                         |
| MIDI                | Format 1, 6 tracks, 480 TPQ, 239.93 s; note-ons on ch0–ch4 = 664 / 737 / 883 / 588 / 60 |
| ffmpeg cross-check  | −15.36 LUFS / −1.02 dBTP / LRA 15.00 (matches `pyloudnorm`)                             |

Per-section RMS (pre-master, dBFS):

| Intro | A1    | B     | A2    | C1    | C2        | Outro1 | Outro2 |
|-------|-------|-------|-------|-------|-----------|--------|--------|
| −36.6 | −29.8 | −34.3 | −28.3 | −24.6 | **−22.3** | −30.6  | −31.6  |

Intro → C2 spans 14.3 dB, and section B (−34.3) sits below A1 (−29.8), yielding the "establish – breathe – escalate –
explode – decay" arc.

---

## 8. Known Constraints (measured, not theoretical)

1. **`pysfizz` only accepts ASCII paths**: the project directory contains Chinese characters, so the `D:\_sso` junction
   is mandatory — see §2.2.
2. **Network**: direct `raw.githubusercontent.com` connections reset (WinError 10054); the `codeload` whole package
   stalls at 348 MB; `gh-proxy` delivers only 20–60 kB/s per connection. The final solution uses
   jsDelivr's `gcore` / `testingcf` CDNs with 1–2 connections each, measured at ~160 kB/s per connection.
3. **SSO samples are dark in the high end by nature**: `trumpets-sus-a#4.wav` has only 0.2% energy at 5–10 kHz,
   and `horns-stc` / `celli-stc` have 0%. Pure EQ boosts only raise noise, so a harmonic exciter is used (second-order
   nonlinearity within 1.2–5 kHz → HP 5 kHz → mixed at −17 dB relative level).
4. **Learning/demo scope**: SSO is a free 2011 library (CC Sampling Plus 1.0). Even with the exciter, brightness cannot
   reach real Hollywood recording standards; a commercial library (e.g., Cinesamples / Berlin series) would be needed
   for a theatrical release.
5. **Archive folder name contains Chinese characters and parentheses**: the scripts write to `renders/vN`, which differs
   from the archive `renders（就是喇叭从弱到强）`, so re-rendering creates a new folder instead of overwriting the
   archive.

---

## 9. License & Credits

- Samples: **Sonatina Symphonic Orchestra** (CC Sampling Plus 1.0, v4.0, by Mattias Westlund, GitHub: `peastman/sso`).
- Rendering: **sfizz / pysfizz**.
- Melody, orchestration, DSP, mastering and all code: this project's author.
- Research basis and parameter sources: see [RESEARCH_NOTES.md](RESEARCH_NOTES.md) (30 hard rules of epic scoring,
  EQ/compression/loudness references, and self-assessment).
