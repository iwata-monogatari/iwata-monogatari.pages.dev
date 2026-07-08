import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const footerPath = join(root, "partials", "footer.html");
const migrationPath = join(root, "migrations", "0001_site_fragments.sql");
const outPath = join(root, ".tmp", "seed_footer_fragment.sql");

function sqlString(value) {
  return "'" + value.replaceAll("'", "''") + "'";
}

const footerHtml = readFileSync(footerPath, "utf8");
const migrationSql = readFileSync(migrationPath, "utf8");

mkdirSync(dirname(outPath), { recursive: true });
writeFileSync(
  outPath,
  `${migrationSql}

INSERT INTO site_fragments (fragment_key, html, is_active, updated_at)
VALUES ('footer', ${sqlString(footerHtml)}, 1, CURRENT_TIMESTAMP)
ON CONFLICT(fragment_key) DO UPDATE SET
  html = excluded.html,
  is_active = 1,
  updated_at = CURRENT_TIMESTAMP;
`,
  "utf8"
);

console.log(outPath);
