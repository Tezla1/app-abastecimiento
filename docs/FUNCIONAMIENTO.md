# Funcionamiento de TextilFlow 2.0

## 1. Qué problema resuelve
En un taller de confección cada pedido se divide en lotes y cada lote recorre varias áreas (corte, costura, bordado, inspección,
planchado, empaque) antes de salir por Despacho. Hay tres fuentes de pérdida: **áreas que se saturan** (cuellos de botella),
**transporte insuficiente o mal dimensionado** y **prioridades que no se respetan**. TextilFlow las mide con datos y simulación.

## 2. Datos de entrada
| Entidad | Qué define |
|---|---|
| Área | código, función (Almacén / Despacho / Proceso…), posición, **min por unidad**, **puestos en paralelo**, **grupo** |
| Conexión | pasillo entre dos áreas: distancia (m) y ancho (m) |
| Prenda | peso por unidad (kg), unidades por lote, factor de dificultad (multiplica los tiempos de las áreas) |
| Ruta (rama) | secuencia `A>C>B>@COSTURA>I>E>D` y % de las unidades de esa prenda que la siguen |
| Pedido | prenda, cantidad, prioridad (1 = urgente), llegada al almacén, fecha límite |
| Escenario | nº de recursos, velocidad, capacidad por viaje, carga/descarga, política, balanceo, demanda %, variabilidad ±%, semilla |

## 3. Motor de simulación
* Cada pedido se reparte entre sus ramas (método del mayor resto) y se parte en lotes.
* Un lote llega al almacén, pide transporte a la primera área, se procesa, pide transporte a la siguiente, etc., hasta Despacho.
* **Áreas**: procesan hasta `puestos` lotes a la vez; el resto espera en cola (se atiende por prioridad o por llegada).
* **Transporte**: cada traslado va al recurso libre **más cercano**; recorre vacío hasta el lote y luego cargado por la ruta más
  corta que quepa por los pasillos. Viajes por traslado = ⌈unidades / ⌊capacidad / peso⌋⌉.
* **Grupos** (`@COSTURA`): se elige el área con menor carga estimada (tiempo de viaje + trabajo comprometido / puestos). Sin balanceo, por turnos.
* **Cierre de turno**: no se inicia transporte ni proceso desde el minuto de observación; lo pendiente queda «sin terminar» y genera alerta.
* **Variabilidad**: con semilla fija, cada tiempo de proceso varía ±X %. Con 0 % el modelo es determinista.

## 4. Qué se calcula
* **Por área**: utilización, espera media y máxima, cola máxima, y carga ofrecida analítica ρ = Σ(unidades × min/u × factor) / (puestos × turno).
* **Por proceso**: lotes completados, cierre de la última entrega, lead time, rendimiento (u/h), pedidos a tiempo y tardanza.
* **Modelo de `calculos.py`** sobre los traslados: tiempo de abastecimiento, distancia, espera, utilización de la flota, % atendidos y variación S0→S1.
* **Tráfico**: pasadas y kg por arco y nodo (mapa de calor), acumulable en el tiempo.
* **Críticos**: cuellos de botella, nodos y arcos cuya falla desconecta la red (puntos únicos de falla), pasillos bajo la norma, arco más transitado.
* **Requerimientos**: barrido de flota 1…N (utilización, espera, cierre), estimación analítica N ≥ trabajo de transporte / (turno × utilización objetivo), viajes por prenda, distancias por rama.
* **Réplicas**: N corridas con semillas distintas → media, desviación, mínimo, máximo e IC 95 % (t de Student), y un resumen de qué tan estable es cada resultado.

## 5. Alertas
Configuración (sin Almacén o Despacho, rutas inválidas, prenda sin ruta), normativa (pasillo bajo el mínimo, robot que no cabe),
y simulación (cuello de botella, cola larga, pedido tarde o sin terminar, lotes sin transporte, flota saturada o sobredimensionada).
Los umbrales son parámetros editables.

## 6. Cómo leer los resultados
1. **¿Dónde se pierde tiempo?** Estado de las áreas: utilización simulada vs ρ. Si ρ ≥ umbral, es el cuello de botella.
2. **¿Faltan equipos?** Barrido de flota: si más equipos no mejoran el cierre, el límite no es el transporte.
3. **¿Se respeta la prioridad?** Lead time del pedido urgente con prioridad vs FIFO (pruebas 4 del ejercicio).
4. **¿Qué ruta usa un pedido?** Mapa operativo → pedido → pulsar un área.
5. **¿Qué tan fiable es el número?** Réplicas con variabilidad: use el IC 95 %.

## 7. Limitaciones
Datos sintéticos; sin averías, baterías ni cruces entre recursos; capacidad de pasillos solo por ancho; normativa según la tabla
de «verificado» del README. Los resultados de un modelo no sustituyen la medición en planta.
