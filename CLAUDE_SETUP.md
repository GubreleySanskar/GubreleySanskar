# Instructions for Claude: build this GitHub profile for a new person

You are setting up an animated GitHub profile README for the person you are talking to,
using the template in this repository (github.com/GubreleySanskar/GubreleySanskar).
Follow these steps in order. Keep messages to the person short and friendly; they may be a
beginner. Do not rebuild the design by hand: always use `scripts/build.py`.

## 1. Collect what you need (one message, then wait)

Ask for everything below in a single message, as a short checklist. Mark which are optional.

1. **Photo**, attached to the chat. Best: face clearly visible, good light, plain or simple background.
2. **GitHub username** (exactly as on github.com).
3. **Full name** to display.
4. **Tagline**, one short line, e.g. "CS Student · Web Developer".
5. **Current role and where**, e.g. "Final-year CS student" + "@ IIT Delhi", or "Software Engineer" + "@ Acme".
6. **What you build or create**, one line.
7. **Tech stack**, up to 8 items.
8. **Three highlights**, one short line each.
9. *Optional* links: email, Instagram, LinkedIn, X, YouTube, website (handles or URLs).
10. **Contribution number** to show on the graph for the year (any number, e.g. 800).
    Tell them plainly: the graph is a static, decorative image with this number, not their live GitHub data.

If they skip something required, ask once for just that item. If they say "you decide",
write sensible text from what they gave you.

## 2. Check their profile repository exists and Claude can write to it

The repository must be named exactly like the username: `USERNAME/USERNAME`, public.

- Request push access to `USERNAME/USERNAME` (in Claude's cloud session use the add-repo tool with push access).
- If the repo does not exist, stop and tell them:
  "On GitHub click **+ → New repository**, name it exactly `USERNAME`, set **Public**, tick
  **Add a README file**, click **Create repository**, then tell me 'done'."
- If access is refused, tell them:
  "Open https://github.com/apps/claude/installations/select_target, choose your account,
  select **Only select repositories → USERNAME**, click **Install** (or **Save**), then tell me 'done'."

## 3. Build

```bash
git clone --depth 1 https://github.com/GubreleySanskar/GubreleySanskar /tmp/profile-template
git clone https://github.com/USERNAME/USERNAME /tmp/their-profile      # use the clone command your tools give you
pip install -r /tmp/profile-template/scripts/requirements.txt          # add --break-system-packages if pip asks
```

Write `/tmp/their-profile/profile.json` in the same shape as this repo's `profile.json`:
- `handle`: their first name in lowercase (used in the `name@github` prompts)
- `heatmap`: `{"total": <their number>, "seed": 29, "end_date": ""}` (blank date = today)
- `portrait`: `{"crop": ""}` (leave blank; the script trims empty background itself)
- empty strings for links they did not give
- remove the `_help` key

Then build into their repo:

```bash
python /tmp/profile-template/scripts/build.py \
  --photo "<path of the attached photo>" \
  --config /tmp/their-profile/profile.json \
  --out /tmp/their-profile
cp -r /tmp/profile-template/scripts /tmp/their-profile/   # so they can rebuild later
```

The first run downloads a background-removal model (about 180 MB); that is expected.
**Never copy their photo into the repository.**

## 4. Check before publishing

- If a headless browser is available, render `assets/ascii-portrait.svg`, `assets/info-card.svg` and
  `assets/contrib-heatmap.svg` on a dark background after ~8 seconds and look at them. If the portrait is too dark or too
  faint, rebuild with `GAMMA=1.1` (darker) or `GAMMA=1.5` (lighter) set in the environment.
- Show the person a screenshot if you made one, and ask if they want any text changed.

## 5. Publish

```bash
cd /tmp/their-profile
git add -A
git commit -m "Animated profile README"
git push origin HEAD
```

The push starts the snake workflow (`.github/workflows/snake.yml`); it creates an `output`
branch with the snake images in about a minute. If you can, confirm the run succeeded.

If the push is refused or there is no way to push from this session: zip `/tmp/their-profile`
(without `.git`), send it, and tell them to upload `README.md`, `profile.json` and the `assets`, `data`
and `scripts` folders with **Add file → Upload files**, then create `.github/workflows/snake.yml`
with **Add file → Create new file** and paste its contents. Then **Actions → Generate snake animation → Run workflow**.

## 6. Finish

Tell them:
- their profile is live at `https://github.com/USERNAME`
- GitHub caches images: hard-refresh after a minute if they see the old version
- if the workflow fails with a permission error: **Settings → Actions → General → Workflow permissions →
  Read and write permissions → Save**, then run it again
- to change text later, edit `profile.json` and ask Claude to run `scripts/build.py` again
