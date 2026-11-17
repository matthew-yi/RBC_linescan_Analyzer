# Ocean artwork

Generated with the built-in image_gen tool using the two user-supplied references.

- `ocean_fish_sheet.png`: transparent 4 × 4 swimming sprite sheet; four species with four frames each. The app extracts frames at runtime, mirrors left-facing fish, and uses nearest-neighbor scaling.
- `ocean_wave.png`: pixel-art interpretation of the supplied wave painting, shown as a complete vignette with gentle movement and water effects.

These are reference-inspired generated assets, not direct extractions of the supplied fish inventory.

## Prompt summary

Fish: Use case: stylized-concept. Create a production game sprite sheet inspired by the FIRST attached reference (fish inventory pixel art). SECOND attached wave painting is only palette inspiration. Output PNG true transparent background, 1024x1024, exactly 4 columns x 4 rows equal 256px cells. Four distinct fish species one per row: silver blue trout, golden orange carp, green perch, red salmon. Each row has four side-view swimming frames with subtly changing tail and fins, same body size and position in every cell. ALL face RIGHT horizontally, no diagonal view. Each fish fits centered inside its cell with generous empty transparent margin, maximum fish bounding box 200x100 pixels. Crisp hand-crafted pixel art, dark outlines, rich limited palette, visible gills and eyes, inspired by the reference fish. No text, no grid lines, no background, no shadows outside fish. 

Wave: Pixel-art adaptation of the supplied wave painting with a curling indigo wave, cream foam, Mount Fuji, warm sky, limited game palette, no interface or text.

## Expanded ocean scene

All four earlier fish remain available. `ocean_depth_fish.png` adds eight fish types: sardine, mackerel, gold reef fish, clownfish, sea bass, purple deep-sea fish, anglerfish, and flatfish. `ocean_mammals.png` preserves the initial detailed marine-mammal artwork; the app uses `ocean_mammals_flat.png`, a simpler four-frame sprite sheet of dolphins, orcas, humpbacks, and belugas. It is downsampled and color-keyed from a built-in image generator output.

Prompt summary for additional fish: transparent 4-column, 8-row pixel-art sheet, four aligned swimming frames per creature, crisp silhouettes and limited palette. Prompt summary for the final mammals: four columns by four rows of right-facing dolphins, orcas, humpback whales and belugas, simple 32×16-style pixel silhouettes, five flat colors per animal, no gradients or effects, solid magenta background removed for transparent app sprites. The user’s orca reference guided the simpler style.

The full-window editor background uses code-drawn depth bands, animated waves, sand and seaweed, plus the generated wave vignette. Controls and scan viewer overlay this background. Creatures are assigned decorative surface, midwater, deep-water and bottom bands, not a scientific habitat chart.

Current rendering: the painting is retained as a reference asset but is no longer displayed or tiled. Wave motion is drawn directly as continuous shaded swells and foam. Fish and marine mammals display one stationary sprite per species; swimming frames are retained in the asset sheets for reference.

`great_wave_animation.png` is the active wave artwork, generated with the built-in image generator. It has two columns and four rows: eight panoramic Great Wave frames, played in a forward/backward loop. Final prompt summary: re-layout Great Wave animation as exactly two columns and four rows on a landscape 1536×1024 canvas; each 768×256 panorama contains a large curling indigo wave on the left, foam fingers, low Mount Fuji on the right, cream sky and dark ocean; consistent composition and pixel clusters across eight subtle animation frames; no text, borders, labels or grid lines. The app preserves aspect ratio and never repeats the painting horizontally.

Banner layout correction: complete frames now use aspect-preserving cover scaling and cropping, without edge-column padding. Rendering is tested at normal and wide window sizes.

Active artwork is now `small_waves_animation.png`, edited with the built-in image generator from the Great Wave animation sheet. Edit prompt: remove only the giant curling wave from the left of every panel, replace it with matching sky and small low rolling waves; preserve the smaller waves, Mount Fuji, colors, eight-frame two-column/four-row layout, and gentle water animation. The app aligns cropping to the bottom so the smaller waves remain visible in short banners.

The app now crops the active sheet to its water region when rendering. Both windows use a full-window underwater background. Creatures use one sprite pose and move through smoothly steered random paths within their depth bands.

Runtime corrections preserve sprite RGB/alpha without recoloring, remove marine-mammal magenta key remnants, and scale the full small-wave water band to the window width with a soft alpha transition into deeper water.

## Seattle artwork

`seattle_skyline.png` was created with the built-in image generator from the user's skyline photograph. It is the static background for both Seattle-theme windows. The app scales the artwork to cover the window with nearest-neighbor resizing, crops edges as needed, and dims the presentation slightly for text contrast.

Final prompt: Use case: style-transfer. Transform the attached Seattle skyline photograph into clean detailed 16-bit pixel art for a desktop application's Seattle theme. Preserve the actual composition: Space Needle prominent on LEFT, downtown Seattle skyline in middle, snowy Mount Rainier on RIGHT in distance, green trees and Seattle Center buildings in foreground, clear blue sky above. Keep recognizable proportions and positions of landmarks. Crisp square pixel clusters, hand-crafted game background, limited blue/evergreen/warm stone palette, no gradients or photo texture. Landscape 1536x1024. No text, logos, interface, borders, invented landmarks, or watermarks. The result should be a pixel-art adaptation of THIS photograph, not a different Seattle scene.

## Tokyo artwork and city weather

`tokyo_skyline.png` was created with the built-in image generator from the user's Tokyo photo. The app animates cherry blossom petals separately using small code-drawn particles. Seattle Rain reuses `seattle_skyline.png`, applies a cooler presentation, and draws rain particles at runtime. No weather is baked into scan images or exported results.

Final Tokyo prompt: Use case: style-transfer. Turn the attached Tokyo skyline photograph into crisp richly detailed 16-bit pixel art for a desktop app theme. Preserve THIS composition: red-and-white Tokyo Tower left of center, dense Tokyo buildings below, huge snowy Mount Fuji centered in distance, soft golden sunset on right, blue sky with pale clouds. Keep landmark scale, city layout, lighting direction, and camera. Deliberate square pixel clusters and limited warm gold, slate blue, muted pink and evergreen palette; no photographic texture, no smooth gradients. Landscape 1536x1024. Do not add text, logos, borders, people or interface. Do not bake cherry petals into the scene; the app will animate those separately. No invented landmarks.

## Overcast Seattle Rain

`seattle_rain_skyline.png` is a separate built-in image-generator edit of the sunny Seattle artwork; regular Seattle still uses the original. Foreground rain is animated in code.

Final edit prompt: Edit this Seattle pixel-art skyline for a POURING RAIN weather variant. Change the bright blue sky to a fully overcast GRAY sky with layered, thick storm clouds, light and dark slate grey pixel clusters, NO blue sky patches and NO sunshine. Keep the Space Needle, all buildings, Mount Rainier, trees, camera framing, exact landmark positions, and crisp pixel art style. Cool overcast lighting, slightly muted wet green trees and wet-looking roofs, light atmospheric haze around mountain. Do not draw foreground raindrops or rain streaks; animated rain is added by app. No lightning, text, logos, UI, borders. Preserve the image dimensions and composition.
