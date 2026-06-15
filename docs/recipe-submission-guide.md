# How to submit a recipe in 5 minutes

This guide is for Microsoft employees who want to share a recipe in the HLS
Cookbook. You do not need to clone the repo or write code. Write naturally; the
agent turns your issue into recipe YAML and opens a pull request for review.

For the technical shape behind the form, see the [recipe schema](architecture.md#recipe-schema).

## Step 1 — Open the issue form

Open the [Submit a recipe issue form](https://github.com/samueltauil/hls-cookbook/issues/new?template=recipe.yml).
If GitHub asks, sign in with your Microsoft account that has access to the repo.

## Step 2 — Fill out the sections

### Recipe identity

- **Recipe name** (required) — the title printed in the cookbook, like
  `Chicken Adobo` or `Pão de Queijo`.
- **GitHub handle** (required) — your GitHub username, without worrying about the
  `@`.
- **Contributor display name** — the name you want shown in the book.
- **Summary** — 1-3 sentences shown above the recipe in the book. Mention what
  makes the dish special, when you cook it, or how it tastes.
- **Source / credit** + **Source URL** — use these for adapted or inspired-by
  recipes. Family recipes can say something like `Adapted from Lola Maria's
  adobo`; web recipes should include the original URL when possible.

### Classification

- **Cuisine** (required), **Course** (required), **Difficulty** (required) — pick
  the closest option. Maintainers can polish wording later.
- **Dietary tags** — comma-separated tags such as `dairy-free, gluten-free`.
- **Allergens** — checkboxes for the major eight: gluten, dairy, eggs, nuts, soy,
  shellfish, sesame, and fish.
- **Occasion** — choose any that fit, such as weeknight, holiday, batch-cook,
  party, brunch, picnic, kids-friendly, or date-night.
- **Keywords / tags** — extra search tags, comma-separated, like `one-pot,
  comfort food, freezer-friendly`.

### Yield & time

- **Yield servings** (required) — the number of servings the recipe makes.
- **Yield notes** — helpful context, like `Halve for snack portions` or `Doubles
  cleanly for a party`.
- **Prep minutes**, **Cook minutes**, **Rest / marinade minutes** — estimates are
  fine. Rest time includes marinating, chilling, proofing, or cooling.

### Ingredients & steps

- **Ingredients** — one ingredient per line, written the way a cook would write
  it. Use `## Section` headings to group ingredients, such as `## Marinade`,
  `## Sauce`, or `## Garnish`.

  ```text
  ## Marinade
  2 lb chicken thighs, bone-in, skin-on
  1/4 cup soy sauce, low-sodium preferred

  ## Braise
  6 cloves garlic, smashed
  2 bay leaves
  ```

  The agent keeps your original text, normalizes metric and US-friendly
  quantities, and extracts trailing comma notes. For example,
  `2 lb chicken thighs, bone-in` becomes name=`chicken thighs` and
  notes=`bone-in`.

- **Steps** — one step per paragraph. Numbering is optional because the agent
  renumbers steps in order.

  ```text
  1. Marinate the chicken for 30 minutes.

  2. Brown the chicken, then simmer with the marinade until tender.
  ```

### Extras

- **Equipment** — one item per line or comma-separated, such as `Dutch oven,
  tongs, digital scale`.
- **Notes** — any longer context that does not fit elsewhere.
- **Tips & substitutions** — swaps, brand preferences, doneness cues, or lessons
  learned.
- **Storage & make-ahead** — how long leftovers keep, freezing notes, and reheating
  advice.
- **Pairings & serving suggestions** — sides, drinks, garnishes, or how you like to
  plate it.

### Photos & locale

- **Photos** — paste URLs or drag-and-drop images into the field. The agent
  commits them under `recipes/<slug>/photos/`.
- **Hero photo caption** — caption for the first photo; it appears in the book.
- **Recipe language** — choose `en` (default) or `pt-BR`. Choosing `pt-BR` files
  the recipe at `recipes/<slug>/recipe.pt-BR.yaml`.

### Submitter agreement

- **Submitter agreement** (required) — confirm the recipe is your original work or
  properly credited, and that you agree to release it under this repository's MIT
  license. No PR is created until this is checked.

## Step 3 — Submit and watch the PR

Click **Submit new issue**. The agent reads the issue, normalizes the recipe,
adds any photos, and opens a PR with `recipes/<slug>/recipe.yaml` or
`recipes/<slug>/recipe.<locale>.yaml`. You will be tagged on the PR.

Watch for validation comments or maintainer questions. Maintainers review the
YAML diff, adjust anything that needs a human touch, and merge when the recipe is
ready for a cookbook build.

## FAQ

**Can I submit in Portuguese?**

Yes — choose `pt-BR` from the Recipe language dropdown. See
[`recipes/pao-de-queijo/recipe.pt-BR.yaml`](../recipes/pao-de-queijo/recipe.pt-BR.yaml)
for an example.

**Can I submit a translation of an existing recipe?**

Yes — open a new issue with the same recipe title and choose the other locale.
Both files can coexist under the same `recipes/<slug>/` directory.

**Can I edit later?**

Yes. Open a PR editing the YAML directly, or open an issue describing the change
if you want help.

**What if my ingredient is not in the master?**

Validation warns but does not fail. Maintainers may add it to
[`data/ingredients.yaml`](../data/ingredients.yaml) with aliases, nutrition, and
density data.

**What if I forget the agreement checkbox?**

The agent will comment asking you to update the issue. No PR is created until the
required checkbox is checked.

Happy cooking. 🍳
