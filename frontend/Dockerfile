# syntax=docker/dockerfile:1.7

# --- Builder: install deps and build the Next app ---------------------------
FROM node:22-alpine AS builder

ENV PNPM_HOME=/root/.local/share/pnpm \
    PATH=/root/.local/share/pnpm:$PATH

RUN corepack enable && corepack prepare pnpm@11.0.3 --activate

WORKDIR /app

# NEXT_PUBLIC_* values are baked into the client bundle by `next build`, so
# they have to be present at build time. Render passes Build Env Vars whose
# names match declared ARGs.
ARG NEXT_PUBLIC_API_BASE_URL=""
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build


# --- Runtime: only what `next start` needs ----------------------------------
FROM node:22-alpine AS runtime

ENV NODE_ENV=production \
    PORT=3000

RUN corepack enable && corepack prepare pnpm@11.0.3 --activate \
    && addgroup -S lusterko && adduser -S -G lusterko lusterko

WORKDIR /app

COPY --from=builder --chown=lusterko:lusterko /app/package.json /app/pnpm-lock.yaml /app/pnpm-workspace.yaml ./
COPY --from=builder --chown=lusterko:lusterko /app/node_modules ./node_modules
COPY --from=builder --chown=lusterko:lusterko /app/.next ./.next
COPY --from=builder --chown=lusterko:lusterko /app/next.config.mjs ./next.config.mjs

USER lusterko
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/ >/dev/null 2>&1 || exit 1

CMD ["pnpm", "start", "--port", "3000"]
