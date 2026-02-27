# Chuscraper Documentation Website 🕷️

This is the source code for the official documentation of **Chuscraper**, an industry-leading stealth browser automation and universal crawling framework.

The documentation is built using [Docusaurus 2](https://docusaurus.io/), a modern static website generator.

## Project Structure

- `docs/` - Contains the Markdown (`.md`) files that make up the documentation pages.
- `src/` - Contains React components, such as the homepage (`pages/index.js`).
- `static/` - Static assets like images (e.g., logo).
- `sidebars.js` - Configuration file to define the documentation sidebar navigation structure.
- `docusaurus.config.js` - Docusaurus site configuration (theme, title, plugins).

## Local Development

To run the documentation site locally and see your changes live:

1. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

2. Start the development server:
   ```bash
   npm run start
   # or
   yarn start
   ```

This command starts a local development server (typically on `http://localhost:3000`) and opens up a browser window. Most changes inside the `docs/` directory will be reflected live without having to restart the server.

## Building for Production

To generate the static HTML files ready for deployment:

```bash
npm run build
# or
yarn build
```

This generates static content into the `build` directory, which can be served using any static hosting service like GitHub Pages, Vercel, or Netlify.

## Updating the Docs

When a new feature (like the **Universal Crawler** or **Local Ollama Extraction**) is added to the backend, ensure you:
1. Write the corresponding Markdown guide in `docs/`.
2. Add the filename hook to `sidebars.js`.
3. Check for any broken links before committing.
