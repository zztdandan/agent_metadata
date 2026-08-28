# Design System Document: Industrial Editorial

## 1. Overview & Creative North Star
The core objective of this design system is to transform the traditional, high-density IOT dashboard into a high-end, "Industrial Editorial" experience. While IOT platforms often suffer from "data-clutter," this system prioritizes clarity and intentionality.

**Creative North Star: The Precision Curator**
We treat industrial data with the same reverence as architectural photography. The layout is not a grid to be filled, but a canvas where white space acts as a functional separator. By moving from dense lists to spacious card-based layouts, we emphasize the "Signal" over the "Noise." We break the "template" look through **asymmetric data distribution** and **layered tonal depth**, ensuring the platform feels premium, authoritative, and bespoke.

---

## 2. Colors
Our palette balances the sterility of industrial grey with a vibrant, high-energy "Action Blue" to signify connectivity and movement.

*   **Primary Action:** `primary` (#0045db) used for main CTAs and critical status indicators.
*   **Surface Hierarchy:** We utilize the `surface-container` tiers to define logic.
*   **The "No-Line" Rule:** Designers are **prohibited** from using 1px solid borders to section off large areas of the UI. Separation must be achieved via background shifts. For example, a card (`surface_container_lowest`) sits on a workspace (`surface_background`) without a stroke.
*   **The "Glass & Gradient" Rule:** To provide "soul" to the industrial data, use semi-transparent overlays for the Agent panel. Use a subtle linear gradient from `primary` (#0045db) to `primary_container` (#285eff) on primary buttons to create depth.

---

## 3. Typography
We use **Inter** as our typographic backbone. It provides the mathematical precision required for IOT data while remaining approachable.

*   **Display (lg/md):** Reserved for high-level KPIs and system health percentages. Large, bold, and authoritative.
*   **Headline & Title:** Used for Agent names and Card headers. We use `headline-sm` for card titles to create a clear entry point for the eye.
*   **Body & Labels:** All data points use `body-md` or `label-md`. We prioritize `label-md` for metadata (e.g., "Last Sync") to create a clear visual distinction from the primary data values.
*   **Editorial Intent:** Use `display-sm` for empty states or welcome headers to break the monotony of the technical interface.

---

## 4. Elevation & Depth
In this system, depth is not "drawn"—it is felt through tonal stacking.

*   **The Layering Principle:** 
    *   **Level 0 (Base):** `surface` (#f8f9fa) - The main background.
    *   **Level 1 (Section):** `surface_container_low` (#f3f4f5) - Used for grouping content.
    *   **Level 2 (Active Card):** `surface_container_lowest` (#ffffff) - Used for the primary interactive cards.
*   **Ambient Shadows:** For floating elements like the Agent Panel or Modals, use a "Tinted Shadow." 
    *   *Shadow Token:* `0px 12px 32px rgba(25, 28, 29, 0.06)` (A 6% opacity shadow tinted with `on_surface`).
*   **The "Ghost Border" Fallback:** If a container requires a boundary (e.g., a search input), use a "Ghost Border": `outline_variant` at **15% opacity**.
*   **Glassmorphism:** The Agent panel should utilize `backdrop-filter: blur(12px)` combined with a semi-transparent `surface` color to allow the dashboard's "glow" to bleed through the edges.

---

## 5. Components

### Cards (The Primary Container)
Move away from 100% width table rows. Use cards with `DEFAULT` (8px) or `md` (12px) roundedness.
*   **Layout:** Vertical white space (`spacing-4`) must separate cards.
*   **Interaction:** On hover, a card should shift from `surface_container_lowest` to a subtle `surface_bright` with an ambient shadow.

### Buttons
*   **Primary:** Gradient fill (`primary` to `primary_container`), `full` roundedness for high-action visibility.
*   **Secondary:** `surface_container_high` background with `on_secondary_container` text. No border.
*   **Tertiary:** Ghost style. Only text and icon, using `primary` color.

### The Agent Panel (Drawers)
*   **Animation:** Use a "Swift-In, Soft-Out" transition. `transform: translateX` with a `cubic-bezier(0.3, 0, 0, 1)` curve over 400ms. 
*   **Visual:** Apply a glassmorphism effect to the panel background to ensure it feels like a physical layer floating above the data.

### Input Fields
*   **Styling:** Forgo the four-sided box. Use a subtle `surface_container_high` background with a bottom-only `outline` for an editorial, modern look.
*   **States:** On focus, the bottom border expands to 2px using the `primary` blue.

---

## 6. Do's and Don'ts

### Do
*   **Do** use `surface_container` shifts to group related IOT sensors.
*   **Do** use `spacing-6` (2rem) as your standard gutter between major card sections to allow the UI to "breathe."
*   **Do** use `tertiary` (#9d3000) for critical warnings, but keep the container background `tertiary_fixed` (#ffdbd0) to keep the "light mode" feel consistent.

### Don't
*   **Don't** use 100% black text. Always use `on_surface` (#191c1d) to maintain a premium, softer contrast.
*   **Don't** use dividers (`<hr>`) unless strictly necessary for a dense data table. Use white space (`spacing-2` or `3`) instead.
*   **Don't** use sharp 90-degree corners. Everything in the industrial environment should feel "machined" and ergonomic (8px–12px).
*   **Don't** use default drop shadows. If a shadow looks "dirty" or "grey," it is too opaque. Reduce to 4–8%.