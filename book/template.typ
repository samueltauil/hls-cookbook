#import "recipe.typ": recipe

#let body-font = ("EB Garamond", "Linux Libertine", "Libertinus Serif")
#let display-font = ("Lato", "Inter", "Liberation Sans")
#let accent = rgb("#b45309")

#let cookbook(body) = {
  set page(
    width: 8.5in,
    height: 11in,
    margin: 0.75in,
    numbering: "1",
  )
  set text(font: body-font, size: 11pt, lang: "en")
  set par(justify: true, leading: 0.58em)
  show heading: set text(font: display-font, fill: rgb("#111827"))
  show heading.where(level: 1): set text(size: 24pt, weight: "bold")
  show heading.where(level: 2): set text(size: 15pt, weight: "bold")
  show link: set text(fill: accent)

  body
}

#let cover(edition: "Preview", date: "") = {
  set page(numbering: none)
  align(center + horizon)[
    #block(width: 100%)[
      #text(font: display-font, size: 46pt, weight: "bold", tracking: -1pt)[HLS Cookbook]
      #v(10pt)
      #line(length: 2.2in, stroke: 1.2pt + accent)
      #v(18pt)
      #text(size: 18pt, style: "italic")[A collection from the Hot Lunch Society]
      #v(1.2in)
      #text(font: display-font, size: 10pt, fill: rgb("#6b7280"))[
        #edition edition #if date != "" [· #date]
      ]
    ]
  ]
  pagebreak()
  set page(numbering: "i")
}

#let front-matter() = {
  align(center + horizon)[
    #block(width: 80%)[
      #heading(level: 1, outlined: false)[Acknowledgements]
      #v(10pt)
      This cookbook was assembled from recipes contributed by the Hot Lunch Society.
      Thank you to every cook, taster, reviewer, and lunch-table storyteller who made
      these pages possible.

      #v(18pt)
      #text(size: 9pt, fill: rgb("#6b7280"))[
        Community project. Recipes are provided by contributors for community use.
        Please verify allergens, dietary needs, and food-safety requirements before serving.
      ]
    ]
  ]
  pagebreak()
}

#let contents() = {
  heading(level: 1, outlined: false)[Contents]
  outline(title: none)
  pagebreak()
  set page(numbering: "1")
}

#let chapter-divider(course) = {
  pagebreak(weak: true)
  align(center + horizon)[
    #block(width: 100%)[
      #line(length: 1.2in, stroke: 1pt + accent)
      #v(16pt)
      #text(font: display-font, size: 30pt, weight: "bold")[#course]
      #v(16pt)
      #line(length: 1.2in, stroke: 1pt + accent)
    ]
  ]
  pagebreak()
}
