---
name: Ingest recipe submission
description: Normalize recipe issue submissions into recipe YAML pull requests.
on:
  issues:
    types: [opened, labeled]
    names: [recipe-submission]
  roles: all
permissions:
  contents: read
engine: copilot
network: defaults
env:
  ISSUE_JSON: ${{ github.workspace }}/.runtime/issue.json
steps:
  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: "3.12"
  - name: Install HLS Cookbook
    run: pip install -e ".[dev]"
  - name: Parse recipe issue form
    id: issue_json
    env:
      ISSUE_BODY: ${{ github.event.issue.body }}
      ISSUE_JSON: ${{ github.workspace }}/.runtime/issue.json
    run: |
      mkdir -p "$(dirname "$ISSUE_JSON")"
      python <<'PY'
      from __future__ import annotations

      import json
      import os
      import re
      from pathlib import Path

      body = os.environ.get("ISSUE_BODY", "")
      output_path = Path(os.environ["ISSUE_JSON"])

      # GitHub renders Issue Form labels as "### Label"; normalize those labels
      # so "&" and "and" variants, extra spaces, and slash spacing all match.
      def normalize_heading(value: str) -> str:
          value = value.strip().lower().replace("&", "and")
          value = re.sub(r"\s*/\s*", " / ", value)
          return re.sub(r"\s+", " ", value)

      heading_to_id = {
          normalize_heading(key): field_id
          for key, field_id in {
              "recipe name": "title",
              "title": "title",
              "summary": "summary",
              "github handle": "contributor_handle",
              "contributor handle": "contributor_handle",
              "contributor display name": "contributor_display_name",
              "source / credit": "source_attribution",
              "source url": "source_url",
              "yield servings": "yield_servings",
              "yield notes": "yield_notes",
              "prep minutes": "prep_min",
              "prep min": "prep_min",
              "cook minutes": "cook_min",
              "cook min": "cook_min",
              "rest / marinade minutes": "rest_min",
              "course": "course",
              "dietary tags": "dietary_tags",
              "allergens": "allergens",
              "occasion": "occasion",
              "keywords / tags": "keywords",
              "difficulty": "difficulty",
              "ingredients": "ingredients",
              "steps": "steps",
              "equipment": "equipment",
              "notes": "notes",
              "tips & substitutions": "tips",
              "storage & make-ahead": "storage",
              "pairings & serving suggestions": "pairings",
              "photos": "photos",
              "hero photo caption": "hero_caption",
              "submitter agreement": "agreement",
          }.items()
      }

      def clean_response(value: str) -> str:
          value = value.strip()
          return "" if value in {"_No response_", "No response"} else value

      # Checkbox fields render as "- [x] label"; selected labels become CSV,
      # except the submitter agreement is stored as a true/false string.
      def selected_checkboxes(value: str) -> list[str]:
          return [
              label.strip()
              for mark, label in re.findall(
                  r"^\s*-\s+\[([ xX])\]\s+(.+?)\s*$", value, flags=re.MULTILINE
              )
              if mark.lower() == "x"
          ]

      matches = list(re.finditer(r"^###\s+(.+?)\s*$", body, flags=re.MULTILINE))
      parsed: dict[str, str] = {}
      for index, match in enumerate(matches):
          field_id = heading_to_id.get(normalize_heading(match.group(1)))
          if not field_id:
              continue
          start = match.end()
          end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
          raw_value = clean_response(body[start:end])
          if field_id == "allergens":
              parsed[field_id] = ", ".join(selected_checkboxes(raw_value))
          elif field_id == "agreement":
              parsed[field_id] = "true" if selected_checkboxes(raw_value) else "false"
          else:
              parsed[field_id] = raw_value

      def value(field_id: str) -> str:
          return parsed.get(field_id, "").strip()

      def unique_urls(items: list[str]) -> list[str]:
          seen: set[str] = set()
          result: list[str] = []
          for item in items:
              url = item.rstrip(".,;)")
              if url and url not in seen:
                  seen.add(url)
                  result.append(url)
          return result

      photo_text = value("photos")
      photo_urls = re.findall(r"!\[[^\]]*\]\((https?://[^\s)]+)", body)
      photo_urls.extend(re.findall(r"https?://[^\s<>)\"]+", photo_text))

      handle = value("contributor_handle").removeprefix("@")
      payload: dict[str, object] = {
          "title": value("title"),
          "summary": value("summary"),
          "contributor": {
              "github_handle": handle,
              "display_name": value("contributor_display_name"),
          },
          "yield_servings": value("yield_servings"),
          "yield_notes": value("yield_notes"),
          "prep_min": value("prep_min"),
          "cook_min": value("cook_min"),
          "rest_min": value("rest_min"),
          "course": value("course"),
          "dietary_tags": value("dietary_tags"),
          "allergens": value("allergens"),
          "occasion": value("occasion"),
          "keywords": value("keywords"),
          "difficulty": value("difficulty"),
          "equipment": value("equipment"),
          "ingredients": value("ingredients"),
          "steps": value("steps"),
          "tips": value("tips"),
          "storage": value("storage"),
          "pairings": value("pairings"),
          "notes": value("notes"),
          "photo_urls": unique_urls(photo_urls),
          "hero_caption": value("hero_caption"),
          "locale": "en",
          "agreement": value("agreement") or "false",
      }
      source = {"attribution": value("source_attribution"), "url": value("source_url")}
      if source["attribution"] or source["url"]:
          payload["source"] = source

      output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
      print(f"Wrote normalized issue payload to {output_path}")
      PY
safe-outputs:
  create-pull-request:
    title-prefix: "[recipe] "
    labels: [recipe-submission, agent-generated]
    draft: false
    allowed-files: ["recipes/**"]
  add-comment:
    max: 2
---

# Ingest recipe submission

Read the normalized issue payload from `$ISSUE_JSON`. The triggering issue is ${{ github.server_url }}/${{ github.repository }}/issues/${{ github.event.issue.number }}.

If the `agreement` payload field is anything other than `true`, use `safe-outputs.add-comment` to post 'Please re-open the issue with the submitter agreement checkbox checked' and stop.

Sanitized issue context, for reference only:

${{ steps.sanitized.outputs.text }}

Recipes are stored as `recipes/<slug>/recipe.yaml` (English only for now). `hls.normalize.write_recipe_yaml` computes the path; do not compute the recipe filename yourself.

Run:

```bash
python -m hls.normalize --issue-json "$ISSUE_JSON"
```

Use the path printed by `hls.normalize` as the recipe YAML path, and use its parent directory as the recipe directory.

For each URL in `photo_urls`, including URLs extracted from Markdown image attachments, try to download it with `curl` into the recipe directory's `photos/` subdirectory. Skip URLs that are unreachable.

Run `python -m hls.validate` on the recipe YAML path printed by `hls.normalize`. If validation fails, use `safe-outputs.add-comment` on the triggering issue with the validation errors and stop.

If validation succeeds, emit `safe-outputs.create-pull-request` with branch `recipe/<slug>`, title `[recipe] <title>`, a body linking the issue and summarizing the added recipe/photos, labels `recipe-submission` and `agent-generated`, and only files under `recipes/**`.
