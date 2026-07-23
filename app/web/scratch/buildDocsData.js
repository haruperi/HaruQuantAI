import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const baseDir = path.join(__dirname, '..', 'docs', 'education');
const categories = ['fundamentals', 'development', 'robustness'];
const result = [];

categories.forEach((cat) => {
  const catDir = path.join(baseDir, cat);
  if (!fs.existsSync(catDir)) return;
  const files = fs.readdirSync(catDir).filter((f) => f.endsWith('.md'));

  files.forEach((file) => {
    const filePath = path.join(catDir, file);
    const content = fs.readFileSync(filePath, 'utf8');
    const slug = file.replace('.md', '');

    const lines = content.split('\n').map((l) => l.trim()).filter(Boolean);
    let title = slug.split('-').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    let description = '';

    for (let l of lines) {
      if (l.startsWith('#')) {
        title = l.replace(/^#+\s*/, '').trim();
        break;
      }
    }

    for (let l of lines) {
      if (!description && l.length > 20 && !l.startsWith('-') && !l.startsWith('*') && !l.startsWith('#')) {
        description = l.slice(0, 160) + '...';
        break;
      }
    }

    const catCap = cat.charAt(0).toUpperCase() + cat.slice(1);
    result.push({
      id: `${cat}-${slug}`,
      title,
      category: catCap,
      slug,
      filePath: `docs/education/${cat}/${file}`,
      description: description || 'Comprehensive guide and documentation.',
      content
    });
  });
});

const fileContent = `export const docsData = ${JSON.stringify(result, null, 2)};\n`;
fs.writeFileSync(path.join(__dirname, '..', 'src', 'mock', 'docsData.js'), fileContent);
console.log('Successfully generated docsData.js with', result.length, 'documents');
