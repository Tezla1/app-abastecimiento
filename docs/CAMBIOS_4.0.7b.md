# TextilFlow 4.0.7b (beta) · qué cambió y cómo funciona

Versión beta sobre la 4.0.7. Los tiempos de abajo se midieron en un equipo de pruebas sin pantalla real (no es Windows);
en un PC real los números cambian, pero la mejora relativa es la que importa. **El `.exe` no se pudo compilar ni probar aquí**
(hay que generarlo en Windows con `construir_exe.bat`).

## Resumen en una tabla

| # | Tema | Resultado |
|---|------|-----------|
| 1 | Ventana de error con descripción | Un error ya no cierra el programa: sale un cuadro que dice qué pasó, dónde y qué hacer, y queda en un archivo de registro |
| 2 | Operaciones largas en segundo plano | Réplicas, análisis de flota y recálculo de cierres con barra de progreso y botón Cancelar |
| 3 | Fallo al abrir la base de datos | Mensaje claro, opción de empezar con una base nueva (la dañada se conserva) y una sola ventana abierta a la vez |
| 4 | Animación del mapa | Se pausa sola al salir de la página, usa menos procesador |
| 5 | Aviso de migración | El aviso de base antigua se ve en pantalla (antes solo en consola) |
| 6 | Guardar al cerrar + respaldos | Pregunta «¿Guardar el proyecto?» como Word; 3 respaldos automáticos; recuperación tras un apagado inesperado |
| 7 | Velocidad en PCs humildes | Abre ~4 veces más rápido, cambio de tema ~20 veces más rápido |
| 8 | Errores ya no se tragan en silencio | Los 4 sitios que ignoraban errores ahora los registran |
| 9 | Tamaño y posición de la ventana | Se recuerdan entre sesiones |
| 10 | Pantallas pequeñas | Las páginas pasan de filas a columnas; sin desplazamiento lateral desde 800 px |
| 11 | **Bug**: área cerrada seguía dejando pasar el flujo | Corregido |
| + | Diálogos ilegibles en tema oscuro | Corregido (descubierto durante el trabajo) |

Mediciones (equipo de pruebas, ventana ya con datos de demostración):

| | 4.0.5 | 4.0.7b |
|---|---|---|
| Abrir la ventana con datos | 1,0 s | 0,25 s |
| Cambiar de tema | 1,8 s | 0,08 s |
| Simulaciones reales al abrir (el resto sale de la caché) | 10 | 2 |

---

## 11 · Bug: el Mapa operativo dejaba pasar el flujo por un área cerrada

**Qué pasaba.** El motor de simulación sí respeta los cierres (con el área cerrada y «Bloquea el paso» marcado, cero
movimientos tocan esa área). El fallo estaba en el mapa: mantenía en pantalla la animación que se había simulado *antes* de
cerrar el área. Al cerrar «Corte» en Contingencias y volver al mapa, se seguía viendo el recorrido viejo pasando por Corte.

**Qué se hizo.** `MapaController` ahora se entera cuando cambian los cierres (`ctx.cierres_cambiaron`) y, además, compara
las áreas cerradas actuales con las que había al simular. Al volver al mapa, si no coinciden, vuelve a simular el mismo
escenario y avisa: «Los cierres cambiaron: se simuló de nuevo el escenario.».

**Importante.** Si un cierre tiene desmarcado «Bloquea el paso», el área deja de *procesar* pero los traslados todavía
pueden *atravesarla* (así está definido el modelo). Para que nada pase por ella, el cierre debe tener «Bloquea el paso».

Prueba: `test_mapa_operativo_respeta_un_area_cerrada_despues_de_simular`.

## 1 y 8 · Ventana de error con descripción

**Qué pasaba.** En PyQt6, una excepción que se escapa de un botón o señal aborta el programa sin mensaje. Con el `.exe`
(`--windowed`) no hay consola: el programa simplemente desaparecía.

**Qué hace ahora.** `main.py` instala un manejador global (`presentation/errores.py`). Ante un error muestra un cuadro con:

- **Título** y **qué pasó** en lenguaje claro (por ejemplo «Cálculo imposible: una fórmula intentó dividir por cero…»).
- **Dónde:** archivo · función (línea) del propio programa donde ocurrió.
- **Qué hacer.**
- Botón **Detalles** con el error técnico completo, **Copiar detalle** (listo para pegar en un reporte, con versión y
  sistema), **Abrir carpeta del registro**, **Continuar** y **Cerrar programa**.

El mismo error repetido en menos de 2 segundos no abre otro cuadro (por ejemplo, dentro de un temporizador).
Todo queda en `~/.textilflow/textilflow.log` (rota a 512 KB, guarda 2 copias).

Las traducciones a lenguaje claro están en `textilflow/registro.py` (`describir`): base de datos bloqueada o solo lectura,
disco lleno, violación de integridad, permisos, archivo no encontrado, memoria, división por cero, datos faltantes, etc.
Los 4 bloques `except Exception` que ignoraban errores (alertas, recálculo de cierres, rutas del informe, Data Manager) ahora
los registran con `registro.registrar(...)`.

Pruebas: `test_error_no_controlado_muestra_cuadro_y_no_cierra`, `test_descripcion_clara_de_errores`.

## 2 · Operaciones largas con barra de progreso y Cancelar

**Qué pasaba.** Réplicas, análisis de flota y recálculo de escenarios corrían en el hilo de la ventana; mientras duraban,
Windows mostraba «no responde».

**Qué hace ahora** (`presentation/tareas.py`):

- Corren en un hilo aparte. Aparece un diálogo con barra de progreso («Réplica 12 de 30») y **Cancelar**.
- El diálogo solo aparece si la tarea dura más de 0,4 s; las rápidas no parpadean.
- Mientras corre, el diálogo bloquea el resto de la ventana: nadie toca la base de datos al mismo tiempo que el hilo.
  Por eso la conexión se abrió con `check_same_thread=False`.
- Un error de negocio llega al cuadro normal; uno inesperado va al manejador global (punto 1).
- Se aplica a: **réplicas** (`EjecutarReplicas`), **requerimientos/barrido de flota** (`AnalizarRequerimientos`) y
  **recálculo tras cambiar cierres** (`ContingenciasController._recalcular`). Los casos de uso reciben un parámetro
  opcional `progreso` (`application/progreso.py`) que informa avance y lanza `Cancelado`.

**Cómo probarlo.** En «Escenarios y simulación → Réplicas» pida 500 réplicas y pulse Cancelar.

**Límite.** Python comparte el procesador entre hilos (GIL): la ventana sigue respondiendo pero la tarea no es más rápida.

Pruebas: `test_tarea_en_segundo_plano_con_progreso_y_cancelar`, `test_replicas_reales_en_hilo_dan_el_mismo_resultado_que_en_linea`.
En las pruebas automáticas las tareas corren en línea (`TEXTILFLOW_SINCRONO=1`).

## 3 y 5 · Arranque seguro y avisos

`presentation/arranque.py`:

- **Una sola ventana.** Un archivo de bloqueo (`textilflow.lock`, `QLockFile`) impide abrir dos TextilFlow sobre los mismos
  datos. Si el programa anterior murió, el bloqueo se detecta como caducado.
- **Base dañada o inaccesible.** Si falla al abrir (archivo corrupto, sin permisos, carpeta inexistente) o la verificación
  `PRAGMA quick_check` falla, sale un cuadro que explica el motivo y ofrece **Empezar con una base nueva** (la dañada se
  guarda como `*.AAAAMMDD_HHMMSS.danada.bak`, no se borra), **Abrir carpeta de datos** o **Salir**.
- **Aviso de migración (punto 5).** Si había una base de la versión 1 (esquema incompatible), el programa la mueve a un
  respaldo `.v1.bak` y crea una nueva. Antes lo avisaba por consola (invisible en el `.exe`); ahora sale un cuadro con la
  ruta del respaldo.

Prueba: `test_base_danada_ofrece_empezar_de_nuevo_y_conserva_copia`.

## 6 · Guardar al cerrar (como Word) y respaldos automáticos

**Detección de cambios.** `Database.cambios_sin_guardar()` usa el contador de SQLite (`total_changes`) comparado con la
marca de la última vez que se guardó un proyecto o se abrió el programa.

**Al cerrar la ventana**, si hubo cambios, pregunta:

- **Guardar como…** → crea un archivo `.rlr` con el nombre que elija (el mismo formato de «Exportar proyecto» de Data Manager;
  se escribe a un archivo temporal y se renombra, así una escritura interrumpida no deja el archivo a medias).
- **No guardar** → cierra.
- **Cancelar** → no cierra.

Aclaración importante: TextilFlow siempre guarda en su base interna a medida que trabaja. «Guardar como…» crea una copia con
nombre para llevar a otro equipo o volver a ese punto; el cuadro lo explica.

**Respaldos automáticos** (`infrastructure/respaldos.py`, carpeta `~/.textilflow/respaldos/`):

- Se crea uno cada 5 minutos si hubo cambios, al abrir (si el último tiene más de 1 hora) y al cerrar.
- Se conservan los **3 más recientes**; son archivos `.rlr` normales.
- **Recuperación tras apagado inesperado.** Al abrir, el programa deja una marca (`sesion_abierta.flag`) que borra al cerrar
  bien. Si al arrancar la marca sigue ahí, la sesión anterior no cerró correctamente: ofrece restaurar el respaldo más
  reciente o continuar con los datos actuales.
- En **Data Manager → Respaldos automáticos (últimos 3)** se puede elegir y restaurar cualquiera.

Pruebas: `test_cerrar_con_cambios_pregunta_y_permite_cancelar_o_guardar`,
`test_respaldos_automaticos_conservan_los_ultimos_3_y_detectan_cierre_incorrecto`.

## 9 · Tamaño y posición de la ventana

Al cerrar se guarda la geometría (`QSettings`) y al abrir se restaura, solo si sigue cabiendo en alguna pantalla conectada
(si se desconectó un monitor, vuelve al tamaño por defecto, centrado). También se recuerda si estaba maximizada.

## 4 y 7 · Velocidad en equipos humildes

Medido con el perfilador: abrir tardaba sobre todo porque **se repetían simulaciones** (10 al abrir; Dashboard, alertas y
refrescos duplicados). Cambios:

1. **Caché de simulaciones** (`nucleo.simular_completo`): si los datos no cambiaron, no se vuelve a simular. La versión de
   los datos es el contador de escrituras de la base; cualquier cambio (un cierre, un pedido, un parámetro) la invalida.
   16 resultados como máximo. 10 simulaciones reales al abrir → 2 (las demás llamadas salen de la caché).
2. **Se quitó un refresco duplicado** al iniciar.
3. **La ventana aparece primero y los datos se cargan justo después** (indicador «● CARGANDO…» → «● READY»).
4. **Páginas bajo demanda** (de la 4.0.6): solo se construye la página que se visita; el cambio de tema ya no reconstruye todo.
5. **Animación del mapa más liviana:**
   - se **pausa sola** al ir a otra página o minimizar, y continúa al volver;
   - avanza según el **reloj real** (en un PC lento salta cuadros pero no cambia la velocidad), a 20 cuadros/s;
   - solo repinta arcos y áreas que **cambiaron**; las tablas y el gráfico se refrescan 4 veces por segundo, no en cada cuadro.
6. **`construir_exe.bat`:** sigue siendo **un solo archivo**; ahora excluye módulos que no se usan (tkinter, matplotlib,
   scipy, IPython, pytest, QtWebEngine, QtQml, QtQuick, QtMultimedia, QtBluetooth, Qt3D) y desactiva UPX. Menos peso y
   menos tiempo de descompresión al abrir. *Sin probar en Windows.*

Pruebas: `test_cache_de_simulacion_se_reutiliza_y_se_invalida_al_cambiar_los_datos`,
`test_animacion_del_mapa_se_pausa_al_salir_de_la_pagina_y_se_reanuda`.

## 10 · Páginas que se adaptan a pantallas pequeñas

- Cada página va dentro de un área con barras de desplazamiento (4.0.7).
- **Menú lateral compacto** (solo iconos) por debajo de 980 px de ancho de ventana; la cabecera se abrevia.
- **`FilaAdaptable`** (`widgets/adaptable.py`): como una fila horizontal, pero si el ancho no alcanza para lo que contiene,
  se apila en columna. Se usa en el mapa, dashboard, simulación, requerimientos, contingencias, formularios con tabla, etc.
- **`FlujoLayout`:** las tarjetas de indicadores (KPI) se reparten en varias filas cuando no caben.
- Las pestañas se desplazan en vez de ensanchar la página.

Prueba: `test_ninguna_pagina_desborda_horizontalmente_desde_800_px` (revisa las 14 páginas a 1366, 1024, 900 y 800 px).
Queda un desplazamiento interno en el formulario de los paneles tabla+formulario a 800 px (es del propio formulario).

## Extra · Diálogos ilegibles en tema oscuro

Los cuadros de mensaje no tenían estilo para el tema oscuro (texto claro sobre fondo claro). Se agregó estilo a
`QDialog`, `QMessageBox`, `QProgressDialog`, `QInputDialog` y `QProgressBar` en `theme.py`.

## Pruebas

89 pruebas (antes 76 en la 4.0.5). `pytest` con `QT_QPA_PLATFORM=offscreen`. Las pruebas usan una carpeta de datos y una
configuración temporales: no tocan `~/.textilflow` ni los ajustes del usuario.

## Pendiente / límites conocidos

- Medir en un PC humilde real con Windows: abrir el `.exe` y cambiar de tema.
- Los botones «Show Details…» de Qt salen en inglés (falta cargar las traducciones de Qt).
- La primera visita a cada página tarda unas décimas porque se construye en ese momento.
