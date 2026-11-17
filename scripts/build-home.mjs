import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import postcss from 'postcss';
import tailwindcss from 'tailwindcss';

const root = fileURLToPath(new URL('../', import.meta.url));
const read = (file) => readFile(path.join(root, file), 'utf8');
let html = await read('src/home.html');
const css = await postcss([tailwindcss({
  content: [{ raw: html, extension: 'html' }],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '"Noto Sans SC"', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        serif: ['"Noto Serif SC"', '"Songti SC"', 'Georgia', 'serif'],
      },
    },
  },
})]).process('@tailwind base;\n@tailwind components;\n@tailwind utilities;', { from: undefined });
html = html.replace('<!-- BUNDLED_STYLES -->', () => `<style>${css.css}</style>`);
for (const [token, file] of [
  ['BUNDLED_CHART', 'node_modules/chart.js/dist/chart.umd.js'],
  ['BUNDLED_ICONS', 'node_modules/lucide/dist/umd/lucide.min.js'],
]) {
  const js = (await read(file)).replace(/\/\/# sourceMappingURL=.*$/gm, '').replace(/<\/script/gi, '<\\/script');
  html = html.replace(`<!-- ${token} -->`, () => `<script>${js}</script>`);
}
const poster = await readFile(path.join(root, 'assets/guanlan-theme.png'));
html = html.replaceAll('assets/guanlan-theme.png', `data:image/png;base64,${poster.toString('base64')}`);
await writeFile(path.join(root, 'index.html'), html);
console.log(`Built standalone index.html (${Buffer.byteLength(html).toLocaleString()} bytes).`);
