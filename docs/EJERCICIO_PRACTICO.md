# TextilFlow 4.0.4 · Ejercicio práctico

Caso: **Confecciones Andina - Caso Experimental 01** (datos SINTÉTICOS, no son mediciones) · compilación 2026-10 · 30 réplicas por prueba · semillas 100–129.

Reproducir: `python tools/ejercicio_practico.py`.

## Prueba 1 · Un turno base (S0 manual vs S1 AMR)

| Escenario | Lotes ok | Cierre (min) | Lead time (min) | A tiempo | Espera transp. (min) | Util. flota | Alertas |
|---|---|---|---|---|---|---|---|
| S0 · Manual (2 operarios) | 46/52 | 477 | 234 | 25 % | 0.80 | 37.9 % | 7 |
| S1 · AMR Andina (2 robots) | 46/52 | 478 | 235 | 25 % | 0.89 | 41.3 % | 7 |


**Estado de las áreas (S0):**

| Área | Puestos | Util. % | Carga ofrecida ρ % | Espera media (min) | Cola máx. |
|---|---|---|---|---|---|
| C · Corte | 3 | 43.9 | 43.9 | 60.5 | 24 |
| CO · Costura 1 | 4 | 68.3 | 70.9 | 15.6 | 4 |
| CO2 · Costura 2 | 4 | 66.3 | 70.9 | 15.1 | 3 |
| B · Bordado | 1 | 82.0 | 87.9 | 143.8 | 14 |
| I · Inspección | 2 | 29.8 | 33.4 | 0.7 | 3 |
| P · Planchado | 2 | 69.8 | 76.8 | 22.0 | 6 |
| E · Empaque | 2 | 53.4 | 59.1 | 0.5 | 2 |

**Lectura:** el cuello de botella es **Bordado** (carga ofrecida 88 %, espera media 144 min): tiene un solo puesto. El transporte no es la restricción.

## Prueba 2 · 30 réplicas con variabilidad de ±15 % en los tiempos de proceso

| Escenario | Cierre (min) | Lead time (min) | Lotes ok (%) | Pedidos a tiempo (%) | Lead time prioridad 1 |
|---|---|---|---|---|---|
| S0 · Manual (2 operarios) | 468.0 ± 2.7 | 230.1 ± 1.5 | 88.4 ± 0.3 | 28 ± 3 | 216.3 ± 2.5 |
| S1 · AMR Andina (2 robots) | 470.9 ± 2.6 | 231.4 ± 1.4 | 88.5 ± 0.4 | 25 ± 0 | 218.2 ± 2.3 |

Valores: media ± semiancho del IC 95 %. La dispersión viene de la variabilidad de los tiempos; la semilla de cada réplica es fija.

## Prueba 3 · Tamaño de la flota (S0, 1 a 6 operarios)

| Equipos | Util. % | Espera (min) | Lotes ok % | Cierre (min) | Cumple objetivo 75 % |
|---|---|---|---|---|---|
| 1 | 75.8 | 4.25 | 88.5 | 478 |  |
| 2 | 37.9 | 0.80 | 88.5 | 477 | ✔ |
| 3 | 25.0 | 0.39 | 88.5 | 477 | ✔ |
| 4 | 18.6 | 0.24 | 88.5 | 476 | ✔ |
| 5 | 14.8 | 0.17 | 88.5 | 476 | ✔ |
| 6 | 12.3 | 0.12 | 88.5 | 476 | ✔ |

**Equipos recomendados: 2.** Aunque haya más equipos, el trabajo no termina por el cuello de botella en Bordado: agregar puestos allí rinde más que agregar equipos.

**Viajes por prenda (capacidad 25 kg):**

| Prenda | kg/u | u/viaje | Viajes por traslado | Lotes | Viajes estimados |
|---|---|---|---|---|---|
| Camisa | 0.25 | 100 | 1 | 24 | 168 |
| Pantalón | 0.6 | 41 | 1 | 10 | 60 |
| Chaqueta | 0.9 | 27 | 1 | 9 | 63 |
| Uniforme | 0.5 | 50 | 1 | 8 | 48 |

En el turno: 286 viajes cargados, 2154 m cargado + 2508 m vacío = 4661 m.

## Prueba 4 · Prioridad vs FIFO (30 réplicas, S0)

| Política | Lead time del pedido urgente (min) | Lead time medio (min) | A tiempo (%) | Cierre (min) |
|---|---|---|---|---|
| PRIORIDAD | 216.3 ± 2.5 | 230.1 ± 1.5 | 28 ± 3 | 468.0 ± 2.7 |
| FIFO | 363.4 ± 1.5 | 240.7 ± 1.2 | 50 ± 0 | 467.0 ± 2.6 |

**Lectura:** la prioridad adelanta el pedido urgente (216.3 ± 2.5 min frente a 363.4 ± 1.5 min con FIFO), pero el retraso no desaparece: se traslada a pedidos de menor prioridad (pedidos a tiempo: 28 ± 3 % con prioridad frente a 50 ± 0 % con FIFO). El cierre total casi no cambia, porque el cuello de botella sigue siendo el mismo.

## Prueba 5 · Balanceo entre Costura 1 y Costura 2 (30 réplicas, S0)

| Modo | Lead time (min) | Cierre (min) | Lotes ok (%) |
|---|---|---|---|
| Con balanceo | 230.1 ± 1.5 | 468.0 ± 2.7 | 88.4 ± 0.3 |
| Sin balanceo (por turnos) | 230.0 ± 1.3 | 467.8 ± 3.0 | 88.5 ± 0.4 |

Las dos costuras son idénticas, por eso el efecto es pequeño. El balanceo importa cuando las alternativas son distintas o están a distancias distintas.

## Prueba 6 · Aumento de la demanda (S1)

| Demanda | Lotes ok | Completado % | Cierre (min) | Área más cargada (ρ) | Alertas |
|---|---|---|---|---|---|
| 60 % | 34/34 | 100 | 389 | Bordado (53 %) | 1 |
| 80 % | 41/43 | 95 | 464 | Bordado (70 %) | 4 |
| 100 % | 46/52 | 88 | 478 | Bordado (88 %) | 7 |
| 120 % | 53/62 | 85 | 477 | Bordado (106 %) | 7 |
| 140 % | 54/74 | 73 | 481 | Bordado (123 %) | 9 |


## Prueba 7 · Qué pasa si se agrega un segundo puesto de Bordado (30 réplicas, S0)

| Configuración | Lead time (min) | Cierre (min) | Lotes ok (%) | A tiempo (%) |
|---|---|---|---|---|
| Bordado con 1 puesto | 230.1 ± 1.5 | 468.0 ± 2.7 | 88.4 ± 0.3 | 28 ± 3 |
| Bordado con 2 puestos | 246.8 ± 1.4 | 469.0 ± 2.2 | 99.9 ± 0.1 | 100 ± 0 |

Con dos puestos de Bordado el área más cargada pasa a ser **Planchado** (ρ 77 %): el cuello de botella se desplaza, que es lo esperable al optimizar un proceso. El lead time medio sube porque ahora terminan lotes que antes quedaban sin completar (y no entraban en el promedio): mire el % de lotes completados y de pedidos a tiempo.
