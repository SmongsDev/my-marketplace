---
name: vanilla-presentation
description: >
  Generates a complete, single-file HTML slide presentation using only vanilla HTML, CSS, and JavaScript — no libraries.
  Use this skill whenever the user asks to create a presentation, slide deck, or slideshow with HTML/CSS/JS.
  Trigger on: "슬라이드 만들어줘", "프레젠테이션 만들어줘", "발표 자료 만들어줘", "HTML 슬라이드", "PPT 대신 HTML로", "make a presentation", "create slides", "build a slide deck", "HTML slideshow", or any request for a presentation/slideshow output file.
  Even if the user says "PPT" or "파워포인트", if they're working with Claude Code and haven't specified a tool, strongly prefer generating a vanilla HTML presentation.
---

# Vanilla HTML Presentation Skill

Generate a polished, **single-file** HTML presentation using only HTML, CSS, and JavaScript — zero external dependencies.

## Output

Always produce **one self-contained `.html` file**. All CSS and JS go inside `<style>` and `<script>` tags. The file must work offline, no CDN, no imports.

Exception: Google Fonts `<link>` tags are acceptable for typography if the user hasn't said "offline-only". Include `Noto Sans KR` for Korean content.

---

## Slide Architecture

### Layout
Use **absolute positioning** for all slides — every slide stacks at the same position, z-index controls visibility. This enables GPU-composited transitions.

```html
<div class="presentation">
  <div class="slide-container" id="slideContainer">
    <section class="slide is-active" data-index="0" data-theme="amber">
      <div class="slide-body">...</div>
    </section>
    <section class="slide" data-index="1" data-theme="navy">
      <div class="slide-body">...</div>
    </section>
  </div>
  <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
  <div class="bottom-bar"><!-- nav UI --></div>
</div>
```

### Core CSS skeleton

```css
.slide-container {
  position: relative; flex: 1; overflow: hidden;
  contain: layout style paint;
}
.slide {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  opacity: 0; pointer-events: none; z-index: 0;
  transition: opacity 0.55s cubic-bezier(0.4,0,0.2,1),
              transform 0.55s cubic-bezier(0.4,0,0.2,1);
  transform: translateX(60px) scale(0.98);
}
.slide.is-active { opacity: 1; pointer-events: auto; z-index: 10; transform: translateX(0) scale(1); }
.slide.is-exit   { opacity: 0; z-index: 5; }
```

Only animate `transform` and `opacity` — these run on the GPU compositor and never trigger layout or paint.

---

## Themes

Use `data-theme` on each `<section class="slide">` to assign a dark gradient background. Include these built-in themes:

| value | palette |
|-------|---------|
| `amber` | warm gold-brown dark |
| `navy` | deep blue |
| `teal` | dark teal-green |
| `crimson` | dark red |
| `sienna` | warm dark orange |
| `violet` | deep purple |

Pick themes that match the slide's mood or alternate for visual variety. The title slide → amber or violet; TOC/section dividers → navy; content slides → cycle through the rest.

---

## Slide Types & Layouts

### Title slide
```html
<section class="slide is-active" data-index="0" data-theme="amber">
  <div class="slide-body">
    <div class="tag">TOPIC TAG</div>
    <h1>Main Title<br>Second Line</h1>
    <p data-step="1" style="--si:0">Subtitle or description text</p>
    <div class="meta-info" data-step="2" style="--si:1">
      <span><strong>발표자</strong>&ensp;Name</span>
      <span><strong>날짜</strong>&ensp;YYYY년 MM월 DD일</span>
    </div>
  </div>
</section>
```

### Table of contents
Use a `.toc-grid` with `.toc-item` cards (each with `.num` + `.title`), each item as `data-step` fragments.

### Content / bullet list
Add `data-layout="list"` to the `<section>` for left-aligned content:
```html
<section class="slide" data-index="N" data-theme="teal" data-layout="list">
  <div class="slide-body">
    <h2>Slide Title</h2>
    <ul style="margin-top: 14px;">
      <li data-step="1" style="--si:0">First point</li>
      <li data-step="2" style="--si:1">Second point</li>
    </ul>
  </div>
</section>
```

### Two-column (code + explanation)
```html
<div class="two-col">
  <pre><code>...</code></pre>
  <div class="code-desc">
    <h3>Key Points</h3>
    <div class="highlight-box" data-step="1" style="--si:0">...</div>
  </div>
</div>
```

### Stats / results
Use `.result-grid` with `.result-card` elements (`.value` + `.label`).

### Tech badges
Use `.tech-grid` with `.tech-badge` items.

### Q&A / closing
```html
<div class="qa-wrap">
  <div class="qa-big" data-step="1">🙋</div>
  <h1>Q &amp; A</h1>
  <p data-step="2">감사합니다.</p>
  <div class="contact-row" data-step="3">
    <span class="contact-item">📧 <strong>email</strong></span>
  </div>
</div>
```

---

## Fragment System (Build Effects)

Fragments are elements with `data-step="N"` that appear one at a time on Space/→ key press.

- `data-step` values: 1, 2, 3, ... (ascending reveal order within a slide)
- `--si` CSS variable: stagger index (0-based) for smooth delay between items
- Fragment CSS: hidden by default (`opacity:0; transform:translateY(16px)`), revealed by `.revealed` class

```css
[data-step] {
  opacity: 0; transform: translateY(16px);
  transition: opacity 0.45s ease, transform 0.45s ease;
  pointer-events: none;
}
[data-step].revealed {
  opacity: 1; transform: translateY(0); pointer-events: auto;
  transition-delay: calc(var(--si, 0) * 0.07s);
}
```

Use fragments thoughtfully: title descriptions, TOC items, bullet list items, highlight boxes, and closing slides benefit from fragments. Static content like headings usually should not be fragments.

---

## Navigation & JavaScript

### State and transitions

```javascript
let currentIndex = 0, isAnimating = false, isComposing = false;
let transitionType = 'slide'; // 'slide' | 'fade' | 'zoom' | 'flip'
const DURATION = 520;

async function goTo(nextIdx, direction) {
  if (isAnimating || nextIdx === currentIndex) return;
  if (nextIdx < 0 || nextIdx >= TOTAL) return;
  isAnimating = true;
  updateUI(nextIdx);
  const dir = direction || (nextIdx > currentIndex ? 'next' : 'prev');
  const oldSlide = slides[currentIndex], newSlide = slides[nextIdx];
  try {
    oldSlide.style.willChange = 'transform, opacity';
    newSlide.style.willChange = 'transform, opacity';
    newSlide.style.transition = 'none';
    newSlide.style.transform  = getEnterTransform(dir);
    newSlide.style.opacity    = '0';
    await nextFrame();
    applyTransitionCSS();
    oldSlide.classList.add('is-exit');
    oldSlide.classList.remove('is-active');
    oldSlide.style.transform = getExitTransform(dir);
    oldSlide.style.opacity   = '0';
    newSlide.style.transform = 'translateX(0) scale(1) rotateY(0deg)';
    newSlide.style.opacity   = '1';
    newSlide.classList.add('is-active');
    await waitFor(oldSlide);
    // cleanup
    [oldSlide, newSlide].forEach(s => {
      s.style.transform = s.style.opacity = s.style.zIndex = '';
      s.style.willChange = 'auto';
    });
    oldSlide.classList.remove('is-exit');
    resetFragments(newSlide);
    currentIndex = nextIdx;
    btnPrev.disabled = currentIndex === 0;
    btnNext.disabled = currentIndex === TOTAL - 1;
    syncHash();
  } finally { isAnimating = false; }
}

const nextFrame = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));

function waitFor(el) {
  return new Promise(resolve => {
    let done = false;
    const finish = () => { if (done) return; done = true; el.removeEventListener('transitionend', finish); clearTimeout(tid); resolve(); };
    const tid = setTimeout(finish, DURATION + 80);
    el.addEventListener('transitionend', finish);
  });
}
```

### Keyboard input
```javascript
document.addEventListener('keydown', e => {
  if (isComposing) return;
  const tag = document.activeElement?.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
  switch (e.key) {
    case 'ArrowRight': case 'PageDown': advance();       e.preventDefault(); break;
    case 'ArrowLeft':  case 'PageUp':  retreat();       e.preventDefault(); break;
    case ' ':                          advance();       e.preventDefault(); break;
    case 'Home':                       goTo(0);         e.preventDefault(); break;
    case 'End':                        goTo(TOTAL - 1); e.preventDefault(); break;
    case 't': case 'T': cycleTransition(); break;
    case 'f': case 'F': toggleFullscreen(); break;
    case 's': case 'S': openSpeakerNotes(); break;
  }
});
document.addEventListener('compositionstart', () => { isComposing = true; });
document.addEventListener('compositionend',   () => { isComposing = false; });
```

### Touch swipe
```javascript
let touchStartX = 0, touchStartY = 0;
container.addEventListener('touchstart', e => {
  touchStartX = e.touches[0].clientX; touchStartY = e.touches[0].clientY;
}, { passive: true });
container.addEventListener('touchend', e => {
  const dx = e.changedTouches[0].clientX - touchStartX;
  const dy = e.changedTouches[0].clientY - touchStartY;
  if (Math.abs(dx) < 50 || Math.abs(dy) / Math.abs(dx) > 0.6) return;
  dx < 0 ? advance() : retreat();
}, { passive: true });
```

### Fragment manager
```javascript
function getFragments(slide) {
  return Array.from(slide.querySelectorAll('[data-step]'))
    .sort((a, b) => +a.dataset.step - +b.dataset.step);
}
function advance() {
  const next = getFragments(slides[currentIndex]).find(f => !f.classList.contains('revealed'));
  if (next) { next.classList.add('revealed'); return; }
  if (currentIndex < TOTAL - 1) goTo(currentIndex + 1, 'next');
}
function retreat() {
  const revealed = getFragments(slides[currentIndex]).filter(f => f.classList.contains('revealed'));
  if (revealed.length) { revealed.at(-1).classList.remove('revealed'); return; }
  if (currentIndex > 0) goTo(currentIndex - 1, 'prev');
}
function resetFragments(slide) {
  getFragments(slide).forEach(f => f.classList.remove('revealed'));
}
```

### URL hash sync
```javascript
function syncHash() {
  history.pushState({ slideIndex: currentIndex }, '', `#slide-${currentIndex + 1}`);
}
window.addEventListener('hashchange', () => {
  const m = location.hash.match(/slide-(\d+)/);
  if (m) { const i = +m[1] - 1; if (!isNaN(i) && i !== currentIndex) goTo(i); }
});
```

### Transition types

```javascript
const TRANSITION_TYPES = ['slide', 'fade', 'zoom', 'flip'];

function applyTransitionCSS() {
  const dur = DURATION / 1000, ease = 'cubic-bezier(0.4,0,0.2,1)';
  const rules = {
    slide: `opacity ${dur}s ${ease}, transform ${dur}s ${ease}`,
    fade:  `opacity ${dur}s ${ease}`,
    zoom:  `opacity ${dur}s ${ease}, transform ${dur}s ${ease}`,
    flip:  `opacity ${dur}s ${ease}, transform ${dur}s ${ease}`,
  };
  slides.forEach(s => { s.style.transition = rules[transitionType]; });
  container.style.perspective = transitionType === 'flip' ? '1000px' : '';
}

function getEnterTransform(dir) {
  const d = dir === 'next' ? 1 : -1;
  switch (transitionType) {
    case 'slide': return `translateX(${d * 60}px) scale(0.98)`;
    case 'zoom':  return `scale(${dir === 'next' ? 0.82 : 1.18})`;
    case 'flip':  return `rotateY(${d * 80}deg)`;
    default:      return 'none';
  }
}
function getExitTransform(dir) {
  const d = dir === 'next' ? -1 : 1;
  switch (transitionType) {
    case 'slide': return `translateX(${d * 60}px) scale(0.98)`;
    case 'zoom':  return `scale(${dir === 'next' ? 1.18 : 0.82})`;
    case 'flip':  return `rotateY(${d * -80}deg)`;
    default:      return 'none';
  }
}

function cycleTransition() {
  const i = TRANSITION_TYPES.indexOf(transitionType);
  transitionType = TRANSITION_TYPES[(i + 1) % TRANSITION_TYPES.length];
  applyTransitionCSS();
  transLabel.textContent = transitionType;
  showToast(`전환 효과: ${transitionType}`);
}
```

### UI update
```javascript
function updateUI(idx = currentIndex) {
  cntCur.textContent = idx + 1;
  progressFill.style.width = `${(idx + 1) / TOTAL * 100}%`;
  btnPrev.disabled = idx === 0;
  btnNext.disabled = idx === TOTAL - 1;
  Array.from(indicators.children).forEach((dot, i) => dot.classList.toggle('active', i === idx));
}
```

---

## Bottom Bar HTML

```html
<div class="bottom-bar">
  <button class="nav-btn" id="btnPrev" disabled aria-label="이전 슬라이드">‹</button>
  <div class="indicators" id="indicators"></div>
  <span class="slide-counter">
    <span id="cntCur">1</span>&thinsp;/&thinsp;<span id="cntTot"></span>
  </span>
  <button class="nav-btn" id="btnNext" aria-label="다음 슬라이드">›</button>
  <span class="transition-label" id="transLabel" title="T 키로 전환 효과 변경">slide</span>
  <div class="hint" id="hintBar">
    <span><kbd>→</kbd> 다음</span>
    <span><kbd>←</kbd> 이전</span>
    <span><kbd>T</kbd> 전환</span>
    <span><kbd>S</kbd> 노트</span>
    <span><kbd>F</kbd> 전체화면</span>
  </div>
  <button class="fs-btn" id="btnFs" title="전체화면 (F)">⛶</button>
</div>
```

---

## Speaker Notes

Store notes as JSON in a `<script type="application/json" id="speakerNotes">` tag — an array where index matches slide index:

```html
<script type="application/json" id="speakerNotes">
["Slide 1 notes...", "Slide 2 notes...", "..."]
</script>
```

Always write speaker notes! They don't need to be long — 1-3 sentences per slide suggesting what to say or highlight.

The speaker notes window (S key) opens a popup with the current notes and a presentation timer.

---

## Typography

```css
.slide h1 {
  font-size: clamp(24px, 5vw, 50px); font-weight: 700;
  background: linear-gradient(135deg, #FFFBEF 30%, #E8C97A 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 2px 12px rgba(198,165,92,0.35));
}
.slide h2 { font-size: clamp(20px, 3.6vw, 38px); color: #F0EAD6; }
.slide h3 { font-size: clamp(15px, 2.2vw, 22px); color: #C6A55C; }
.slide p  { font-size: clamp(13px, 2vw, 18px); line-height: 1.75; color: rgba(240,234,214,0.8); }
```

Always use `clamp()` for font sizes — never fixed `px` for heading/body text.

---

## Color Palette Reference

| Role | Value |
|------|-------|
| Primary accent | `#C6A55C` |
| Accent bright | `#E8C97A` |
| Text primary | `#F0EAD6` |
| Text muted | `rgba(240,234,214,0.8)` |
| Text dim | `rgba(240,234,214,0.45)` |
| Border | `rgba(198,165,92,0.2)` |
| Surface overlay | `rgba(198,165,92,0.06)` |

---

## Init Script Pattern

```javascript
function init() {
  cntTot.textContent = TOTAL;
  // Build indicator dots
  slides.forEach((_, i) => {
    const dot = document.createElement('button');
    dot.className = 'dot' + (i === 0 ? ' active' : '');
    dot.setAttribute('aria-label', `${i + 1}번 슬라이드`);
    dot.addEventListener('click', () => goTo(i));
    indicators.appendChild(dot);
  });
  // Restore from URL hash
  const match = location.hash.match(/slide-(\d+)/);
  if (match) {
    const idx = +match[1] - 1;
    if (idx > 0 && idx < TOTAL) {
      slides[0].classList.remove('is-active');
      slides[idx].classList.add('is-active');
      currentIndex = idx;
    }
  }
  updateUI();
  attachEvents();
}
init();
```

---

## Checklist Before Output

Before writing the final HTML, confirm:

- [ ] Every slide has a unique `data-index` starting from 0
- [ ] First slide has `class="slide is-active"`
- [ ] `data-step` numbering on each slide starts from 1 and is consecutive
- [ ] `--si` values on fragments match 0-based order within that slide
- [ ] Speaker notes array length matches slide count
- [ ] All JS DOM references (btnPrev, btnNext, etc.) match actual HTML `id`s
- [ ] `cntTot` element exists and `init()` sets its `textContent = TOTAL`
- [ ] Fonts: Noto Sans KR included if content has Korean text
- [ ] `contain: layout style paint` on `.slide-container`
- [ ] `will-change` set before animations, cleared after

---

## Adapting to User Input

**Minimal prompt** ("발표 자료 만들어줘 — 주제: 클라우드 보안"): Infer structure. Generate ~6-8 slides: title → TOC → 3-4 content slides → closing. Pick relevant themes.

**Detailed prompt**: Follow the user's outline exactly. Map each section to a slide type.

**Language**: Match the user's language. Korean content → include Noto Sans KR. English content → Inter only.

**Tone**: Infer from topic. Academic/tech → cleaner layouts, more code slides. Business → more stats/result cards.
