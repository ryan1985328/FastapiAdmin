<!-- Admin 登录页技术视觉：用轻量 SVG 表达数据核心、API 与基础设施连接。 -->
<template>
  <section class="login-left-view" aria-label="AI-first technology foundation">
    <div class="login-left-view__texture" aria-hidden="true"></div>

    <div class="login-left-view__content">
      <div class="login-left-view__kicker">
        <span class="login-left-view__status" aria-hidden="true"></span>
        <span>AI-FIRST / DATA CORE</span>
      </div>

      <div class="login-left-view__art" aria-hidden="true">
        <svg
          class="login-left-view__diagram"
          viewBox="0 0 760 560"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="login-line-gradient" x1="40" y1="40" x2="720" y2="520">
              <stop offset="0" stop-color="#6C7CFF" stop-opacity="0.12" />
              <stop offset="0.5" stop-color="#6FD8FF" stop-opacity="0.82" />
              <stop offset="1" stop-color="#9A83FF" stop-opacity="0.12" />
            </linearGradient>
            <radialGradient
              id="login-core-gradient"
              cx="0"
              cy="0"
              r="1"
              gradientTransform="translate(390 276) rotate(90) scale(112)"
            >
              <stop offset="0" stop-color="#F3FBFF" />
              <stop offset="0.18" stop-color="#9BE8FF" />
              <stop offset="0.58" stop-color="#7182FF" />
              <stop offset="1" stop-color="#3B4AB4" stop-opacity="0.3" />
            </radialGradient>
            <linearGradient id="login-core-edge" x1="318" y1="193" x2="462" y2="359">
              <stop stop-color="#B9F2FF" stop-opacity="0.9" />
              <stop offset="0.55" stop-color="#7584FF" stop-opacity="0.8" />
              <stop offset="1" stop-color="#A68DFF" stop-opacity="0.22" />
            </linearGradient>
            <filter id="login-core-glow" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="15" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="login-node-glow" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <g class="login-left-view__grid">
            <path
              d="M36 64H724M36 124H724M36 184H724M36 244H724M36 304H724M36 364H724M36 424H724M36 484H724"
            />
            <path
              d="M80 40V520M160 40V520M240 40V520M320 40V520M400 40V520M480 40V520M560 40V520M640 40V520"
            />
          </g>

          <g class="login-left-view__network-lines">
            <path d="M42 126C154 104 230 158 306 216" />
            <path d="M38 430C154 404 236 340 318 298" />
            <path d="M462 238C548 206 638 140 720 92" />
            <path d="M470 336C574 358 646 426 724 466" />
            <path d="M196 48C272 126 316 178 352 220" />
            <path d="M574 522C544 432 500 382 450 350" />
            <path
              class="login-left-view__network-line--dashed"
              d="M62 520C172 450 246 422 300 378"
            />
            <path
              class="login-left-view__network-line--dashed"
              d="M574 42C548 128 508 178 456 222"
            />
          </g>

          <g class="login-left-view__rings">
            <ellipse cx="390" cy="276" rx="298" ry="172" transform="rotate(-14 390 276)" />
            <ellipse cx="390" cy="276" rx="236" ry="132" transform="rotate(28 390 276)" />
            <ellipse cx="390" cy="276" rx="190" ry="104" transform="rotate(-42 390 276)" />
          </g>

          <g class="login-left-view__nodes" filter="url(#login-node-glow)">
            <circle cx="42" cy="126" r="5" />
            <circle cx="38" cy="430" r="5" />
            <circle cx="196" cy="48" r="4" />
            <circle cx="62" cy="520" r="4" />
            <circle cx="720" cy="92" r="5" />
            <circle cx="724" cy="466" r="5" />
            <circle cx="574" cy="42" r="4" />
            <circle cx="574" cy="522" r="4" />
          </g>

          <g class="login-left-view__core" filter="url(#login-core-glow)">
            <circle class="login-left-view__core-halo" cx="390" cy="276" r="146" />
            <circle
              class="login-left-view__core-halo login-left-view__core-halo--inner"
              cx="390"
              cy="276"
              r="98"
            />
            <polygon
              class="login-left-view__core-hex"
              points="390,193 462,234 462,318 390,359 318,318 318,234"
            />
            <polygon
              class="login-left-view__core-hex login-left-view__core-hex--inner"
              points="390,223 436,250 436,302 390,329 344,302 344,250"
            />
            <path class="login-left-view__core-axis" d="M390 223V329M344 276H436" />
            <circle class="login-left-view__core-dot" cx="390" cy="276" r="27" />
            <circle class="login-left-view__core-point" cx="390" cy="276" r="6" />
          </g>
        </svg>

        <span class="login-left-view__signal login-left-view__signal--api">
          <span>API</span>
        </span>
        <span class="login-left-view__signal login-left-view__signal--data">
          <span>DATA</span>
        </span>
        <span class="login-left-view__signal login-left-view__signal--core">
          <span>CORE</span>
        </span>
      </div>

      <div class="login-left-view__copy">
        <h2>{{ $t("login.leftView.title") }}</h2>
        <p class="login-left-view__subtitle">{{ $t("login.leftView.subTitle") }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineOptions({ name: "FaLoginLeftView" });
</script>

<style scoped lang="scss">
.login-left-view {
  position: relative;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  min-height: 100%;
  overflow: hidden;
  color: #edf4ff;
  background:
    radial-gradient(circle at 18% 16%, rgb(108 124 255 / 22%) 0, transparent 30%),
    radial-gradient(circle at 84% 76%, rgb(78 207 255 / 13%) 0, transparent 29%),
    linear-gradient(135deg, #0e1737 0%, #12204b 56%, #0b1536 100%);
  isolation: isolate;
}

.login-left-view::before {
  position: absolute;
  inset: 0;
  z-index: -2;
  content: "";
  background-image: var(--login-configured-background, none);
  background-position: center;
  background-size: cover;
  mix-blend-mode: screen;
  opacity: 0.1;
}

.login-left-view::after {
  position: absolute;
  inset: 0 -1px 0 auto;
  z-index: 4;
  width: clamp(2.75rem, 4.5vw, 4.5rem);
  pointer-events: none;
  content: "";
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgb(140 163 211 / 14%) 48%,
    var(--login-workspace-bg, #f6f8fc) 100%
  );
  opacity: 0.8;
}

.login-left-view__texture {
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background-image:
    linear-gradient(rgb(170 192 255 / 7%) 1px, transparent 1px),
    linear-gradient(90deg, rgb(170 192 255 / 7%) 1px, transparent 1px);
  background-size: 64px 64px;
  opacity: 0.55;
  mask-image: linear-gradient(to bottom, transparent 0%, black 18%, black 78%, transparent 100%);
}

.login-left-view__content {
  position: relative;
  z-index: 2;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: clamp(6.5rem, 12vh, 8.5rem) clamp(2rem, 5.2vw, 5.5rem) clamp(2.5rem, 6vh, 4rem);
}

.login-left-view__kicker {
  display: flex;
  align-items: center;
  width: min(100%, 52rem);
  font-size: 0.68rem;
  font-weight: 600;
  line-height: 1;
  color: rgb(210 225 255 / 66%);
  letter-spacing: 0.18em;
}

.login-left-view__status {
  display: inline-block;
  width: 0.45rem;
  height: 0.45rem;
  margin-right: 0.7rem;
  background: #6fe0ff;
  border-radius: 50%;
  box-shadow:
    0 0 0 4px rgb(111 224 255 / 10%),
    0 0 16px rgb(111 224 255 / 70%);
}

.login-left-view__art {
  position: relative;
  width: min(100%, 52rem);
  height: clamp(20rem, 49vh, 37rem);
  margin: clamp(0.5rem, 1.5vh, 1rem) 0 clamp(0.75rem, 2vh, 1.5rem);
}

.login-left-view__diagram {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.login-left-view__grid {
  fill: none;
  stroke: rgb(170 192 255 / 10%);
  stroke-width: 0.8;
  stroke-dasharray: 1 8;
}

.login-left-view__network-lines {
  opacity: 0.72;
  fill: none;
  stroke: url("#login-line-gradient");
  stroke-width: 1.4;
  stroke-linecap: round;
}

.login-left-view__network-line--dashed {
  opacity: 0.62;
  stroke-dasharray: 5 11;
  animation: login-network-flow 16s linear infinite;
}

.login-left-view__rings {
  fill: none;
  stroke: rgb(132 157 255 / 32%);
  stroke-width: 1;
}

.login-left-view__rings ellipse:nth-child(2) {
  stroke: rgb(116 221 255 / 35%);
  stroke-dasharray: 2 9;
}

.login-left-view__rings ellipse:nth-child(3) {
  stroke: rgb(177 149 255 / 28%);
  stroke-dasharray: 1 7;
}

.login-left-view__nodes circle {
  fill: #8feaff;
  stroke: rgb(227 252 255 / 80%);
  stroke-width: 1.5;
  animation: login-node-breathe 5.5s ease-in-out infinite;
}

.login-left-view__nodes circle:nth-child(2n) {
  fill: #9b8aff;
  animation-delay: -1.8s;
}

.login-left-view__nodes circle:nth-child(3n) {
  animation-delay: -3.2s;
}

.login-left-view__core-halo {
  fill: rgb(111 151 255 / 8%);
  stroke: rgb(137 215 255 / 38%);
  stroke-width: 1;
  animation: login-core-breathe 7s ease-in-out infinite;
}

.login-left-view__core-halo--inner {
  fill: rgb(94 188 255 / 7%);
  stroke: rgb(184 157 255 / 35%);
  stroke-dasharray: 2 8;
  animation-delay: -2.5s;
}

.login-left-view__core-hex {
  fill: url("#login-core-gradient");
  fill-opacity: 0.72;
  stroke: url("#login-core-edge");
  stroke-width: 1.4;
}

.login-left-view__core-hex--inner {
  fill: rgb(147 231 255 / 17%);
  stroke: rgb(205 246 255 / 70%);
  stroke-width: 1;
}

.login-left-view__core-axis {
  stroke: rgb(228 251 255 / 65%);
  stroke-width: 1;
}

.login-left-view__core-dot {
  fill: url("#login-core-gradient");
  stroke: rgb(231 252 255 / 90%);
  stroke-width: 1.5;
}

.login-left-view__core-point {
  filter: drop-shadow(0 0 8px rgb(180 244 255 / 90%));
  fill: #fff;
}

.login-left-view__signal {
  position: absolute;
  box-sizing: border-box;
  display: flex;
  gap: 0.55rem;
  align-items: center;
  padding: 0.55rem 0.7rem;
  font-size: 0.63rem;
  font-weight: 600;
  color: rgb(222 238 255 / 72%);
  letter-spacing: 0.14em;
  background: rgb(9 19 53 / 46%);
  border: 1px solid rgb(165 196 255 / 18%);
  border-radius: 0.55rem;
  box-shadow: 0 12px 28px rgb(3 9 30 / 18%);
  backdrop-filter: blur(8px);
}

.login-left-view__signal--api {
  top: 19%;
  right: 7%;
}

.login-left-view__signal--data {
  bottom: 14%;
  left: 7%;
}

.login-left-view__signal--core {
  top: 47%;
  right: 26%;
  color: rgb(231 235 255 / 84%);
}

.login-left-view__signal--core b {
  color: #b5a2ff;
}

.login-left-view__copy {
  width: min(100%, 28rem);
}

.login-left-view__copy h2 {
  max-width: 28rem;
  margin: 0;
  font-size: clamp(1.55rem, 2.6vw, 2.2rem);
  font-weight: 600;
  line-height: 1.13;
  color: #f0f5ff;
  letter-spacing: -0.04em;
}

.login-left-view__subtitle {
  max-width: 25rem;
  margin: 0.9rem 0 0;
  font-size: 0.84rem;
  line-height: 1.65;
  color: rgb(211 225 255 / 62%);
}

@keyframes login-network-flow {
  to {
    stroke-dashoffset: -64;
  }
}

@keyframes login-node-breathe {
  0%,
  100% {
    opacity: 0.68;
    transform: scale(0.86);
    transform-origin: center;
  }

  50% {
    opacity: 1;
    transform: scale(1.14);
    transform-origin: center;
  }
}

@keyframes login-core-breathe {
  0%,
  100% {
    opacity: 0.66;
  }

  50% {
    opacity: 1;
  }
}

@media only screen and (width <= 1100px) {
  .login-left-view__content {
    padding-right: clamp(1.5rem, 3vw, 3rem);
    padding-left: clamp(1.5rem, 3vw, 3rem);
  }

  .login-left-view__art {
    height: clamp(18rem, 44vh, 29rem);
  }

  .login-left-view__signal--api,
  .login-left-view__signal--data {
    display: none;
  }
}

@media only screen and (width <= 900px) {
  .login-left-view__copy h2 {
    font-size: clamp(1.25rem, 2.8vw, 1.7rem);
  }

  .login-left-view__subtitle {
    max-width: 18rem;
    font-size: 0.74rem;
  }

  .login-left-view__signal--core {
    right: 18%;
  }
}

@media only screen and (width <= 767px) {
  .login-left-view {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .login-left-view__network-line--dashed,
  .login-left-view__nodes circle,
  .login-left-view__core-halo {
    animation: none;
  }
}

.dark .login-left-view {
  background:
    radial-gradient(circle at 20% 17%, rgb(91 105 255 / 19%) 0, transparent 30%),
    radial-gradient(circle at 84% 78%, rgb(37 183 255 / 11%) 0, transparent 28%),
    linear-gradient(135deg, #050a1d 0%, #0a1431 58%, #050a1b 100%);
}

.dark .login-left-view::after {
  background: linear-gradient(90deg, transparent, var(--login-workspace-bg, #080e1d) 96%);
}
</style>
