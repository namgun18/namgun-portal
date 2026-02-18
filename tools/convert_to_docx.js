const fs = require("fs");
const path = require("path");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  Table,
  TableRow,
  TableCell,
  TableLayoutType,
  WidthType,
  BorderStyle,
  AlignmentType,
  ShadingType,
  LevelFormat,
  convertInchesToTwip,
  PageBreak,
  Spacing,
} = require("docx");

// ─── Markdown Parser ───────────────────────────────────────────────

/**
 * Parse inline markdown formatting (bold, inline code) into TextRun objects.
 * Handles: **bold**, `inline code`, and plain text.
 */
function parseInlineMarkdown(text, baseStyle = {}) {
  const runs = [];
  // Pattern matches **bold** or `code` segments
  const regex = /(\*\*(.+?)\*\*|`([^`]+)`)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Add plain text before this match
    if (match.index > lastIndex) {
      const plain = text.substring(lastIndex, match.index);
      if (plain) {
        runs.push(new TextRun({ text: plain, font: baseStyle.font || "Malgun Gothic", size: baseStyle.size || 20 }));
      }
    }

    if (match[2]) {
      // **bold**
      runs.push(new TextRun({
        text: match[2],
        bold: true,
        font: baseStyle.font || "Malgun Gothic",
        size: baseStyle.size || 20,
      }));
    } else if (match[3]) {
      // `inline code`
      runs.push(new TextRun({
        text: match[3],
        font: "Consolas",
        size: baseStyle.size || 20,
        shading: { type: ShadingType.CLEAR, color: "auto", fill: "E8E8E8" },
      }));
    }

    lastIndex = match.index + match[0].length;
  }

  // Remaining plain text
  if (lastIndex < text.length) {
    const remaining = text.substring(lastIndex);
    if (remaining) {
      runs.push(new TextRun({ text: remaining, font: baseStyle.font || "Malgun Gothic", size: baseStyle.size || 20 }));
    }
  }

  if (runs.length === 0) {
    runs.push(new TextRun({ text: text || "", font: baseStyle.font || "Malgun Gothic", size: baseStyle.size || 20 }));
  }

  return runs;
}

/**
 * Parse a markdown table (array of lines starting with |) into a Table object.
 */
function parseTable(tableLines) {
  // Filter out separator lines (|---|---|)
  const dataLines = tableLines.filter(line => !line.match(/^\|[\s\-:|]+\|$/));

  if (dataLines.length === 0) return null;

  const rows = dataLines.map((line, rowIndex) => {
    const cells = line
      .split("|")
      .slice(1, -1) // remove first and last empty elements
      .map(cell => cell.trim());

    return new TableRow({
      children: cells.map(cellText => {
        return new TableCell({
          children: [
            new Paragraph({
              children: parseInlineMarkdown(cellText, { size: 18 }),
              spacing: { before: 40, after: 40 },
            }),
          ],
          shading: rowIndex === 0
            ? { type: ShadingType.CLEAR, color: "auto", fill: "D9E2F3" }
            : undefined,
          margins: { top: 40, bottom: 40, left: 80, right: 80 },
        });
      }),
    });
  });

  return new Table({
    rows: rows,
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.AUTOFIT,
  });
}

/**
 * Parse a code block (array of lines) into styled Paragraphs.
 */
function parseCodeBlock(codeLines, language) {
  const paragraphs = [];
  for (const line of codeLines) {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: line || " ",
            font: "Consolas",
            size: 16,
          }),
        ],
        shading: { type: ShadingType.CLEAR, color: "auto", fill: "F2F2F2" },
        spacing: { before: 0, after: 0, line: 276 },
        indent: { left: convertInchesToTwip(0.2) },
      })
    );
  }
  return paragraphs;
}

/**
 * Parse a checkbox line (- [ ] or - [x]) into a Paragraph.
 */
function parseCheckboxLine(text, checked) {
  const symbol = checked ? "\u2611" : "\u2610"; // ballot box with/without check
  const cleanText = text.replace(/^-\s*\[[ x]\]\s*/, "");
  return new Paragraph({
    children: [
      new TextRun({
        text: symbol + " ",
        font: "Segoe UI Symbol",
        size: 20,
      }),
      ...parseInlineMarkdown(cleanText),
    ],
    indent: { left: convertInchesToTwip(0.3) },
    spacing: { before: 40, after: 40 },
  });
}

/**
 * Parse a bullet list item into a Paragraph.
 */
function parseBulletItem(text, level = 0) {
  const cleanText = text.replace(/^[-*]\s+/, "");
  const bulletChar = level === 0 ? "\u2022" : "\u25E6";
  return new Paragraph({
    children: [
      new TextRun({
        text: bulletChar + "  ",
        font: "Malgun Gothic",
        size: 20,
      }),
      ...parseInlineMarkdown(cleanText),
    ],
    indent: { left: convertInchesToTwip(0.3 + level * 0.3) },
    spacing: { before: 40, after: 40 },
  });
}

/**
 * Parse a numbered list item into a Paragraph.
 */
function parseNumberedItem(text, number) {
  const cleanText = text.replace(/^\d+\.\s+/, "");
  return new Paragraph({
    children: [
      new TextRun({
        text: `${number}. `,
        font: "Malgun Gothic",
        size: 20,
        bold: false,
      }),
      ...parseInlineMarkdown(cleanText),
    ],
    indent: { left: convertInchesToTwip(0.3) },
    spacing: { before: 40, after: 40 },
  });
}

/**
 * Parse a blockquote line (> text) into a styled Paragraph.
 */
function parseBlockquote(text) {
  const cleanText = text.replace(/^>\s*/, "");
  return new Paragraph({
    children: parseInlineMarkdown(cleanText),
    indent: { left: convertInchesToTwip(0.4) },
    border: {
      left: { style: BorderStyle.SINGLE, size: 6, color: "999999", space: 8 },
    },
    shading: { type: ShadingType.CLEAR, color: "auto", fill: "F9F9F9" },
    spacing: { before: 80, after: 80 },
  });
}

// ─── Main Converter ────────────────────────────────────────────────

/**
 * Convert a markdown string to an array of docx children (Paragraphs, Tables).
 */
function markdownToDocxChildren(markdown) {
  const lines = markdown.split("\n");
  const children = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // ── Code block ──
    if (line.trimStart().startsWith("```")) {
      const language = line.trim().replace(/^```/, "").trim();
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].trimStart().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      // Add a small spacing before code block
      children.push(new Paragraph({ spacing: { before: 80, after: 0 }, children: [] }));
      children.push(...parseCodeBlock(codeLines, language));
      children.push(new Paragraph({ spacing: { before: 0, after: 80 }, children: [] }));
      i++; // skip closing ```
      continue;
    }

    // ── Horizontal rule (---) ──
    if (line.match(/^---+\s*$/) || line.match(/^\*\*\*+\s*$/)) {
      children.push(
        new Paragraph({
          spacing: { before: 200, after: 200 },
          border: {
            bottom: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC", space: 4 },
          },
          children: [],
        })
      );
      i++;
      continue;
    }

    // ── Heading ──
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const text = headingMatch[2];
      const headingLevelMap = {
        1: HeadingLevel.HEADING_1,
        2: HeadingLevel.HEADING_2,
        3: HeadingLevel.HEADING_3,
        4: HeadingLevel.HEADING_4,
        5: HeadingLevel.HEADING_5,
        6: HeadingLevel.HEADING_6,
      };
      const sizeMap = { 1: 32, 2: 28, 3: 24, 4: 22, 5: 20, 6: 20 };

      children.push(
        new Paragraph({
          heading: headingLevelMap[level],
          children: parseInlineMarkdown(text, { size: sizeMap[level] }),
          spacing: { before: level <= 2 ? 360 : 240, after: 120 },
        })
      );
      i++;
      continue;
    }

    // ── Table ──
    if (line.trimStart().startsWith("|")) {
      const tableLines = [];
      while (i < lines.length && lines[i].trimStart().startsWith("|")) {
        tableLines.push(lines[i]);
        i++;
      }
      const table = parseTable(tableLines);
      if (table) {
        children.push(table);
        children.push(new Paragraph({ spacing: { before: 80, after: 80 }, children: [] }));
      }
      continue;
    }

    // ── Checkbox ──
    if (line.match(/^-\s*\[[ x]\]/)) {
      const checked = line.match(/^-\s*\[x\]/) !== null;
      children.push(parseCheckboxLine(line, checked));
      i++;
      continue;
    }

    // ── Bullet list ──
    if (line.match(/^\s*[-*]\s+/)) {
      const indentMatch = line.match(/^(\s*)/);
      const indent = indentMatch ? indentMatch[1].length : 0;
      const level = indent >= 2 ? 1 : 0;
      children.push(parseBulletItem(line.trimStart(), level));
      i++;
      continue;
    }

    // ── Numbered list ──
    const numberedMatch = line.match(/^(\d+)\.\s+(.+)/);
    if (numberedMatch) {
      children.push(parseNumberedItem(line, parseInt(numberedMatch[1])));
      i++;
      continue;
    }

    // ── Blockquote ──
    if (line.trimStart().startsWith(">")) {
      children.push(parseBlockquote(line));
      i++;
      continue;
    }

    // ── Italic / emphasis line (e.g., *End of document*) ──
    const italicMatch = line.match(/^\*([^*]+)\*$/);
    if (italicMatch) {
      children.push(
        new Paragraph({
          children: [
            new TextRun({
              text: italicMatch[1],
              italics: true,
              font: "Malgun Gothic",
              size: 18,
              color: "666666",
            }),
          ],
          spacing: { before: 120, after: 120 },
        })
      );
      i++;
      continue;
    }

    // ── Empty line ──
    if (line.trim() === "") {
      i++;
      continue;
    }

    // ── Plain paragraph ──
    children.push(
      new Paragraph({
        children: parseInlineMarkdown(line),
        spacing: { before: 60, after: 60 },
      })
    );
    i++;
  }

  return children;
}

/**
 * Convert a markdown file to a docx Document object.
 */
function convertMarkdownToDocx(markdownContent, title, creator) {
  const docChildren = markdownToDocxChildren(markdownContent);

  const doc = new Document({
    creator: creator,
    title: title,
    description: title,
    styles: {
      default: {
        document: {
          run: {
            font: "Malgun Gothic",
            size: 20,
          },
        },
        heading1: {
          run: {
            font: "Malgun Gothic",
            size: 32,
            bold: true,
            color: "1F3864",
          },
          paragraph: {
            spacing: { before: 360, after: 120 },
          },
        },
        heading2: {
          run: {
            font: "Malgun Gothic",
            size: 28,
            bold: true,
            color: "2E75B6",
          },
          paragraph: {
            spacing: { before: 300, after: 100 },
          },
        },
        heading3: {
          run: {
            font: "Malgun Gothic",
            size: 24,
            bold: true,
            color: "404040",
          },
          paragraph: {
            spacing: { before: 240, after: 80 },
          },
        },
        heading4: {
          run: {
            font: "Malgun Gothic",
            size: 22,
            bold: true,
            color: "404040",
          },
          paragraph: {
            spacing: { before: 200, after: 80 },
          },
        },
      },
    },
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: convertInchesToTwip(1),
              bottom: convertInchesToTwip(1),
              left: convertInchesToTwip(1),
              right: convertInchesToTwip(1),
            },
          },
        },
        children: docChildren,
      },
    ],
  });

  return doc;
}

// ─── File Processing ───────────────────────────────────────────────

async function processFile(inputPath, outputPath, title) {
  console.log(`Converting: ${path.basename(inputPath)} -> ${path.basename(outputPath)}`);

  const markdown = fs.readFileSync(inputPath, "utf-8");
  const doc = convertMarkdownToDocx(markdown, title, "남기완");

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);

  const stats = fs.statSync(outputPath);
  console.log(`  Output: ${outputPath} (${(stats.size / 1024).toFixed(1)} KB)`);
}

async function main() {
  const baseDir = "/mnt/d/Docker/namgun-portal";

  const files = [
    {
      input: path.join(baseDir, "docs/progress/project_progress_ko.md"),
      output: path.join(baseDir, "docs/progress/project_progress_ko.docx"),
      title: "namgun.or.kr 종합 포털 SSO 통합 플랫폼 - 프로젝트 진행 보고서",
    },
    {
      input: path.join(baseDir, "docs/progress/project_progress_en.md"),
      output: path.join(baseDir, "docs/progress/project_progress_en.docx"),
      title: "namgun.or.kr Integrated Portal SSO Platform - Project Progress Report",
    },
    {
      input: path.join(baseDir, "docs/phase2/phase2_mail_migration_ko.md"),
      output: path.join(baseDir, "docs/phase2/phase2_mail_migration_ko.docx"),
      title: "Phase 2: iRedMail → Stalwart Mail Server 마이그레이션",
    },
    {
      input: path.join(baseDir, "docs/phase2/phase2_mail_migration_en.md"),
      output: path.join(baseDir, "docs/phase2/phase2_mail_migration_en.docx"),
      title: "Phase 2: iRedMail to Stalwart Mail Server Migration",
    },
  ];

  console.log("=== Markdown to DOCX Converter ===\n");

  for (const file of files) {
    if (!fs.existsSync(file.input)) {
      console.error(`  SKIP: ${file.input} not found`);
      continue;
    }
    await processFile(file.input, file.output, file.title);
  }

  console.log("\nDone. All files converted.");
}

main().catch(err => {
  console.error("Error:", err);
  process.exit(1);
});
