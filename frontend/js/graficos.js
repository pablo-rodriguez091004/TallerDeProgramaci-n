// frontend/js/graficos.js
// Gráficos en <canvas> sin librerías (requisito: frontend vanilla).
// - Nitidez en pantallas HiDPI (devicePixelRatio).
// - Se redibujan solos al cambiar el ancho (ResizeObserver).
// - Tooltip HTML al pasar el mouse (zona de impacto más grande que la barra).
// Los colores salen de variables CSS (--viz-*) definidas en styles.css.

function colorCss(nombre) {
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}

function prepararCanvas(canvas, altoCss) {
  const ancho = canvas.parentElement.clientWidth;
  const dpr = window.devicePixelRatio || 1;
  canvas.style.width = `${ancho}px`;
  canvas.style.height = `${altoCss}px`;
  canvas.width = Math.round(ancho * dpr);
  canvas.height = Math.round(altoCss * dpr);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, ancho, altoCss);
  ctx.font = `12px ${colorCss('--font-sans') || 'sans-serif'}`;
  ctx.textBaseline = 'middle';
  return { ctx, ancho, alto: altoCss };
}

// Rectángulo con las esquinas del extremo de datos redondeadas (4px) y la base recta.
function barraRedondeada(ctx, x, y, ancho, alto, radio = 4, redondearDerecha = true) {
  const r = Math.max(0, Math.min(radio, alto / 2, ancho));
  ctx.beginPath();
  if (redondearDerecha) {
    ctx.moveTo(x, y);
    ctx.lineTo(x + ancho - r, y);
    ctx.arcTo(x + ancho, y, x + ancho, y + r, r);
    ctx.lineTo(x + ancho, y + alto - r);
    ctx.arcTo(x + ancho, y + alto, x + ancho - r, y + alto, r);
    ctx.lineTo(x, y + alto);
  } else {
    ctx.rect(x, y, ancho, alto);
  }
  ctx.closePath();
  ctx.fill();
}

function niceMax(valor) {
  if (valor <= 0) return 1;
  const potencia = 10 ** Math.floor(Math.log10(valor));
  return [1, 2, 2.5, 5, 10].map(m => m * potencia).find(m => m >= valor);
}

// Conecta el tooltip una sola vez. Cada redibujo deja en canvas._buscar(x, y)
// una función que devuelve {html} o null para la posición del mouse.
function activarTooltip(canvas) {
  const tooltip = canvas.parentElement.querySelector('.grafico-tooltip');
  if (!tooltip || canvas.dataset.tooltip) return;
  canvas.dataset.tooltip = '1';
  canvas.addEventListener('mousemove', (evento) => {
    const caja = canvas.getBoundingClientRect();
    const x = evento.clientX - caja.left;
    const y = evento.clientY - caja.top;
    const encontrado = canvas._buscar?.(x, y);
    if (!encontrado) { tooltip.hidden = true; canvas.style.cursor = ''; return; }
    tooltip.innerHTML = encontrado.html;
    tooltip.hidden = false;
    canvas.style.cursor = 'default';
    const izquierda = Math.min(x + 14, caja.width - tooltip.offsetWidth - 4);
    tooltip.style.left = `${Math.max(4, izquierda)}px`;
    tooltip.style.top = `${Math.max(4, y - tooltip.offsetHeight - 10)}px`;
  });
  canvas.addEventListener('mouseleave', () => { tooltip.hidden = true; });
}

function redibujarAlCambiarTamano(canvas, dibujar) {
  if (canvas._observador) canvas._observador.disconnect();
  let anchoPrevio = 0;
  canvas._observador = new ResizeObserver(() => {
    const ancho = canvas.parentElement.clientWidth;
    if (ancho !== anchoPrevio) { anchoPrevio = ancho; dibujar(); }
  });
  canvas._observador.observe(canvas.parentElement);
}

/**
 * Barras horizontales ordenadas (una serie).
 * items: [{ etiqueta, valor, detalle }]; referencia: { valor, etiqueta } (línea vertical opcional).
 */
function graficoBarrasHorizontales(canvas, { items, referencia = null, formato = v => v, unidad = '' }) {
  const dibujar = () => {
    const altoFila = 22;
    const margen = { arriba: 28, abajo: 8, izquierda: 0, derecha: 64 };
    const alto = margen.arriba + margen.abajo + items.length * altoFila;
    const { ctx, ancho } = prepararCanvas(canvas, alto);

    ctx.font = `12px ${colorCss('--font-sans')}`;
    margen.izquierda = Math.min(220, Math.max(...items.map(i => ctx.measureText(i.etiqueta).width)) + 12);
    const anchoPlot = Math.max(40, ancho - margen.izquierda - margen.derecha);
    const maximo = niceMax(Math.max(...items.map(i => i.valor || 0), referencia?.valor || 0));
    const escala = v => margen.izquierda + (v / maximo) * anchoPlot;

    // Rejilla y eje (recesivos)
    ctx.strokeStyle = colorCss('--c-border');
    ctx.fillStyle = colorCss('--c-text-subtle');
    ctx.lineWidth = 1;
    ctx.textAlign = 'center';
    for (let i = 0; i <= 4; i++) {
      const valor = (maximo / 4) * i;
      const x = Math.round(escala(valor)) + 0.5;
      ctx.beginPath(); ctx.moveTo(x, margen.arriba - 6); ctx.lineTo(x, alto - margen.abajo); ctx.stroke();
      ctx.fillText(formato(valor), x, 10);
    }

    if (referencia) {
      const x = Math.round(escala(referencia.valor)) + 0.5;
      ctx.strokeStyle = colorCss('--c-text');
      ctx.setLineDash([4, 3]);
      ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(x, margen.arriba - 4); ctx.lineTo(x, alto - margen.abajo); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = colorCss('--c-text');
      ctx.textAlign = x > ancho - 120 ? 'right' : 'left';
      ctx.fillText(`${referencia.etiqueta}: ${formato(referencia.valor)}`, x + (ctx.textAlign === 'left' ? 4 : -4), 22);
    }

    const zonas = [];
    items.forEach((item, i) => {
      const y = margen.arriba + i * altoFila;
      ctx.textAlign = 'right';
      ctx.fillStyle = colorCss('--c-text-muted');
      ctx.fillText(item.etiqueta, margen.izquierda - 8, y + altoFila / 2);
      if (item.valor == null) {
        ctx.textAlign = 'left';
        ctx.fillStyle = colorCss('--c-text-subtle');
        ctx.fillText('sin datos', margen.izquierda + 4, y + altoFila / 2);
      } else {
        const anchoBarra = escala(item.valor) - margen.izquierda;
        ctx.fillStyle = colorCss('--viz-serie');
        barraRedondeada(ctx, margen.izquierda, y + 5, anchoBarra, altoFila - 10);
        // Valor con halo del color de la superficie para que la línea de referencia no lo tape.
        const texto = formato(item.valor);
        ctx.textAlign = 'left';
        ctx.lineWidth = 4;
        ctx.strokeStyle = colorCss('--c-surface');
        ctx.strokeText(texto, margen.izquierda + anchoBarra + 6, y + altoFila / 2);
        ctx.fillStyle = colorCss('--c-text-muted');
        ctx.fillText(texto, margen.izquierda + anchoBarra + 6, y + altoFila / 2);
      }
      zonas.push({ y0: y, y1: y + altoFila, item });
    });

    // La fila completa es zona de impacto (más grande que la barra).
    canvas._buscar = (x, y) => {
      const zona = zonas.find(z => y >= z.y0 && y < z.y1);
      if (!zona) return null;
      const { item } = zona;
      return { html: `<strong>${esc(item.etiqueta)}</strong><br>${item.valor == null ? 'sin datos' : `${esc(formato(item.valor))} ${esc(unidad)}`}`
        + (item.detalle ? `<br><span>${esc(item.detalle)}</span>` : '') };
    };
    activarTooltip(canvas);
  };
  dibujar();
  redibujarAlCambiarTamano(canvas, dibujar);
}

/**
 * Barras apiladas al 100 % (una barra por grupo, segmentos ordinales).
 * grupos: [{ etiqueta, segmentos: [{ clave, valor (porcentaje), detalle }] }]
 * colores: { clave: variableCss }
 */
function graficoApilado100(canvas, { grupos, orden, colores }) {
  const dibujar = () => {
    const altoFila = 40;
    const margen = { arriba: 22, abajo: 6, derecha: 24 };
    const alto = margen.arriba + margen.abajo + grupos.length * altoFila;
    const { ctx, ancho } = prepararCanvas(canvas, alto);
    ctx.font = `12px ${colorCss('--font-sans')}`;
    const izquierda = Math.max(...grupos.map(g => ctx.measureText(g.etiqueta).width)) + 14;
    const anchoPlot = Math.max(40, ancho - izquierda - margen.derecha);
    const separacion = 2; // hueco de superficie entre segmentos

    ctx.fillStyle = colorCss('--c-text-subtle');
    ctx.textAlign = 'center';
    [0, 25, 50, 75, 100].forEach(p => ctx.fillText(`${p} %`, izquierda + (p / 100) * anchoPlot, 9));

    const zonas = [];
    grupos.forEach((grupo, i) => {
      const y = margen.arriba + i * altoFila + 6;
      const altoBarra = altoFila - 12;
      ctx.textAlign = 'right';
      ctx.fillStyle = colorCss('--c-text-muted');
      ctx.fillText(grupo.etiqueta, izquierda - 10, y + altoBarra / 2);

      let x = izquierda;
      orden.forEach((clave, j) => {
        const segmento = grupo.segmentos.find(s => s.clave === clave);
        if (!segmento || !segmento.valor) return;
        const anchoSeg = (segmento.valor / 100) * anchoPlot;
        const ultimo = j === orden.length - 1;
        ctx.fillStyle = colorCss(colores[clave]);
        barraRedondeada(ctx, x, y, Math.max(0, anchoSeg - (ultimo ? 0 : separacion)), altoBarra, 4, ultimo);
        if (anchoSeg > 40) {
          // Texto con tinta de texto (no el color de la serie): blanco sobre los pasos oscuros.
          ctx.fillStyle = j >= 2 ? '#ffffff' : colorCss('--c-text');
          ctx.textAlign = 'center';
          ctx.fillText(`${segmento.valor.toFixed(0)} %`, x + anchoSeg / 2, y + altoBarra / 2);
        }
        zonas.push({ x0: x, x1: x + anchoSeg, y0: y - 4, y1: y + altoBarra + 4, grupo, segmento });
        x += anchoSeg;
      });
    });

    canvas._buscar = (mx, my) => {
      const zona = zonas.find(z => mx >= z.x0 && mx < z.x1 && my >= z.y0 && my < z.y1);
      if (!zona) return null;
      return { html: `<strong>${esc(zona.grupo.etiqueta)} · ${esc(zona.segmento.clave)} años</strong>`
        + `<br>${zona.segmento.valor.toFixed(1)} % del tipo<br><span>${esc(zona.segmento.detalle || '')}</span>` };
    };
    activarTooltip(canvas);
  };
  dibujar();
  redibujarAlCambiarTamano(canvas, dibujar);
}
