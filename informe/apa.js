// Formato APA 7 compartido por los informes (mismo estilo que build_informe.js de la Guía 5):
// Times New Roman 12, carta, márgenes de 1", doble espacio, número de página arriba a la derecha,
// rótulos de tabla/figura en negrita + título en cursiva, notas a 10 pt y [[pendientes]] en amarillo.

const fs = require('fs');
const path = require('path');
const {
  AlignmentType, BorderStyle, Document, Footer, Header, HeadingLevel, ImageRun, LevelFormat,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} = require('docx');

const FONT = 'Times New Roman';
const MONO = 'Consolas';
const PAGE_W = 12240; // Carta
const MARGIN = 1440; // 1 pulgada
const CONTENT_W = PAGE_W - 2 * MARGIN; // 9360 DXA = 6.5 in
const CONTENT_PX = 624; // 6.5 in a 96 px/in
const DOUBLE = 480;
const SINGLE = 240;

// Texto con marcas simples: **negrita**, *cursiva*, `codigo`, [[PENDIENTE]] (resaltado).
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[\[[^\]]+\]\])/g;
  let last = 0;
  let m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith('**')) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    // Sombreado amarillo en vez de `highlight`: docx 9.7 emite <w:highlightCs>, que no valida contra el esquema.
    else if (t.startsWith('[[')) out.push(new TextRun({ text: t.slice(2, -2), shading: { type: ShadingType.CLEAR, fill: 'FFFF00', color: 'auto' }, bold: true, ...base }));
    else if (t.startsWith('*')) out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), font: MONO, size: (base.size || 24) - 2, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}

const p = (text, opts = {}) => new Paragraph({
  children: runs(text), spacing: { line: DOUBLE, before: 0, after: 0 }, indent: { firstLine: 720 }, ...opts,
});
const plain = (text, opts = {}) => p(text, { indent: {}, ...opts });
const center = (text, opts = {}) => p(text, { indent: {}, alignment: AlignmentType.CENTER, ...opts });
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
const h3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(text)] });
const bullet = (text) => new Paragraph({
  children: runs(text), numbering: { reference: 'bullets', level: 0 }, spacing: { line: DOUBLE },
});
const numbered = (text, ref = 'numbers') => new Paragraph({
  children: runs(text), numbering: { reference: ref, level: 0 }, spacing: { line: DOUBLE },
});
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

function code(text, size = 16) {
  return text.split('\n').map((line, i, all) => new Paragraph({
    children: [new TextRun({ text: line || ' ', font: MONO, size })],
    spacing: { line: SINGLE, before: i === 0 ? 120 : 0, after: i === all.length - 1 ? 240 : 0 },
    shading: { type: ShadingType.CLEAR, fill: 'F2F2F2', color: 'auto' },
    indent: { left: 144, right: 144 },
  }));
}

// Numeración automática de tablas y figuras: el contenido se arma dos veces; la primera
// pasada registra el número de cada tabla (por título) y figura (por archivo).
function numbering() {
  const labels = {};
  let tableNo = 0;
  let figureNo = 0;

  function apaLabel(kind, n, title) {
    return [
      new Paragraph({ children: [new TextRun({ text: `${kind} ${n}`, bold: true })], spacing: { before: 240, line: DOUBLE }, keepNext: true }),
      new Paragraph({ children: [new TextRun({ text: title, italics: true })], spacing: { line: DOUBLE }, keepNext: true }),
    ];
  }
  const note = (text) => new Paragraph({
    children: [new TextRun({ text: 'Nota. ', italics: true, size: 20 }), ...runs(text, { size: 20 })],
    spacing: { line: SINGLE, before: 80, after: 240 },
  });

  function table(title, headers, rows, widths, { size = 18, notes } = {}) {
    const total = widths.reduce((a, b) => a + b, 0);
    if (total !== CONTENT_W) throw new Error(`Las columnas de "${title}" suman ${total}, no ${CONTENT_W}`);
    const border = { style: BorderStyle.SINGLE, size: 4, color: '999999' };
    const cell = (text, w, header) => new TableCell({
      width: { size: w, type: WidthType.DXA },
      margins: { top: 40, bottom: 40, left: 80, right: 80 },
      shading: header ? { type: ShadingType.CLEAR, fill: 'D9E2F3', color: 'auto' } : undefined,
      borders: { top: border, bottom: border, left: border, right: border },
      children: String(text).split('\n').map((line) => new Paragraph({
        children: runs(line, { size, bold: header || undefined }), spacing: { line: SINGLE },
      })),
    });
    tableNo += 1;
    labels[`T:${title}`] = tableNo;
    return [
      ...apaLabel('Tabla', tableNo, title),
      new Table({
        width: { size: CONTENT_W, type: WidthType.DXA },
        columnWidths: widths,
        rows: [
          new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], true)) }),
          ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, widths[i], false)) })),
        ],
      }),
      ...(notes ? [note(notes)] : [new Paragraph({ spacing: { after: 240 }, children: [] })]),
    ];
  }

  function pngSize(file) {
    const buf = fs.readFileSync(file);
    return { buf, w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
  }

  // 650 px (~6,8 in) deja espacio en la página de 9 in para el rótulo APA de dos líneas y la nota.
  function figure(file, title, notes, maxHeightPx = 650) {
    const { buf, w, h } = pngSize(file);
    const scale = Math.min(CONTENT_PX / w, maxHeightPx / h);
    figureNo += 1;
    labels[`F:${path.basename(file)}`] = figureNo;
    return [
      ...apaLabel('Figura', figureNo, title),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        keepNext: !!notes,
        children: [new ImageRun({
          type: 'png', data: buf,
          transformation: { width: Math.round(w * scale), height: Math.round(h * scale) },
          altText: { title, description: title, name: path.basename(file) },
        })],
      }),
      ...(notes ? [note(notes)] : []),
    ];
  }

  return {
    table, figure, note,
    tab: (title) => labels[`T:${title}`] ?? '?',
    fig: (file) => labels[`F:${file}`] ?? '?',
    reset: () => { tableNo = 0; figureNo = 0; },
    counts: () => ({ tables: tableNo, figures: figureNo }),
  };
}

function apaDocument({ title, description, children }) {
  return new Document({
    creator: 'MecaTrack',
    title,
    description,
    styles: {
      default: { document: { run: { font: FONT, size: 24 } } },
      paragraphStyles: [
        { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { font: FONT, size: 24, bold: true, color: '000000' },
          paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 240, after: 0, line: DOUBLE }, outlineLevel: 0, keepNext: true } },
        { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { font: FONT, size: 24, bold: true, color: '000000' },
          paragraph: { spacing: { before: 120, after: 0, line: DOUBLE }, outlineLevel: 1, keepNext: true } },
        { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { font: FONT, size: 24, bold: true, italics: true, color: '000000' },
          paragraph: { spacing: { before: 120, after: 0, line: DOUBLE }, outlineLevel: 2, keepNext: true } },
      ],
    },
    numbering: {
      config: [
        { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: 'numbers', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      ],
    },
    sections: [{
      properties: { page: { size: { width: PAGE_W, height: 15840 }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ children: [PageNumber.CURRENT] })] })] }) },
      footers: { default: new Footer({ children: [] }) },
      children,
    }],
  });
}

const reference = (text) => new Paragraph({ children: runs(text), spacing: { line: DOUBLE }, indent: { left: 720, hanging: 720 } });

module.exports = {
  CONTENT_W, DOUBLE, runs, p, plain, center, h1, h2, h3, bullet, numbered, pageBreak, code,
  numbering, apaDocument, reference, Paragraph, TextRun, AlignmentType,
};
