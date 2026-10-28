from dataclasses import dataclass
from typing import Optional

ORIGENES_DATOS = {
    "SINTETICO": "Sintético",
    "REAL": "Real",
    "DISENO": "Diseño / conceptual",
}

FUNCIONES = {
    "ALMACEN": "Almacén (punto inicial)",
    "DESPACHO": "Despacho (punto final)",
    "PROCESO": "Área de proceso",
    "ESPERA": "Punto de espera / buffer",
    "BASE": "Base del recurso",
}

TIPOS_ESCENARIO = {
    "MANUAL": "S0 · Manual",
    "AMR": "S1 · AMR",
}

POLITICAS = {
    "PRIORIDAD": "Prioridad (1 = más urgente)",
    "FIFO": "FIFO · orden de llegada",
}

PREFIJO_GRUPO = "@"


@dataclass
class Taller:
    nombre: str
    area_m2: float = 0.0
    operadores: int = 0
    jornada_h: float = 8.0
    origen_datos: str = "SINTETICO"
    observaciones: str = ""
    id: Optional[int] = None

    def validar(self) -> list[str]:
        e = []
        if not self.nombre.strip():
            e.append("El nombre del taller es obligatorio.")
        if self.area_m2 < 0:
            e.append("El área no puede ser negativa.")
        if self.operadores < 0:
            e.append("Los operadores no pueden ser negativos.")
        if not 0 < self.jornada_h <= 24:
            e.append("La jornada debe estar entre 0 y 24 horas.")
        if self.origen_datos not in ORIGENES_DATOS:
            e.append("Origen de datos no válido.")
        return e


@dataclass
class Estacion:
    taller_id: int
    codigo: str
    nombre: str = ""
    funcion: str = "PROCESO"
    x: float = 0.0
    y: float = 0.0
    tiempo_proceso_min: float = 0.0
    capacidad: int = 1
    grupo: str = ""
    id: Optional[int] = None

    def validar(self) -> list[str]:
        e = []
        if not self.codigo.strip() or " " in self.codigo.strip() or self.codigo.startswith(PREFIJO_GRUPO):
            e.append("El código de la estación es obligatorio, sin espacios y no puede empezar con «@».")
        if self.funcion not in FUNCIONES:
            e.append("Función logística no válida.")
        if self.tiempo_proceso_min < 0:
            e.append("El tiempo de proceso no puede ser negativo.")
        if self.tiempo_proceso_min > 0 and self.funcion != "PROCESO":
            e.append("Solo las áreas de proceso pueden tener tiempo de proceso.")
        if self.capacidad < 1:
            e.append("La capacidad (puestos en paralelo) debe ser al menos 1.")
        if " " in self.grupo.strip() or self.grupo.startswith(PREFIJO_GRUPO):
            e.append("El grupo no puede tener espacios ni empezar con «@».")
        return e


@dataclass
class Conexion:
    taller_id: int
    origen: str
    destino: str
    distancia_m: float = 0.0
    ancho_m: float = 1.5
    bidireccional: bool = True
    id: Optional[int] = None

    def validar(self) -> list[str]:
        e = []
        if self.origen == self.destino:
            e.append("Una conexión no puede unir una estación consigo misma.")
        if self.distancia_m < 0:
            e.append("La distancia no puede ser negativa.")
        if self.ancho_m <= 0:
            e.append("El ancho del pasillo debe ser mayor que 0.")
        return e


@dataclass
class TipoPrenda:
    nombre: str
    peso_unidad_kg: float = 0.3
    unidades_por_lote: int = 50
    factor_proceso: float = 1.0
    id: Optional[int] = None

    def validar(self) -> list[str]:
        e = []
        if not self.nombre.strip():
            e.append("El nombre del tipo de prenda es obligatorio.")
        if self.peso_unidad_kg <= 0:
            e.append("El peso por unidad debe ser mayor que 0.")
        if self.unidades_por_lote < 1:
            e.append("El lote debe tener al menos 1 unidad.")
        if self.factor_proceso <= 0:
            e.append("El factor de proceso debe ser mayor que 0.")
        return e


@dataclass
class RutaProceso:
    taller_id: int
    tipo_prenda_id: int
    nombre: str
    fraccion_pct: float = 100.0
    secuencia: str = ""
    id: Optional[int] = None

    def pasos(self) -> list[str]:
        pasos = [p.strip() for p in self.secuencia.split(">") if p.strip()]
        return [p.upper() if p.startswith(PREFIJO_GRUPO) else p for p in pasos]

    def validar(self) -> list[str]:
        e = []
        if not self.nombre.strip():
            e.append("El nombre de la ruta es obligatorio.")
        if not 0 < self.fraccion_pct <= 100:
            e.append("La fracción debe estar entre 0 y 100 %.")
        pasos = self.pasos()
        if len(pasos) < 2:
            e.append("La ruta necesita al menos 2 pasos (origen y destino).")
        if any(a == b for a, b in zip(pasos, pasos[1:])):
            e.append("Una ruta no puede repetir el mismo paso dos veces seguidas.")
        return e


@dataclass
class Pedido:
    taller_id: int
    tipo_prenda_id: int
    cantidad: int
    prioridad: int = 3
    llegada_min: float = 0.0
    vencimiento_min: float = 0.0
    origen_datos: str = "SINTETICO"
    id: Optional[int] = None

    def validar(self) -> list[str]:
        e = []
        if self.cantidad < 1:
            e.append("La cantidad debe ser al menos 1 unidad.")
        if not 1 <= self.prioridad <= 9:
            e.append("La prioridad debe estar entre 1 (urgente) y 9.")
        if self.llegada_min < 0:
            e.append("La llegada no puede ser negativa.")
        if self.vencimiento_min < 0:
            e.append("El vencimiento no puede ser negativo.")
        if self.vencimiento_min and self.vencimiento_min <= self.llegada_min:
            e.append("El vencimiento debe ser posterior a la llegada.")
        if self.origen_datos not in ORIGENES_DATOS:
            e.append("Origen de datos no válido.")
        return e


@dataclass
class Robot:
    nombre: str
    capacidad_kg: float
    velocidad_ms: float
    ancho_m: float
    radio_giro_m: float = 0.0
    origen_datos: str = "DISENO"
    id: Optional[int] = None

    def validar(self) -> list[str]:
        e = []
        if not self.nombre.strip():
            e.append("El nombre del robot es obligatorio.")
        if self.capacidad_kg <= 0:
            e.append("La capacidad de carga debe ser mayor que 0.")
        if self.velocidad_ms <= 0:
            e.append("La velocidad debe ser mayor que 0.")
        if self.ancho_m <= 0:
            e.append("El ancho del robot debe ser mayor que 0.")
        if self.radio_giro_m < 0:
            e.append("El radio de giro no puede ser negativo.")
        return e


@dataclass
class Escenario:
    taller_id: int
    nombre: str
    tipo: str = "MANUAL"
    num_recursos: int = 1
    tiempo_observacion_min: float = 480.0
    velocidad_ms: float = 1.0
    capacidad_kg: float = 40.0
    t_carga_s: float = 0.0
    t_descarga_s: float = 0.0
    nodo_inicial: str = ""
    reposicionamiento: bool = True
    robot_id: Optional[int] = None
    politica: str = "PRIORIDAD"
    balanceo: bool = True
    factor_demanda_pct: float = 100.0
    variabilidad_pct: float = 0.0
    semilla: int = 1
    id: Optional[int] = None

    def validar(self) -> list[str]:
        e = []
        if not self.nombre.strip():
            e.append("El nombre del escenario es obligatorio.")
        if self.tipo not in TIPOS_ESCENARIO:
            e.append("Tipo de escenario no válido.")
        if self.num_recursos < 1:
            e.append("Debe haber al menos un recurso.")
        if self.tiempo_observacion_min <= 0:
            e.append("El tiempo de observación debe ser mayor que 0.")
        if self.velocidad_ms <= 0:
            e.append("La velocidad debe ser mayor que 0.")
        if self.capacidad_kg <= 0:
            e.append("La capacidad debe ser mayor que 0.")
        if self.t_carga_s < 0 or self.t_descarga_s < 0:
            e.append("Los tiempos de carga/descarga no pueden ser negativos.")
        if not self.nodo_inicial.strip():
            e.append("Seleccione el nodo inicial del recurso.")
        if self.politica not in POLITICAS:
            e.append("Política de despacho no válida.")
        if self.factor_demanda_pct <= 0:
            e.append("El factor de demanda debe ser mayor que 0 %.")
        if not 0 <= self.variabilidad_pct < 100:
            e.append("La variabilidad debe estar entre 0 y 99 %.")
        return e

    def para_calculo(self) -> dict:
        return {
            "num_recursos": self.num_recursos,
            "tiempo_observacion_min": self.tiempo_observacion_min,
        }


@dataclass
class Registro:
    escenario_id: int
    pedido_id: Optional[int]
    lote: int
    desde: str
    hacia: str
    atendida: bool
    tiempo_espera_min: float = 0.0
    tiempo_recorrido_min: float = 0.0
    distancia_m: float = 0.0
    inicio_min: float = 0.0
    fin_min: float = 0.0
    recurso: int = 0
    viajes: int = 1
    detalle: str = ""
    id: Optional[int] = None

    def para_calculo(self) -> dict:
        return {
            "atendida": self.atendida,
            "tiempo_espera_min": self.tiempo_espera_min,
            "tiempo_recorrido_min": self.tiempo_recorrido_min,
            "distancia_m": self.distancia_m,
        }


@dataclass
class Parametro:
    clave: str
    valor: float
    unidad: str = ""
    descripcion: str = ""
    fuente: str = ""
    verificado: bool = False
    id: Optional[int] = None

    def validar(self) -> list[str]:
        return [] if self.valor >= 0 else ["El valor del parámetro no puede ser negativo."]


MOTIVOS_CIERRE = {
    "FALLA_MAQUINARIA": "Falla de maquinaria",
    "MANTENIMIENTO": "Mantenimiento programado",
    "FALTA_PERSONAL": "Falta de personal",
    "SEGURIDAD": "Riesgo o inspección de seguridad",
    "FALTA_INSUMOS": "Falta de insumos",
    "OTRO": "Otro motivo",
}


ESTADOS_COMPRA = {
    "PENDIENTE": "Pendiente · por pedir a Compras",
    "PEDIDA": "Pedida · en camino",
    "RECIBIDA": "Recibida · ya está en el almacén",
    "CANCELADA": "Cancelada",
}


@dataclass
class Stock:
    """Unidades disponibles en el almacén del taller para una prenda, y el mínimo que dispara el aviso."""
    taller_id: int
    tipo_prenda_id: int
    unidades: int = 0
    stock_minimo: int = 0
    id: Optional[int] = None

    def validar(self) -> list[str]:
        e = []
        if self.unidades < 0:
            e.append("Las unidades en el almacén no pueden ser negativas.")
        if self.stock_minimo < 0:
            e.append("El stock mínimo no puede ser negativo.")
        return e


@dataclass
class SolicitudCompra:
    """Aviso que el operador genera para que Compras haga el pedido de reposición."""
    taller_id: int
    tipo_prenda_id: int
    cantidad: int
    estado: str = "PENDIENTE"
    nota: str = ""
    registrado: str = ""
    id: Optional[int] = None

    def validar(self) -> list[str]:
        e = []
        if self.cantidad < 1:
            e.append("La cantidad a comprar debe ser al menos 1 unidad.")
        if self.estado not in ESTADOS_COMPRA:
            e.append("Estado de la compra no válido.")
        return e


@dataclass
class Cierre:
    taller_id: int
    codigo: str
    motivo: str = "FALLA_MAQUINARIA"
    detalle: str = ""
    desde_min: float = 0.0
    hasta_min: float = 0.0
    bloquea_paso: bool = True
    vigente: bool = True
    registrado: str = ""
    id: Optional[int] = None

    def validar(self) -> list[str]:
        e = []
        if not self.codigo.strip():
            e.append("Elija el área que se va a cerrar.")
        if self.motivo not in MOTIVOS_CIERRE:
            e.append("Motivo de cierre no válido.")
        if self.desde_min < 0:
            e.append("El minuto de inicio no puede ser negativo.")
        if self.hasta_min < 0:
            e.append("El minuto de reapertura no puede ser negativo.")
        if self.hasta_min and self.hasta_min <= self.desde_min:
            e.append("La reapertura debe ser posterior al inicio del cierre (use 0 si no se reabre en el turno).")
        return e
