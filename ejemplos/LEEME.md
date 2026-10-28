# Ejemplos para TextilFlow

Data Manager → **Cargar ejemplo desde archivo… → Elegir archivo…** y seleccione un `.xlsx` de esta carpeta.
No borra nada: crea un taller nuevo y su escenario S0 (manual, 2 operarios) ya simulado.

| Archivo | Qué es |
|---|---|
| `01_confeccion_andina.xlsx` | Caso base (el mismo del ejemplo integrado). |
| `02_confeccion_transporte_critico.xlsx` | Distancias ×3 y pedidos ×1.5: el transporte pasa a limitar; útil para comparar manual vs robot. |
| `03_DIFICIL_camiseria_14_areas.xlsx` | 14 áreas, 5 prendas, 10 ramas, 8 pedidos. Dos cuellos de botella (Estampado y Bordado, ρ ≈ 100 %), 3 costuras alternativas y atajos angostos. Flota inicial: 3 operarios; con el turno completo termina ≈ 77 % de los lotes. |
| `04_MUY_DIFICIL_denim_20_areas.xlsx` | 20 áreas, 7 prendas, 13 ramas, 12 pedidos. Lavandería saturada (ρ ≈ 117 %), retrabajo (Inspección→Retrabajo→Inspección), buffer, tres grupos paralelos y pasillos de 1,0 m. Flota inicial: 4 operarios; termina ≈ 45 %. |
| `05_ULTRA_planta_3_naves_29_areas.xlsx` | 29 áreas en 3 naves unidas por un solo «Pasillo central» (nodo crítico), 10 prendas, 19 ramas, 20 pedidos con prioridad 1 a mitad del turno y plazos ajustados. Varias áreas con ρ > 100 %. Flota inicial: 6 operarios; termina ≈ 27 %. |

Los tres últimos se generan con `python tools/generar_ejemplos.py` (datos sintéticos, no mediciones). La flota inicial es un punto de partida: pruebe más operarios, robots o el barrido de flota para ver cómo cambia el resultado.

## Ejemplos generados por una IA
Descargue la plantilla (Data Manager → Crear plantilla) y pídale a la IA que la llene con su caso, por ejemplo:

> Llena este libro de Excel con un taller de **[tipo de producto]**. Hojas: Taller, Nodos (código, nombre, función ALMACEN/DESPACHO/PROCESO/ESPERA/BASE, x, y, min/unidad, capacidad, grupo), Conexiones (origen, destino, distancia_m, ancho_m, bidireccional), Prendas, Rutas (secuencia con códigos de nodo separados por «>», empezando en el Almacén y terminando en Despacho; las fracciones de un mismo producto suman 100 %) y Pedidos. No cambie los encabezados.

Si el archivo tiene errores, el programa lo rechaza completo y le dice en qué hoja y fila están.
