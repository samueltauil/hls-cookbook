#import "template.typ": cookbook, cover, front-matter, contents, chapter-divider
#import "recipe.typ": recipe

#show: cookbook

#cover(edition: "Sample", date: "June 12, 2026")
#front-matter()
#contents()

#chapter-divider([Mains])

#recipe(
  title: [Chicken Adobo],
  contributor: [Ana Reyes],
  cuisine: [Filipino],
  course: [Mains],
  dietary-tags: [gluten-free, dairy-free],
  prep-time: [15 min],
  cook-time: [45 min],
  total-time: [60 min],
  servings: [4],
  summary: [A comforting Filipino braise of chicken, vinegar, soy, garlic, and bay leaves. The sauce reduces to a glossy, tangy-salty glaze that is perfect over steamed rice.],
  ingredient-sections: (
    (
      title: [Chicken],
      items: (
        (quantity: [900 g (2 lb)], name: [bone-in chicken thighs], notes: [skin-on]),
        (quantity: [120 ml (1/2 cup)], name: [soy sauce], notes: none),
        (quantity: [120 ml (1/2 cup)], name: [cane vinegar], notes: none),
        (quantity: [10 cloves], name: [garlic], notes: [smashed]),
        (quantity: [3], name: [bay leaves], notes: none),
        (quantity: [1 tsp], name: [black peppercorns], notes: [cracked]),
      ),
    ),
    (
      title: [To Serve],
      items: (
        (quantity: [4 cups], name: [steamed jasmine rice], notes: none),
        (quantity: [2], name: [scallions], notes: [thinly sliced]),
      ),
    ),
  ),
  steps: (
    [Combine soy sauce, vinegar, garlic, bay leaves, and peppercorns in a wide pot. Add chicken and turn to coat. Rest for 20 minutes while the rice cooks.],
    [Bring the pot to a simmer over medium heat. Cover, reduce heat, and cook until the chicken is tender, about 30 minutes.],
    [Uncover and simmer briskly, turning the chicken once or twice, until the sauce reduces and lightly glazes the meat.],
    [Serve chicken and sauce over rice with scallions.],
  ),
  nutrition-complete: true,
  nutrition: (
    calories: [410 kcal],
    protein: [32 g],
    fat: [22 g],
    carbs: [14 g],
  ),
)

