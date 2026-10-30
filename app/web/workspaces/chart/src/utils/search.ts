export function fuzzy(query: string, text: string): boolean {
  let i = 0;
  const q = query.toLowerCase().replace(/\s/g, '');
  for (const c of text.toLowerCase()) if (c === q[i]) i++;
  return i === q.length;
}
