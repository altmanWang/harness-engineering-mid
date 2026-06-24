---
name: minimax-music-gen
description: >
  Use when user wants to generate music, songs, or audio tracks. Triggers on any request
  involving music creation, song writing, lyrics generation, audio production, or covers.
  Also triggers when user provides lyrics and wants them turned into a song, or describes
  a mood/scene and wants background music. Supports multilingual triggers — match equivalent
  phrases in any language. Does NOT auto-play audio; generates MP3 + TXT lyrics document.
  Do NOT use for music playback of existing files, music theory questions, or music
  recommendation without generation.
license: MIT
metadata:
  version: "1.2"
  category: creative
---

# MiniMax Music Generation Skill

Generate songs (vocal or instrumental) using the MiniMax Music API. Supports two creation
modes: **Basic** (one-sentence-in, song-out) and **Advanced Control** (edit lyrics, refine
prompt, plan before generating).

## Prerequisites

- **mmx CLI** (required): Music generation uses the `mmx` command-line tool.

  **Check if installed:**
  ```bash
  command -v mmx && mmx --version || echo "mmx not found"
  ```

  **Install (requires Node.js):**
  ```bash
  npm install -g mmx-cli
  ```

  **Authenticate (first time only):**
  ```bash
  mmx auth login --api-key <your-minimax-api-key>
  ```
  The API key can be obtained from [MiniMax Platform](https://platform.minimaxi.com/).
  Credentials are saved to `~/.mmx/credentials.json` and persist across sessions.

  **Verify:**
  ```bash
  mmx quota show
  ```

- No audio player required — music is saved to file without auto-playback

## CLI Tool

This skill uses the `mmx` CLI for all music generation:

- **Music Generation**: `mmx music generate` — model: `music-2.6-free`
  - Supports `--lyrics-optimizer` to auto-generate lyrics from prompt
  - Supports `--instrumental` for instrumental tracks
  - Supports `--lyrics` for user-provided lyrics
  - Structured params: `--genre`, `--mood`, `--vocals`, `--instruments`, `--bpm`, `--key`, `--tempo`, `--structure`, `--references`
  
- **Cover**: `mmx music cover` — model: `music-cover-free`
  - Takes reference audio via `--audio-file <path>` or `--audio <url>`
  - `--prompt` describes the target cover style

**Agent flags**: Always add `--quiet --non-interactive` when calling mmx from agents.

**Pipeline**:
- Vocal: `User description -> mmx music generate --lyrics-optimizer -> MP3`
- Instrumental: `User description -> mmx music generate --instrumental -> MP3`
- Cover: `Source audio + style -> mmx music cover -> MP3`

## Storage

All generated music is saved to `~/Music/minimax-gen/`. Create the directory if it doesn't
exist. Files are named with a timestamp and a short slug derived from the prompt:
`YYYYMMDD_HHMMSS_<slug>.mp3`

---

## Language & Interaction

Detect the user's language from their first message and respond in that language for the
entire session. This applies to all interaction text, questions, confirmations, and feedback
prompts.

**User-facing text localization rule**:
- ALL text shown to the user — including preview labels, field names, confirmations, status
  messages, playback info, feedback prompts, **and the prompt/description preview** — MUST
  be fully translated into the user's language.
- The **API prompt** sent to the model should always be written in English for best
  generation quality. However, when previewing the prompt to the user, show a localized
  description in the user's language instead of the raw English prompt. The English prompt
  is an internal implementation detail — the user does not need to see it.
- The templates below are written in English as reference. At runtime, translate every label
  and message into the user's detected language.

**Lyrics language rule**:
- Default lyrics language = the user's language. A Chinese-speaking user gets Chinese lyrics;
  an English-speaking user gets English lyrics.
- Only generate lyrics in a different language if the user **explicitly** requests it.
- When a different lyrics language is needed, embed it naturally into the vocal or genre
  description in the prompt. For example, instead of appending "with Korean lyrics", use
  "featuring a Korean female vocalist" or specify a genre that implies the language (e.g.,
  "K-pop", "J-rock", "Mandopop", "Latin pop").

---

## Workflow

### Step 0: Detect Intent

Parse the user's message to determine:

1. **Song category**: vocal (with lyrics), instrumental (no vocals), or cover
2. **Creation mode preference**: did they provide detailed requirements (Advanced) or a
   casual one-liner (Basic)?

If ambiguous, ask using this decision tree:

```
Q1: What type of music?
  - Vocal (with lyrics)
  - Instrumental (no vocals)
  - Cover

Q2: Creation mode?
  - Basic — one-line description, auto-generate
  - Advanced — edit lyrics, refine prompt, plan
```

If the user gives a clear one-liner like "make me a sad piano piece", skip the questions —
infer instrumental + basic mode and proceed.

---

### Step 1: Basic Mode

**Goal**: User provides a short description, the skill auto-generates everything, then calls
the API.

1. **Expand the description into a prompt**: Take the user's one-liner and expand it into a
   rich music prompt. Refer to the **Prompt Writing Guide** appendix at the end of this
   document for style vocabulary, genre/instrument references, and prompt structure.
   **The API prompt should always be written in English** for best generation quality,
   regardless of the user's language.
   
   Follow this pattern:
   ```
   A [mood] [BPM optional] [genre] song, featuring [vocal description],
   about [narrative/theme], [atmosphere], [key instruments and production].
   ```

2. **Show the user a preview** before generating. Translate all labels AND the prompt
   description into the user's language. The English prompt is only used internally when
   calling the API — the user should never see it. Example template (English reference —
   localize everything at runtime):

   ```
   About to generate:
   Type: Vocal / Instrumental
   Description: indie folk, melancholy, acoustic guitar, gentle female voice
   Lyrics: Auto-generated (--lyrics-optimizer)
   
   Confirm? (press enter to confirm, or tell me what to change)
   ```

3. **Call mmx**: Generate the music directly.

---

### Step 2: Advanced Control Mode

**Goal**: User has full control over every parameter before generation.

1. **Lyrics phase**:
   - If user provided lyrics: display them formatted with section markers, ask for edits.
     The final lyrics will be passed via `--lyrics` to mmx.
   - If user has a theme but no lyrics: will use `--lyrics-optimizer` to auto-generate.
   - Support iterative editing: "change the second chorus" -> only rewrite that section.
   - User can also write lyrics themselves and pass via `--lyrics`.

2. **Prompt phase**:
   - Generate a recommended prompt based on the lyrics' mood and content.
   - Present it as editable tags the user can add/remove/modify.
   - Refer to the **Prompt Writing Guide** appendix for the full vocabulary.

3. **Advanced planning** (optional, offer but don't force):
   - Song structure: verse-chorus-verse-chorus-bridge-chorus or custom
   - BPM suggestion (encode in prompt as tempo descriptor)
   - Reference style: "something like X style" -> map to prompt tags
   - Vocal character description

4. **Final confirmation**: Show complete parameter summary, then generate.

---

### Step 3: Call mmx

Generate music using the mmx CLI:

**Vocal with auto-generated lyrics:**
```bash
mmx music generate \
  --prompt "<prompt>" \
  --lyrics-optimizer \
  --genre "<genre>" --mood "<mood>" --vocals "<vocal style>" \
  --instruments "<instruments>" --bpm <bpm> \
  --out ~/Music/minimax-gen/<filename>.mp3 \
  --quiet --non-interactive
```

**Vocal with user-provided lyrics:**
```bash
mmx music generate \
  --prompt "<prompt>" \
  --lyrics "<lyrics with section markers>" \
  --genre "<genre>" --mood "<mood>" --vocals "<vocal style>" \
  --out ~/Music/minimax-gen/<filename>.mp3 \
  --quiet --non-interactive
```

**Instrumental (no vocal):**
```bash
mmx music generate \
  --prompt "<prompt>" \
  --instrumental \
  --genre "<genre>" --mood "<mood>" --instruments "<instruments>" \
  --out ~/Music/minimax-gen/<filename>.mp3 \
  --quiet --non-interactive
```

Use structured flags (`--genre`, `--mood`, `--vocals`, `--instruments`, `--bpm`, `--key`,
`--tempo`, `--structure`, `--references`, `--avoid`, `--use-case`) to give the API
fine-grained control instead of cramming everything into `--prompt`.

Display a progress indicator while waiting. Typical generation takes 30-120 seconds.

---

### Step 4: Output & Lyrics Document

After successful generation, **do NOT play the audio automatically**. Instead:

1. **Create a lyrics document** (`.txt` file) with the same base name as the MP3, saved in
   the same directory: `~/Music/minimax-gen/<filename>.txt`

2. **The lyrics document should contain 4 sections:**

   ```
   歌曲名：<song_name>
   MP3路径：~/Music/minimax-gen/<filename>.mp3

   ==================== 歌词 ====================

   <full_lyrics_without_section_markers>

   ==================== 歌曲参数 ====================

   曲风：<genre>
   BPM：<bpm>
   情绪：<mood>
   人声：<vocal_description>
   乐器：<instruments>
   生成时间：<timestamp>

   ==================== 原始创作故事 ====================

   <user's original story or prompt>
   ```

   - Section 1: Song name and MP3 file path (first line)
   - Section 2: Full lyrics **without** `[verse]`, `[chorus]`, `[bridge]`, etc. markers
   - Section 3: Song parameters (genre, BPM, mood, vocals, instruments, generation time)
   - Section 4: User's original story/prompt that inspired the song

3. **Tell the user the output paths** (localize all text):

   ```
   ✅ 歌曲生成成功！

   🎵 音频文件：~/Music/minimax-gen/<filename>.mp3
   📄 歌词文档：~/Music/minimax-gen/<filename>.txt
   ```

---

### Step 5: Feedback & Iteration

After showing the output paths, ask for feedback (localize all text):

```
这首歌怎么样？
  1. 太棒了，就它了！
  2. 还差点感觉，调整一下重新生成
  3. 微调歌词/风格后重新生成
  4. 不想要了，重新开始
```

Based on feedback:
- **Satisfied**: Done. Mention the file paths again.
- **Adjust & regenerate**: Ask what to change (prompt? lyrics? style?), apply edits,
  re-run generation. Keep both old files (`.mp3` and `.txt`) with a `_v1` suffix.
- **Fine-tune**: Enter Advanced Control Mode with the current parameters pre-filled.
- **Delete & restart**: Remove both files, go back to Step 0.

---

## Cover Mode

Generate a cover version of a song based on reference audio. Model: `music-cover-free`.

**Reference audio requirements**: mp3, wav, flac — duration 6s to 6min, max 50MB.
If no lyrics are provided, the original lyrics are extracted via ASR automatically.

### Workflow

When the user selects Cover mode:
1. Ask for the source audio — a local file path or URL
2. Ask for the target cover style (e.g., "acoustic cover, stripped-down, intimate vocal")
3. Optionally ask for custom lyrics or lyrics file

### Commands

**Cover from local file:**
```bash
mmx music cover \
  --prompt "<cover style description>" \
  --audio-file <source.mp3> \
  --out ~/Music/minimax-gen/<filename>.mp3 \
  --quiet --non-interactive
```

**Cover from URL:**
```bash
mmx music cover \
  --prompt "<cover style description>" \
  --audio <source_url> \
  --out ~/Music/minimax-gen/<filename>.mp3 \
  --quiet --non-interactive
```

**With custom lyrics (text):**
```bash
mmx music cover \
  --prompt "<style>" \
  --audio-file <source.mp3> \
  --lyrics "<custom lyrics>" \
  --out ~/Music/minimax-gen/<filename>.mp3 \
  --quiet --non-interactive
```

**With custom lyrics (file):**
```bash
mmx music cover \
  --prompt "<style>" \
  --audio-file <source.mp3> \
  --lyrics-file <lyrics.txt> \
  --out ~/Music/minimax-gen/<filename>.mp3 \
  --quiet --non-interactive
```

### Optional flags

| Flag | Description |
|------|-------------|
| `--seed <number>` | Random seed 0-1000000 for reproducible results |
| `--channel <n>` | `1` (mono) or `2` (stereo, default) |
| `--format <fmt>` | `mp3` (default), `wav`, `pcm` |
| `--sample-rate <hz>` | Sample rate (default: 44100) |
| `--bitrate <bps>` | Bitrate (default: 256000) |

### After generation

1. **Create a cover document** (`.txt` file) with the same base name as the MP3:
   `~/Music/minimax-gen/<filename>.txt`

2. **The cover document should contain:**
   - Song name and MP3 file path
   - Cover style description
   - Source audio reference (file path or URL)
   - Custom lyrics (if provided)
   - Generation timestamp

3. **Tell the user the output paths** (localize all text):

```
✅ 翻唱生成成功！

🎵 音频文件：~/Music/minimax-gen/<filename>.mp3
📄 文档：~/Music/minimax-gen/<filename>.txt
```

Then proceed with the normal feedback flow (Step 5).

---

## Error Handling

| Error | Action |
|-------|--------|
| mmx not found | `npm install -g mmx-cli` |
| mmx auth error (exit code 3) | `mmx auth login` |
| Quota exceeded (exit code 4) | Report quota limit, suggest waiting or upgrading |
| API timeout (exit code 5) | Retry once, then report failure |
| Content filter (exit code 10) | Adjust prompt to avoid filtered content |
| Invalid lyrics format | Auto-fix section markers, warn user |
| Lyrics document creation failed | Report error, retry creating the document |
| Network error | Show error detail, suggest checking connection |

---

## Important Notes

- **Never reproduce copyrighted lyrics.** When doing covers, always write original lyrics
  inspired by the song's theme. Explain this to the user.
- **Prompt language**: The API prompt works best with English tags. Chinese tags are also
  acceptable. Mixing is OK.
- **Section markers in lyrics**: The API recognizes `[verse]`, `[chorus]`, `[bridge]`,
  `[outro]`, `[intro]`. Always include them when providing `--lyrics`.
- **File management**: If `~/Music/minimax-gen/` has more than 50 files, suggest cleanup
  when starting a new session.
- **Structured params**: Prefer using `--genre`, `--mood`, `--vocals`, `--instruments`,
  `--bpm` etc. over embedding everything in `--prompt`. This gives the API better control.
- **Lyrics language via style**: When the user wants lyrics in a specific language, express
  it through the vocal description or genre (e.g., "Japanese female vocalist", "Mandopop
  ballad") rather than appending a language directive to the prompt.

---

## Appendix: Prompt Writing Guide

See [references/prompt_guide.md](references/prompt_guide.md) for the complete prompt writing guide,
including genre/vocal/instrument references and BPM tables.