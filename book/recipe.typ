#let display-font = ("Lato", "Inter", "Liberation Sans")
#let body-font = ("EB Garamond", "Linux Libertine", "Libertinus Serif")

#let metadata-label(label) = {
  text(font: display-font, size: 8.5pt, weight: "bold", fill: rgb("#6b7280"))[#label]
}

#let ingredient-line(item) = {
  block(spacing: 3pt)[
    #if item.quantity != none and item.quantity != [] [
      #text(fill: rgb("#6b7280"))[#item.quantity ]
    ]
    #strong[#item.name]#if item.notes != none and item.notes != [] [, #item.notes]
  ]
}

#let nutrition-block(nutrition-complete, nutrition) = {
  block(
    fill: rgb("#f8fafc"),
    inset: 8pt,
    radius: 3pt,
    width: 100%,
  )[
    #text(font: display-font, size: 9pt, weight: "bold")[Nutrition per serving]
    #v(3pt)
    #if nutrition-complete [
      #grid(
        columns: (1fr, 1fr, 1fr, 1fr),
        gutter: 8pt,
        text(size: 9pt)[Calories: #nutrition.calories],
        text(size: 9pt)[Protein: #nutrition.protein],
        text(size: 9pt)[Fat: #nutrition.fat],
        text(size: 9pt)[Carbs: #nutrition.carbs],
      )
    ] else [
      #text(size: 9pt, style: "italic")[Nutrition data incomplete]
    ]
  ]
}

#let recipe(
  title: [],
  hero-photo: none,
  contributor: [—],
  course: [—],
  dietary-tags: [—],
  prep-time: [—],
  cook-time: [—],
  total-time: [—],
  servings: [—],
  summary: [],
  ingredient-sections: (),
  steps: (),
  nutrition-complete: false,
  nutrition: (:),
) = {
  pagebreak(weak: true)

  grid(
    columns: (1fr, auto),
    gutter: 0.35in,
    align: top,
    [
      #heading(level: 1)[#title]
      #v(8pt)
      #line(length: 1.45in, stroke: 1pt + rgb("#d97706"))
      #v(12pt)
      #text(size: 13pt, style: "italic", fill: rgb("#4b5563"))[#summary]
    ],
    if hero-photo != none {
      image(hero-photo, width: 3in, height: 3in, fit: "cover")
    } else {
      []
    },
  )

  v(14pt)

  table(
    columns: (auto, 1fr, auto, 1fr),
    stroke: none,
    inset: (x: 4pt, y: 3pt),
    metadata-label([Contributor]),
    contributor,
    metadata-label([Course]),
    course,
    metadata-label([Dietary]),
    dietary-tags,
    metadata-label([Serves]),
    servings,
    metadata-label([Prep]),
    prep-time,
    metadata-label([Cook]),
    cook-time,
    metadata-label([Total]),
    total-time,
    [], [],
  )

  v(18pt)
  heading(level: 2, outlined: false)[Ingredients]
  columns(2, gutter: 0.3in)[
    #for section in ingredient-sections [
      #if section.title != none and section.title != [] [
        #text(font: display-font, size: 11pt, weight: "bold", fill: rgb("#92400e"))[#section.title]
        #v(4pt)
      ]
      #for item in section.items [
        #ingredient-line(item)
      ]
      #v(8pt)
    ]
  ]

  v(14pt)
  heading(level: 2, outlined: false)[Steps]
  enum(numbering: "1.", spacing: 8pt, ..steps)

  v(12pt)
  nutrition-block(nutrition-complete, nutrition)
}
