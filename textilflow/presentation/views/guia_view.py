from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTextBrowser, QVBoxLayout

from .. import theme
from ...version import FECHA, NOMBRE, SUBTITULO, VERSION
from ..widgets.common import PageView
from ..widgets.logo import logo_pixmap

def guia_html() -> str:
    return f"""
<style>
 h2 {{ color:{theme.DOC_TITULO}; margin-top:18px; }} h3 {{ color:{theme.DOC_ENLACE}; }} p, li {{ color:{theme.DOC_TEXTO}; line-height:150%; }}
 code {{ color:{theme.DOC_CODIGO}; }} td, th {{ padding:4px 10px; color:{theme.DOC_TEXTO}; }} th {{ color:{theme.DOC_TITULO}; text-align:left; }}
</style>
<h2>¿Para qué sirve TextilFlow?</h2>
<p>Es una herramienta de <b>optimización de procesos industriales</b> para talleres de confección. Responde, con datos y
simulación: ¿dónde se forman los cuellos de botella?, ¿cuántos equipos de transporte (operarios o robots AMR) hacen falta?,
¿cuántos viajes y cuántos metros se recorren?, ¿se respeta la prioridad de los pedidos? y ¿qué ganaría un robot frente
al transporte manual?</p>

<h2>Cómo funciona (de punta a punta)</h2>
<ol>
 <li><b>Taller y layout.</b> Se definen las áreas: un <b>Almacén</b> (inicio de todo lote) y un <b>Despacho</b> (fin), más las áreas de proceso
  (corte, costura, bordado, inspección, planchado, empaque…). Cada área tiene <i>minutos por unidad</i>, <i>puestos en paralelo</i> y, si hay
  varias equivalentes, un <i>grupo</i> (ej. COSTURA = Costura 1 + Costura 2). Los pasillos son conexiones con distancia y ancho.</li>
 <li><b>Prendas y rutas.</b> Cada tipo de prenda tiene peso, tamaño de lote y factor de dificultad. Cada prenda puede tener varias
  <b>ramas</b>: por ejemplo, 55 % pasa por <code>A&gt;C&gt;@COSTURA&gt;I&gt;P&gt;E&gt;D</code> y 30 % añade bordado
  <code>A&gt;C&gt;B&gt;@COSTURA&gt;…</code>. Así un mismo pedido se reparte entre varias áreas y todo llega a Despacho.</li>
 <li><b>Pedidos.</b> Prenda, cantidad, <b>prioridad</b> (1 = urgente), hora de llegada y fecha límite. Se parten en lotes.</li>
 <li><b>Escenarios y condiciones base.</b> Cuántos recursos, velocidad, capacidad por viaje, tiempos de carga/descarga, política
  (prioridad o FIFO), balanceo de grupos, demanda (% de los pedidos) y variabilidad de tiempos.</li>
 <li><b>Simulación de eventos discretos.</b> Los lotes avanzan por sus rutas; las áreas procesan en paralelo (hasta su número de puestos);
  cuando un lote termina pide transporte y el recurso libre más cercano lo lleva. Las colas, esperas, viajes y metros salen del propio
  comportamiento del sistema, no de promedios.</li>
 <li><b>Modelo matemático (<code>calculos.py</code>).</b> Con los traslados simulados se calculan los indicadores del estudio
  (tiempo de abastecimiento, distancia, espera, utilización, % atendidas) y la variación porcentual entre S0 y S1. Se complementa con la
  <b>carga ofrecida ρ</b> de cada área (analítica) para detectar cuellos antes de simular.</li>
</ol>

<h2>Dónde ver cada cosa</h2>
<table>
 <tr><th>Pregunta</th><th>Página</th></tr>
 <tr><td>¿Cuáles son los componentes críticos? ¿Qué distancias hay?</td><td><b>Requerimientos y normativas</b></td></tr>
 <tr><td>¿Cuántos equipos y cuántos viajes, según normas?</td><td><b>Requerimientos y normativas → Equipos y viajes / Normativa</b></td></tr>
 <tr><td>¿Qué ruta usará cada pedido? Pulse un área del mapa.</td><td><b>Mapa operativo</b></td></tr>
 <tr><td>¿Dónde hay más tránsito? (mapa de calor que crece con el tiempo)</td><td><b>Mapa operativo</b> y Dashboard</td></tr>
 <tr><td>¿Qué tan variable es el resultado? (N pruebas)</td><td><b>Escenarios y simulación → Réplicas</b></td></tr>
 <tr><td>¿Mejora el robot frente al manual?</td><td><b>Comparación experimental</b></td></tr>
 <tr><td>¿Se dañó una máquina o hay que cerrar un área? ¿Cómo se reorganiza todo?</td><td><b>Contingencias y cierres</b></td></tr>
 <tr><td>¿Qué falta o está mal?</td><td>Alertas (insignia superior) y <b>Validación integral</b></td></tr>
</table>

<h2>Cierre de áreas (contingencias)</h2>
<p>En <b>Contingencias y cierres</b> elija un área (por ejemplo <code>Costura 1</code>), el motivo y, si lo sabe, desde qué minuto
y hasta cuándo. Al guardar, TextilFlow <b>recalcula solo</b> las rutas y vuelve a simular todos los escenarios del taller:
el trabajo pasa a las áreas equivalentes abiertas, los pasillos por áreas cerradas se evitan y, si un paso queda sin ninguna
área disponible, esos lotes se marcan como no terminados con su motivo. Debajo del formulario, un mapa muestra el área afectada y la ruta de respaldo de cada prenda; «Generar informe (Excel)» guarda todas las contingencias con su fecha y hora. Las áreas cerradas se ven con
una ✕ roja en el mapa y el dashboard.</p>

<h2>Tema claro y oscuro</h2>
<p>El botón de la barra superior cambia entre tema claro y oscuro; la preferencia se recuerda.</p>

<h2>Límites que conviene conocer</h2>
<ul>
 <li>Los datos del ejemplo son <b>sintéticos</b>: sirven para validar el software, no son mediciones del taller.</li>
 <li>Las normas están en <b>Parámetros normativos</b> con su fuente y un indicador «verificado». Solo los valores marcados «Sí»
  fueron contrastados con el texto; el resto son criterios de diseño o citas secundarias que debe confirmar antes de citarlos.</li>
 <li>La factibilidad del robot por ancho es geométrica; no sustituye una evaluación de riesgos de seguridad.</li>
 <li>Los cierres son decisiones suyas (no averías aleatorias). Los lotes que ya estaban en la cola de un área cuando se cierra se quedan esperando a que reabra.</li>
 <li>El modelo no incluye baterías ni cruces entre recursos en un pasillo (se pueden agregar como extensión).</li>
</ul>
"""


class GuiaView(PageView):
    def __init__(self):
        super().__init__("Guía y acerca de TextilFlow",
                         "Qué hace el programa, cómo se usa y qué límites tiene.", theme.TURQUESA)
        cab = QFrame(); cab.setObjectName("tarjeta")
        cl = QHBoxLayout(cab)
        logo = QLabel()
        logo.setPixmap(logo_pixmap(84))
        cl.addWidget(logo)
        txt = QVBoxLayout()
        n = QLabel(f"{NOMBRE}  ·  versión {VERSION}")
        n.setStyleSheet("font-size: 22px; font-weight: 800;")
        txt.addWidget(n)
        txt.addWidget(QLabel(f"{SUBTITULO}  ·  compilación {FECHA}"))
        t2 = QLabel("Simulación de eventos discretos + modelo matemático (calculos.py) · PyQt6 · arquitectura limpia y MVC")
        t2.setObjectName("tenue")
        txt.addWidget(t2)
        cl.addLayout(txt, 1)
        self.cuerpo.addWidget(cab)
        self.texto = QTextBrowser()
        self.texto.setOpenExternalLinks(False)
        self.texto.setHtml(guia_html())
        self.texto.setStyleSheet(f"background: {theme.PANEL}; border: 1px solid {theme.BORDE}; border-radius: 10px; padding: 12px;")
        self.cuerpo.addWidget(self.texto, 1)
