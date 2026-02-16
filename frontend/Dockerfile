# ── Development Dockerfile (Vite) ─────────────────────────────────────────────
# docker-compose mounts ./frontend:/app as a live volume.
# node_modules live in a named Docker volume (frontend_nm) so the host
# bind-mount doesn't wipe them.
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine

WORKDIR /app

# Copy manifests first for layer caching
COPY package*.json ./

# Install deps into the image layer.
# At runtime the named volume takes over /app/node_modules,
# but npm install in CMD keeps it up to date.
RUN npm install

ENV PATH=/app/node_modules/.bin:$PATH

EXPOSE 3000

# Install any new packages added since image was built, then start Vite.
CMD ["sh", "-c", "npm install && npm run dev"]