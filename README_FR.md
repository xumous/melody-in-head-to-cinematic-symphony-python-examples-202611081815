# Une mélodie dans ma tête → Symphonie épique cinématographique (4 minutes)

**Langue** : [中文](README.md) · [English](README_EN.md) · [日本語](README_JA.md) · [Français](README_FR.md)

Transformer une petite mélodie en notation chiffrée « qui tourne dans la tête » en une partition épique de cinéma de 4
minutes, prête pour le streaming : rendu entièrement en Python, échantillons du Sonatina Symphonic Orchestra (SSO)
chargés via `pysfizz`, mixage et mastering réalisés avec un DSP écrit à la main en NumPy + SciPy — sans aucun DAW.

Livrable final : **240,00 s / −15,35 LUFS / −1,02 dBTP / LRA 15,0 LU**, 8 sections, 6 stems, MIDI format 1.

---

## 1. Où trouver les livrables

| Fichier                            | Description                                                                                                                                    |
|------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `epic_final.flac`                  | Master final (sans perte, issu d'une source 24 bits)                                                                                           |
| `epic_final.mp3`                   | Master final (version diffusion streaming)                                                                                                     |
| `epic_final.mid`                   | Format 1 / 6 pistes / 480 TPQ ; ch0 cuivres mélodie, ch1 cuivres graves, ch2 percussions, ch3 cordes, ch4 chœur                                |
| `premaster.flac` / `premaster.mp3` | Version avant mastering (sans limitation ni alignement de loudness)                                                                            |
| `spectrogram_final.png`            | Spectrogramme + spectre moyen (pour la validation)                                                                                             |
| `loudness_report.txt`              | Rapport de rendu généré automatiquement (loudness, crêtes, bandes, RMS par section, stems, verdict d'acceptation)                              |
| `stems/*.flac` / `stems/*.mp3`     | 6 stems : `melody_lead` / `brass` / `low_brass_bass` / `strings` / `percussion` / `choir_hybrid`                                               |
| `probe.flac` / `probe.mp3`         | Audition de disponibilité des sources : accord parfait majeur aux cuivres + timbales + grosse caisse/caisse claire + trémolo de cordes + chœur |

Le dossier `renders（就是喇叭从弱到强）/` conserve l'intégralité des artefacts de chaque version, de v1 à
v5 (`epic_final.wav`, `premaster.wav`, stems, spectrogrammes, rapports), ce qui permet de comparer directement
l'évolution « crescendo ». `v2（最好听）` (« la plus agréable à l'oreille ») est la prise la plus plaisante
subjectivement, et `v5` est la version livrée qui satisfait tous les critères objectifs et l'échelle de dynamique.

---

## 2. Démarrage rapide

### 2.1 Prérequis

```
Python 3.14 (testé)
numpy  scipy  soundfile  matplotlib  pyloudnorm  requests  pysfizz==0.1.3
ffmpeg (uniquement pour la contre-vérification et le transcodage ; facultatif)
```

`pysfizz` est le binding Python du moteur d'échantillonnage sfizz et rend les instruments SFZ hors ligne à partir d'
événements MIDI. Sans lui, `epic_engine.py` retombe sur `Synth = None` (seul le pipeline à échantillonneur factice
de `tools_selftest.py` reste exécutable).

### 2.2 Bibliothèque d'échantillons

- La bibliothèque est fournie dans le dépôt sous `soundfonts/Sonatina Symphonic Orchestra/` (641 fichiers, ~283 Mo — un
  **sous-ensemble à la demande** du paquet complet de 1,39 Go).
- **Piège connu** : `pysfizz` n'accepte que des chemins purement ASCII. Un dossier de projet contenant des caractères
  non ASCII lève
  `No mapping for the Unicode character exists in the target multi-byte code page`.
  La solution est une jonction ASCII pointant vers la bibliothèque :

  ```powershell
  cmd /c mklink /J D:\_sso "D:\MasterXu2026091\melody-in-head-to-cinematic-symphony-python-examples-202611081815\soundfonts\Sonatina Symphonic Orchestra"
  ```

  `epic_engine.SSO_ROOT` privilégie `D:/_sso` et ne retombe sur le chemin interne au dépôt que si la jonction est
  absente.

### 2.3 Rendu et archivage

```powershell
# 1) Auto-test du pipeline complet (sans échantillons, échantillonneur factice, ~1 minute)
python tools_selftest.py

# 2) Validation minimale des sources (écrit probe.wav ; vérifier que cela ressemble à de vrais cuivres)
python probe_sso.py
python tools_check_probe.py

# 3) Rendu de la version finale (v5, écrite dans renders/v5)
python v5_epic_orchestrator.py

# 4) Copie des artefacts v5 à la racine du dépôt et vérifications finales
python tools_package.py v5

# 5) Contre-vérification de la loudness avec ffmpeg (ajout dans loudness_report.txt)
python tools_ffmpeg_verify.py
```

> Remarque : `v1..v5` et `tools_package.py` codent en dur le dossier de sortie `renders/vN`, alors que le dossier
> d'archive a été renommé `renders（就是喇叭从弱到强）`. Un nouveau rendu crée donc un **nouveau** dossier `renders/` au
> lieu d'écraser l'archive ; modifiez le chemin au préalable si vous voulez l'écraser.

---

## 3. Arborescence

```
melody-in-head-to-cinematic-symphony-python-examples-202611081815/
├── epic_engine.py                  # ★ Bibliothèque centrale : échantillonneur + orchestrateur + mixeur + DSP + mastering + MIDI + rapport
├── v1_epic_orchestrator.py         # v1 : squelette en quatre actes (PROFILE de référence)
├── v2_epic_orchestrator.py         # v2 : spectre et équilibre (hérite du PROFILE v1)
├── v3_epic_orchestrator.py         # v3 : brillance et texture (hérite de v2)
├── v4_epic_orchestrator.py         # v4 : contraste dynamique et mastering (hérite de v3)
├── v5_epic_orchestrator.py         # v5 : livraison finale (hérite de v4) ★ point d'entrée recommandé
├── original_script.py              # Copie en lecture seule, identique octet pour octet, du script symphonique original de 4 min (version synthé 44,1 kHz)
├── RESEARCH_NOTES.md               # 30 règles exécutables « pourquoi c'est épique » + valeurs de mixage + contraintes mesurées
│
├── first/                          # Origine du projet : trois scripts monofichiers et leurs sorties
│   ├── 我脑海里的一段旋律_python_20261107_65b3ca.py/.exe        # Mélodie piano seule + WAV/MIDI
│   ├── 我脑海里的一段旋律扩展4分钟_python_20261108_050346.py/.exe  # Version piano de 4 min (gestion de l'anacrouse)
│   ├── 我脑海里的一段旋律扩展4分钟最初交响版_python_20261108_f84da8.py/.exe # Version symphonique initiale (= original_script.py)
│   └── piano.flac/.mid/.mp3  piano_4min.*  piano_epic_4min.*    # Rendus des scripts ci-dessus
│
├── soundfonts/Sonatina Symphonic Orchestra/   # Sous-ensemble SSO v4.0 (Brass/Strings/Woodwinds/Percussion/Chorus + Samples*)
├── logs/                           # Journaux de téléchargement et d'auto-test
│   ├── download.log / download.err         # Approche zip complet (BadZipFile, abandonnée)
│   ├── fetch.log / fetch_samples.log       # Récupération des SFZ et échantillons (y compris les échecs de reprise)
│   ├── sample_list.json                    # Liste finale des 702 échantillons à télécharger (triée par priorité)
│   └── selftest.log                        # Sortie de l'auto-test à échantillonneur factice (47 s)
│
├── renders（就是喇叭从弱到强）/    # Archive complète des artefacts par version
│   ├── selftest/                   # Sorties de l'échantillonneur factice
│   ├── v1/ v2（最好听）/ v3/ v4/ v5/   # Par version : epic_final.* / premaster.* / stems/ / spectrogramme / rapport
│
├── stems/                          # Les 6 stems finaux (flac + mp3)
├── __pycache__/                    # Cache de bytecode Python
└── README*.md                      # Cette documentation (ZH/EN/JA/FR)
```

### 3.1 Scripts outils (`tools_*.py` — diagnostics et utilitaires autonomes)

| Script                   | Rôle                                                                                                                                                                                                                                                                                                                 |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `tools_download_sso.py`  | Téléchargement du paquet complet : miroir gh-proxy + reprise Range + validation zip. Il se bloque en pratique à 348 Mo ; conservé comme solution de repli                                                                                                                                                            |
| `tools_probe_mirrors.py` | Mesure en parallèle 6 accélérateurs GitHub (ghfast / gh-proxy / moeyy / gitmirror / kgithub / ghproxy.net) et affiche les kB/s                                                                                                                                                                                       |
| `tools_fetch_subset.py`  | Récupère les SFZ d'une liste blanche → résout récursivement les `#include` → collecte les chemins `sample=` → télécharge les échantillons avec 16 threads ; conserve l'arborescence du dépôt pour que sfizz résolve les chemins relatifs                                                                             |
| `tools_fetch_samples.py` | **La solution retenue** : importe `epic_engine.INST` pour ne télécharger que les échantillons réellement utilisés ; rotation de plusieurs CDN jsDelivr + réutilisation d'une Session `requests` + reprise Range + priorité à trois niveaux (percussions → cuivres → cordes → vents → chœur) + 3 passes de rattrapage |
| `tools_move_samples.py`  | Corrige les échantillons placés par erreur dans les sous-dossiers d'instruments (les `sample=../Samples/...` de SSO se résolvent par rapport au dossier SFZ principal)                                                                                                                                               |
| `tools_status.py`        | Charge chaque SFZ de `epic_engine.INST`, indique le succès et la plage de notes jouables (confirme que le sous-ensemble suffit)                                                                                                                                                                                      |
| `probe_sso.py`           | Audition minimale : accord parfait majeur de do (trompette/cor/trombone/tuba) + timbales + grosse caisse/caisse claire + trémolo de cordes + chœur → `probe.wav`                                                                                                                                                     |
| `tools_check_probe.py`   | Analyse le RMS par segment, la crête et le barycentre spectral de `probe.wav`, prouvant qu'il s'agit d'échantillons et non de sinusoïdes                                                                                                                                                                             |
| `tools_selftest.py`      | Exécute toute la chaîne avec un échantillonneur factice (bruit à la place de SSO) : orchestration → stems → DSP → mastering → MIDI → rapport en 47 s, validant les chemins de code et la mémoire                                                                                                                     |
| `tools_diagnose.py`      | Crête/RMS des stems, courbe RMS des 8 sections, répartition des bandes sur le morceau entier                                                                                                                                                                                                                         |
| `tools_bands.py`         | Part d'énergie par bande pour chaque stem et le mix final (localise « le haut du spectre manquant »)                                                                                                                                                                                                                 |
| `tools_check_midi.py`    | Analyse l'en-tête MIDI, le nombre de pistes, le TPQ, les note-on par canal et la durée du dernier tick                                                                                                                                                                                                               |
| `tools_ffmpeg_verify.py` | Contre-vérifie LUFS / True Peak / LRA avec `ffmpeg loudnorm` et ajoute le résultat à `loudness_report.txt`                                                                                                                                                                                                           |
| `tools_sample_bands.py`  | Analyse directement le spectre des échantillons SSO bruts (bibliothèque ou chaîne de rendu ; chemin codé en dur `D:/_sso`)                                                                                                                                                                                           |
| `tools_hf_test.py`       | Comparaison spectrale étape par étape : échantillon brut / HP+EQ / compression / chaîne de mastering, pour localiser la perte de hautes fréquences                                                                                                                                                                   |
| `tools_package.py`       | Copie le mix final, le rapport, le spectrogramme et les stems d'une version donnée (v5 par défaut) à la racine du dépôt et lance les vérifications finales                                                                                                                                                           |

---

## 4. Conception musicale (règles strictes encodées dans le code)

### 4.1 Structure : 8 sections × 30 s (96 temps @ 192 BPM)

| # | Section | Temps     | Orchestration et fonction                                                                                                                                                                |
|---|---------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0 | Intro   | 0:00–0:30 | Trémolo de cordes + nappe de violoncelles graves + sub bass + grosse caisse façon battement de cœur + timbales lointaines + harpe + avant-goût du thème à la flûte + roulement ascendant |
| 1 | A1      | 0:30–1:00 | **Mélodie principale au cor solo** (première exposition) + cordes chaleureuses + nappe de cuivres graves + battement de timbales + caisse claire légère                                  |
| 2 | B       | 1:00–1:30 | **Mélodie principale à la flûte** (doublée discrètement par le hautbois) + les cuivres se retirent en nappes harmoniques ; seule section « respiration »                                 |
| 3 | A2      | 1:30–2:00 | **La trompette reprend la mélodie** + contre-chant du cor + ostinato de croches aux cuivres graves + caisse claire plus dense                                                            |
| 4 | C1      | 2:00–2:30 | **Trompettes à l'unisson** + ostinato de cordes + trémolo + percussions complètes ; à partir de la mesure 20, modulation vers **D♭ (napolitain ♭II)**                                    |
| 5 | C2      | 2:30–3:00 | **Tous les cuivres à l'octave + chœur + vents aigus + kick électronique** ; ostinato en triolets ; fin V→Cm                                                                              |
| 6 | Outro1  | 3:00–3:30 | Le cor revient au thème (marée descendante), les couches se retirent, l'harmonie des cuivres se referme                                                                                  |
| 7 | Outro2  | 3:30–4:00 | Échos de violon solo/flûte, crescendo en deux temps sur V (G) → **frappe finale en do majeur (tierce de Picardie)** + 3,5 s de décroissance naturelle                                    |

Le même thème est exposé quatre fois avec une échelle de force et un groupement de cuivres croissants : cor →
trompette → cuivres à l'unisson → tous les cuivres + chœur.

### 4.2 Mélodie et harmonie

- La mélodie est stockée sous forme de tableaux en notation chiffrée : `PICKUP` (anacrouse de 2 temps) + `MAIN` (corps
  de 77 temps). Les règles de notation sont documentées en tête
  de `first/我脑海里的一段旋律_python_20261107_65b3ca.py` (`-` prolonge, `【】` divise les durées par deux, `{}` indique
  le legato, `————>` est une fin en fondu).
- Do mineur harmonique ; progression centrale `Cm – A♭ – Fm – G` (change toutes les 2 mesures, 12 cycles) ; `D♭` est
  inséré à la fin de C1 et Outro2 conclut `G → C`.
- La mélodie est placée dans le registre le plus brillant des cuivres (trompette F4–C5), de sorte que réorchestrer la
  même ligne la fait naturellement paraître « plus grande ».

---

## 5. Architecture du moteur

```
Échantillons SSO (pysfizz / SFZ)
        │  Sampler.note(inst, pitch, vel, on_dur, tail)  → rendu d'une note avec cache disque
        ▼
Orchestrator (8 méthodes sec_*) ──► Mixer (6 bus + 2 sends de réverbération + clé de sidechain kick)
        │                          événements MIDI enregistrés en synchronisation
        ▼
process_buses (DSP par stem) ──► mix_down (somme + courbe de wet réverbération) ──► premaster.wav
        │
        ▼
master_chain : ① HP 20 Hz ② léger creux 2–4 kHz ③ shelf 6 kHz ④ compression de colle GR≤3
              ⑤ saturation tanh THD 1–2% ⑥ alignement de loudness + itérations de limitation True Peak ⑦ fondu de 3,5 s
        │
        ▼
epic_final.wav + epic_final.mid + spectrogram_final.png + loudness_report.txt
```

- **Tous les paramètres musicaux vivent dans le dictionnaire `PROFILE`** : choix des instruments, vélocités, textures,
  densité des percussions, niveaux de bus, réverbération, cibles de mastering. Les scripts v1–v5 ne changent
  que `PROFILE`, jamais le moteur.
- **6 bus** : `lead` (cuivres mélodie/flûte/violon), `brass` (harmonie des cuivres), `low` (cuivres graves + sub +
  cordes graves), `strings`, `perc`, `choir`.
- **Couche hybride** : `synth_harp` / `synth_bass_inst` / `synth_choir` / `synth_bass_drum` sont des timbres de
  synthétiseur hérités du script original, superposés aux échantillons pour l'impact du kick électronique et l'épaisseur
  du chœur.
- **Cache d'échantillons** : `Sampler` met en cache avec la clé `inst|pitch|vel|on_dur|tail` dans `cache/*.npz`, donc
  les notes répétées ne sont jamais rendues deux fois.

### 5.1 Traitement par bus (valeurs réglées par la mesure)

| Bus              | Traitement                                                                                                                                                                                                                 |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `brass` / `lead` | HP 80 Hz (18 dB/oct) → 200–400 Hz −1,5 dB (suppression de la « boîte ») → 2–5 kHz +2,5 dB (présence) → shelf 5 kHz +3,5 dB (air) → excitateur harmonique optionnel → compression de colle 2:1 / 30 ms / 250 ms (GR 1–2 dB) |
| `low`            | **Pas de HP**, conservation 40–100 Hz → ducking sidechain du kick (−18 dB / 3:1 / 5 ms / 120 ms, profondeur 5–6,5 dB) → compression 2:1                                                                                    |
| `strings`        | HP 80 Hz → 150–350 Hz −2 dB → shelf 4 kHz +1,5 dB → excitateur (4 dB sous les cuivres) → compression 1,5:1                                                                                                                 |
| `perc`           | Creux dynamique 300–500 Hz −2 dB (évite les bas médiums des cuivres) → HP 28 Hz → 3–6 kHz +2 dB                                                                                                                            |
| `choir`          | HP 60 Hz → 300–600 Hz −1,5 dB → shelf 4 kHz +1 dB                                                                                                                                                                          |
| `reverb`         | IR long pour cuivres/cordes/chœur (2,8–3,3 s), IR court pour percussions (1,2–1,6 s) ; le wet de C2 est **25–28 % plus bas** que celui de A1 (le climax doit rester « sec » pour conserver l'impact)                       |

### 5.2 Chaîne de mastering

HP 20 Hz (24 dB/oct) → 2–4 kHz −0,8 dB → shelf 6 kHz +1,5 dB → compression de colle 1,8:1 / 35 ms / 250 ms / GR ≤ 3 dB →
légère saturation `tanh` (THD 1–2 %) → alignement de loudness + limitation True Peak (mesure par blocs 4×
suréchantillonnés, ≤ 3 itérations) → fondu naturel de 3,5 s.

---

## 6. Évolution des versions (pourquoi 5 orchestrateurs)

| Version | Objectif                                   | Changements clés                                                                                                                        | Résultat objectif                                                                                             |
|---------|--------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| v1      | Faire tourner le squelette en quatre actes | Échantillons SSO + couches hybrides du script original ; table d'orchestration en 8 sections ; élévation D♭ ; finale de Picardie        | Durée/LUFS/TP conformes, mais spectre sombre et mélodie noyée par les cordes (lead −43,6 vs strings −35,2 dB) |
| v2      | Spectre et équilibre                       | EQ presence/air, bus lead +7,6 dB, strings −2,5 dB, perc +5,1 dB, cordes HP 80 Hz                                                       | Part 120–300 Hz 41,9 %→27,2 %, la mélodie émerge                                                              |
| v3      | Brillance et texture                       | Excitateur harmonique ; contre-chant de cor en A2 ; ostinato de triolets en C2 ; caisse claire en doubles croches en C1 ; densité +15 % | 5–10 kHz 0,03 %→0,09 %, mélodie −33,7 dB                                                                      |
| v4      | Contraste dynamique et mastering           | intro 0,78, climax 1,15, −14,5 LUFS, réverbération 3,3 s                                                                                | Contraste Intro→C2 de 13,3 dB, THD 1,96 %                                                                     |
| **v5**  | Finition finale                            | Échelle de vélocité corrigée, excitateur −17 dB, climax 1,2, TP mesuré par blocs 4× suréchantillonnés                                   | Contraste **14,3 dB**, TP **−1,02 dBTP**, cohérent avec ffmpeg                                                |

---

## 7. Validation objective (v5)

| Élément                    | Résultat                                                                             |
|----------------------------|--------------------------------------------------------------------------------------|
| Durée                      | 240,00 s (PASS, 240 ± 2)                                                             |
| Loudness intégrée          | −15,35 LUFS (PASS, −16…−14)                                                          |
| True Peak                  | −1,02 dBTP (PASS, ≤ −1,0)                                                            |
| Loudness Range             | 15,0 LU (dynamique de niveau cinéma/classique, pas 3–6 LU écrasés)                   |
| Énergie 50–100 Hz          | −48,3 dB (cuivres graves/timbales actifs)                                            |
| Énergie 2–5 kHz            | −69,7 dB (les cuivres ont du mordant)                                                |
| Stems                      | Les 6 sont non vides                                                                 |
| MIDI                       | Format 1, 6 pistes, 480 TPQ, 239,93 s ; note-on ch0–ch4 = 664 / 737 / 883 / 588 / 60 |
| Contre-vérification ffmpeg | −15,36 LUFS / −1,02 dBTP / LRA 15,00 (cohérent avec `pyloudnorm`)                    |

RMS par section (avant mastering, dBFS) :

| Intro | A1    | B     | A2    | C1    | C2        | Outro1 | Outro2 |
|-------|-------|-------|-------|-------|-----------|--------|--------|
| −36,6 | −29,8 | −34,3 | −28,3 | −24,6 | **−22,3** | −30,6  | −31,6  |

L'écart Intro → C2 est de 14,3 dB, et la section B (−34,3) est sous A1 (−29,8), produisant l'arc « établir – respirer –
monter – exploser – retomber ».

---

## 8. Contraintes connues (mesurées, non théoriques)

1. **`pysfizz` n'accepte que des chemins ASCII** : le dossier du projet contient des caractères chinois, la
   jonction `D:\_sso` est donc indispensable — voir §2.2.
2. **Réseau** : les connexions directes à `raw.githubusercontent.com` sont réinitialisées (WinError 10054) ; le paquet
   complet via `codeload` se bloque à 348 Mo ; `gh-proxy` ne fournit que 20–60 kB/s par connexion. La solution finale
   utilise les CDN jsDelivr `gcore` / `testingcf` avec 1–2 connexions chacun, mesurés à ~160 kB/s par connexion.
3. **Les échantillons SSO sont naturellement sombres dans le haut du spectre** : `trumpets-sus-a#4.wav` n'a que 0,2 %
   d'énergie entre 5 et 10 kHz, et `horns-stc` / `celli-stc` 0 %. Un simple boost EQ ne ferait que monter le bruit, d'où
   l'excitateur harmonique (non-linéarité du second ordre dans 1,2–5 kHz → HP 5 kHz → ajout à −17 dB de niveau relatif).
4. **Portée pédagogique/démonstration** : SSO est une bibliothèque gratuite de 2011 (CC Sampling Plus 1.0). Même avec
   l'excitateur, la brillance n'atteint pas celle d'un enregistrement hollywoodien réel ; une bibliothèque commerciale (
   Cinesamples / série Berlin, etc.) serait nécessaire pour une sortie en salle.
5. **Le nom du dossier d'archive contient des caractères chinois et des parenthèses** : les scripts écrivent
   dans `renders/vN`, différent de l'archive `renders（就是喇叭从弱到强）`, donc un nouveau rendu crée un nouveau dossier
   sans écraser l'ancien.

---

## 9. Licence et crédits

- Échantillons : **Sonatina Symphonic Orchestra** (CC Sampling Plus 1.0, v4.0, par Mattias Westlund,
  GitHub : `peastman/sso`).
- Rendu : **sfizz / pysfizz**.
- Mélodie, orchestration, DSP, mastering et tout le code : l'auteur de ce projet.
- Base de recherche et sources des paramètres : voir [RESEARCH_NOTES.md](RESEARCH_NOTES.md) (30 règles strictes de la
  musique épique, références EQ/compression/loudness et auto-évaluation).
