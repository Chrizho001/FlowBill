# FlowBill landing page — Gemini image prompts

The landing page works without these images: it draws iPhone 16 mockups in code and shows initials for
testimonials. **Drop a generated file at the exact path below and the page uses it automatically**
(dev server: just refresh; production: rebuild).

| Slot | Save as | Size / ratio | Background |
|---|---|---|---|
| Step 1 — Create | `frontend/public/images/steps/step-create.png` | 1080×1920 (9:16) | pure white `#FFFFFF` |
| Step 2 — Send | `frontend/public/images/steps/step-send.png` | 1080×1920 (9:16) | pure white `#FFFFFF` |
| Step 3 — Client pays | `frontend/public/images/steps/step-client.png` | 1080×1920 (9:16) | pure white `#FFFFFF` |
| Step 4 — Get paid | `frontend/public/images/steps/step-paid.png` | 1080×1920 (9:16) | pure white `#FFFFFF` |
| Client portal phone | `frontend/public/images/portal/portal-iphone.png` | 1080×1920 (9:16) | light grey-blue `#F5F7FC` |
| Testimonial — Amaka | `frontend/public/images/testimonials/amaka.jpg` | 1024×1280 (4:5) | studio backdrop |
| Testimonial — Kwame | `frontend/public/images/testimonials/kwame.jpg` | 1024×1280 (4:5) | studio backdrop |
| Testimonial — Zainab | `frontend/public/images/testimonials/zainab.jpg` | 1024×1280 (4:5) | studio backdrop |
| Testimonial — Tunde | `frontend/public/images/testimonials/tunde.jpg` | 1024×1280 (4:5) | studio backdrop |
| Testimonial — Wanjiru | `frontend/public/images/testimonials/wanjiru.jpg` | 1024×1280 (4:5) | studio backdrop |

> If Gemini gives you a PNG for a portrait (or a JPG for a phone), keep the exact name above and change
> only the extension in `src/content/landing.ts` (`photo:` / `image:` fields), or ask me to convert it.

---

## 1. iPhone 16 step images (4 images)

**Attach the matching screen reference** from `frontend/docs/image-refs/` so the UI text stays exact:
`step-create-screen.png`, `step-send-screen.png`, `step-client-screen.png`, `step-paid-screen.png`.
(The `*-reference.png` files show the full phone if you want Gemini to see the framing too.)

Use the same prompt for all four. Change only the attachment.

```text
Using the attached image as the exact screen content, create a photorealistic studio product render of an
Apple iPhone 16 Pro in Natural Titanium, front view, perfectly upright and centred.

The screen must show the attached screenshot exactly: keep every word, number, colour, icon and layout
unchanged, with the Dynamic Island at the top and correct rounded screen corners.

Lighting: soft, even studio light with a subtle glass reflection across the screen and a soft contact shadow
under the phone. Background: solid pure white (#FFFFFF), nothing else in the frame.

The phone fills about 92% of the image height with equal space on the left and right.
Aspect ratio 9:16, 1080×1920. No hands, no props, no extra text, no logos, no watermark.
```

**Check before saving:** the amounts read ₦450,000, the invoice number reads INV-2026-0042, and no text is
garbled. If any text drifts, regenerate with: *"The screen text is wrong. Copy the attached screenshot
exactly, pixel for pixel."*

---

## 2. Client portal iPhone (1 image)

Attach `frontend/docs/image-refs/portal-screen.png`.

```text
Using the attached image as the exact screen content, create a photorealistic studio product render of an
Apple iPhone 16 Pro in Natural Titanium, front view, upright and centred. The screen shows a client paying an
invoice from a secure payment link in Safari; display the attached screenshot exactly, keeping every word,
number, colour and layout unchanged, with the Dynamic Island at the top.

Lighting: soft premium studio light, a gentle diagonal reflection on the glass, a soft shadow beneath the
phone. Background: solid light grey-blue (#F5F7FC), nothing else in the frame.

The phone fills about 90% of the image height, centred. Aspect ratio 9:16, 1080×1920.
No hands, no props, no extra text, no watermark.
```

---

## 3. Testimonial portraits (5 images)

These are **sample, AI-generated people** for the design. They are marked as samples in code and are hidden
in production unless `NEXT_PUBLIC_SHOW_SAMPLE_TESTIMONIALS=true`. Replace them with real, consented customers
before launch.

Paste the **shared style** first, then the person's line.

**Shared style (paste first):**

```text
Editorial headshot photograph for a fintech website. Chest-up, looking directly at the camera with a genuine,
relaxed smile. Soft window light from the left, gentle fill, natural skin texture with no heavy retouching.
Background: a seamless light grey-blue studio backdrop (#E9EDF6), softly out of focus. Shot on an 85mm lens at
f/2, shallow depth of field. Photorealistic, natural colours. Aspect ratio 4:5, 1024×1280.
No text, no logos, no watermark, no jewellery glare, hands out of frame.
```

**Then one of these:**

- **amaka.jpg** — `A Nigerian woman in her late 20s, a brand designer, natural hair in a neat high afro puff, small gold stud earrings, wearing a mustard-yellow knit top.`
- **kwame.jpg** — `A Ghanaian man in his early 30s, a software developer, short fade haircut and a neatly trimmed beard, thin round glasses, wearing a dark green crew-neck T-shirt.`
- **zainab.jpg** — `A Nigerian Hausa woman in her mid 20s, a content writer, wearing a soft coral hijab and a cream blouse, warm brown eyes.`
- **tunde.jpg** — `A Nigerian man in his late 30s, the founder of a design agency, clean-shaven with a low haircut, wearing a crisp white shirt under a navy blazer, confident smile.`
- **wanjiru.jpg** — `A Kenyan woman in her early 30s, a UX consultant, long braids gathered in a low bun, wearing a navy blouse, calm friendly expression.`

**Keep them consistent:** generate all five in the same Gemini chat so the lighting and backdrop match. If one
looks off, ask: *"Same person, same style as the previous portraits, more natural smile."*
