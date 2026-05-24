# app/services/ubs_service.py
"""
Serviço de busca de UBS (Unidades Básicas de Saúde) próximas a um CEP.

Pipeline completo (todas as APIs são gratuitas e sem chave):
  1. ViaCEP          → converte CEP em endereço + cidade + estado
  2. Nominatim (OSM) → converte endereço em coordenadas (lat, lng)
  3. Overpass API    → busca estabelecimentos de saúde num raio de 5km
  4. Ordena por: públicas primeiro, dentro de cada grupo ordena por distância
  5. Retorna as 5 mais relevantes com links do Google Maps
"""

import logging
import math
import httpx

logger = logging.getLogger("denguecare.ubs")

# ==========================================
# CONFIGURAÇÕES
# ==========================================
RAIO_KM = 5
MAX_RESULTADOS = 5

# health_post vem primeiro — é exclusivamente público no Brasil
OSM_AMENITIES = ["health_post", "clinic", "hospital", "doctors"]

HEADERS_NOMINATIM = {
    "User-Agent": "DengueCare-Bot/1.0 (projeto academico FATEC Rio Claro)"
}

# ==========================================
# SISTEMA DE PONTUAÇÃO — PRIORIZA UNIDADES PÚBLICAS
# ==========================================
_PALAVRAS_PUBLICO = [
    "ubs", "upa", "cbs", "posto de saúde", "posto saude",
    "unidade básica", "unidade basica", "unidade de saúde",
    "caps", "ams", "ambulatório", "ambulatorio",
    "municipal", "prefeitura", "sus",
]

_PALAVRAS_PRIVADO = [
    "particular", "ltda", "s/a", "sa ", "grupo", "rede", "s.a",
]

_OPERADORES_PUBLICO = [
    "prefeitura", "secretaria", "municipal", "estado", "governo",
    "sus", "ministerio", "ministério",
]


def _calcular_prioridade(tags: dict) -> int:
    """
    0 = certamente público
    1 = provavelmente público
    2 = desconhecido
    3 = privado
    """
    amenity  = tags.get("amenity", "")
    nome     = (tags.get("name", "") + " " + tags.get("name:pt", "")).lower()
    operator = tags.get("operator", "").lower()
    fee      = tags.get("fee", "").lower()
    access   = tags.get("healthcare:access", "").lower()

    if amenity == "health_post":
        return 0
    if access in ("yes", "public") or fee == "no":
        return 0
    if any(p in nome for p in _PALAVRAS_PUBLICO):
        return 1
    if any(p in operator for p in _OPERADORES_PUBLICO):
        return 1
    if fee == "yes":
        return 3
    if any(p in nome for p in _PALAVRAS_PRIVADO):
        return 3
    return 2


# ==========================================
# UTILITÁRIO: Fórmula de Haversine
# ==========================================
def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


# ==========================================
# STEP 1: CEP → Endereço (ViaCEP)
# ==========================================
async def buscar_endereco_por_cep(cep: str) -> dict | None:
    url = f"https://viacep.com.br/ws/{cep}/json/"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        if data.get("erro"):
            logger.warning(f"CEP não encontrado no ViaCEP: {cep}")
            return None

        logger.info(f"ViaCEP OK: {data.get('localidade')}/{data.get('uf')}")
        return {
            "logradouro": data.get("logradouro", ""),
            "bairro":     data.get("bairro", ""),
            "cidade":     data.get("localidade", ""),
            "estado":     data.get("uf", ""),
            "cep":        cep,
        }
    except httpx.HTTPError as e:
        logger.error(f"Erro ao consultar ViaCEP para CEP {cep}: {e}")
        return None


# ==========================================
# STEP 2: Endereço → Coordenadas (Nominatim)
# Tenta do mais específico ao mais genérico para maior precisão
# ==========================================
async def geocodificar_endereco(endereco: dict) -> tuple[float, float] | None:
    """
    Tenta múltiplas queries do mais específico ao mais genérico,
    garantindo que o ponto de origem seja o mais preciso possível.
    """
    cidade  = endereco.get("cidade", "")
    estado  = endereco.get("estado", "")
    bairro  = endereco.get("bairro", "")
    rua     = endereco.get("logradouro", "")

    # Lista de tentativas, da mais específica à mais genérica
    tentativas = []

    if rua and bairro:
        tentativas.append(f"{rua}, {bairro}, {cidade}, {estado}, Brasil")
    if rua:
        tentativas.append(f"{rua}, {cidade}, {estado}, Brasil")
    if bairro:
        tentativas.append(f"{bairro}, {cidade}, {estado}, Brasil")
    tentativas.append(f"{cidade}, {estado}, Brasil")

    url = "https://nominatim.openstreetmap.org/search"

    for query in tentativas:
        params = {"q": query, "format": "json", "limit": 1, "countrycodes": "br"}
        try:
            async with httpx.AsyncClient(timeout=15, headers=HEADERS_NOMINATIM) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                results = response.json()

            if results:
                lat = float(results[0]["lat"])
                lng = float(results[0]["lon"])
                logger.info(f"Nominatim OK com query '{query}': ({lat}, {lng})")
                return lat, lng

        except httpx.HTTPError as e:
            logger.error(f"Erro ao consultar Nominatim: {e}")
            continue

    logger.warning(f"Nominatim não encontrou coordenadas para nenhuma tentativa do CEP")
    return None


# ==========================================
# STEP 3: Coordenadas → Unidades de saúde (Overpass)
# ==========================================
async def buscar_ubs_proximas(lat: float, lng: float) -> list[dict]:
    raio_metros = RAIO_KM * 1000

    amenities_query = ""
    for amenity in OSM_AMENITIES:
        amenities_query += f'node["amenity"="{amenity}"](around:{raio_metros},{lat},{lng});\n'
        amenities_query += f'way["amenity"="{amenity}"](around:{raio_metros},{lat},{lng});\n'

    # Buscamos mais resultados para depois filtrar e ordenar corretamente
    overpass_query = f"""
    [out:json][timeout:25];
    (
      {amenities_query}
    );
    out center {MAX_RESULTADOS * 6};
    """

    url = "https://overpass-api.de/api/interpreter"

    try:
        async with httpx.AsyncClient(timeout=30, headers=HEADERS_NOMINATIM) as client:
            response = await client.post(url, data={"data": overpass_query})
            response.raise_for_status()
            data = response.json()

        elementos = data.get("elements", [])
        if not elementos:
            logger.warning(f"Overpass não retornou resultados para ({lat}, {lng})")
            return []

        ubs_list = []
        for elem in elementos:
            elem_lat = elem.get("lat") or elem.get("center", {}).get("lat")
            elem_lng = elem.get("lon") or elem.get("center", {}).get("lon")
            if not elem_lat or not elem_lng:
                continue

            tags = elem.get("tags", {})
            nome = (
                tags.get("name")
                or tags.get("name:pt")
                or tags.get("operator")
                or "Unidade de Saúde"
            )

            partes_end = []
            if tags.get("addr:street"):
                rua = tags["addr:street"]
                if tags.get("addr:housenumber"):
                    rua += f", {tags['addr:housenumber']}"
                partes_end.append(rua)
            if tags.get("addr:suburb") or tags.get("addr:neighbourhood"):
                partes_end.append(tags.get("addr:suburb") or tags.get("addr:neighbourhood"))
            if tags.get("addr:city"):
                partes_end.append(tags["addr:city"])

            endereco_str = " — ".join(partes_end) if partes_end else "Endereço não disponível"
            prioridade   = _calcular_prioridade(tags)
            distancia_km = _haversine(lat, lng, elem_lat, elem_lng)

            ubs_list.append({
                "nome":       nome,
                "endereco":   endereco_str,
                "lat":        elem_lat,
                "lng":        elem_lng,
                "tipo":       tags.get("amenity", "clinic"),
                "telefone":   tags.get("phone") or tags.get("contact:phone", ""),
                "prioridade": prioridade,
                "distancia":  distancia_km,  # usado só para ordenação, não exibido
            })

        # Ordenação em dois níveis:
        # 1º critério: prioridade (públicas antes das privadas)
        # 2º critério: distância (mais próximas antes das mais longes)
        # Isso garante: UBS pública próxima > UBS pública longe > particular próxima > particular longe
        ubs_list.sort(key=lambda x: (x["prioridade"], x["distancia"]))
        resultado = ubs_list[:MAX_RESULTADOS]

        publicos = sum(1 for u in resultado if u["prioridade"] <= 1)
        logger.info(
            f"Overpass OK: {len(resultado)} unidades encontradas "
            f"({publicos} públicas) — mais próxima a {resultado[0]['distancia']:.2f}km"
            if resultado else "Overpass OK: nenhuma unidade encontrada"
        )
        return resultado

    except httpx.HTTPError as e:
        logger.error(f"Erro ao consultar Overpass API: {e}")
        return []


# ==========================================
# FUNÇÃO PRINCIPAL
# ==========================================
async def buscar_ubs_por_cep(cep: str) -> tuple[list[dict], dict | None]:
    cep_limpo = ''.join(filter(str.isdigit, cep))
    if len(cep_limpo) != 8:
        return [], None

    endereco = await buscar_endereco_por_cep(cep_limpo)
    if not endereco:
        return [], None

    coords = await geocodificar_endereco(endereco)
    if not coords:
        return [], None

    lat, lng = coords
    ubs_list = await buscar_ubs_proximas(lat, lng)
    return ubs_list, endereco


# ==========================================
# FORMATAÇÃO DA MENSAGEM PARA O BOT
# ==========================================
def formatar_mensagem_ubs(ubs_list: list[dict], endereco: dict) -> str:
    from app.handlers.start_handler import _escape_md

    cidade = _escape_md(endereco.get("cidade", ""))
    estado = _escape_md(endereco.get("estado", ""))

    if not ubs_list:
        return (
            f"😔 *Nenhuma unidade de saúde encontrada* num raio de {RAIO_KM}km "
            f"de *{cidade}/{estado}*\\.\n\n"
            f"Sugerimos que você:\n"
            f"• Ligue para o *SAMU: 192* em caso de emergência\n"
            f"• Consulte o site da prefeitura de {cidade} para localizar a UBS mais próxima"
        )

    linhas = [
        f"🏥 *Unidades de Saúde próximas a {cidade}/{estado}*\n"
        f"_Raio de busca: {RAIO_KM}km \\| Públicas e mais próximas aparecem primeiro_\n"
    ]

    emojis_num = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

    for i, ubs in enumerate(ubs_list):
        emoji = emojis_num[i] if i < len(emojis_num) else "•"
        nome         = _escape_md(ubs["nome"])
        endereco_ubs = _escape_md(ubs["endereco"])

        if ubs["prioridade"] <= 1:
            badge = "🟢 _Pública_"
        elif ubs["prioridade"] == 2:
            badge = "⚪ _Não identificada_"
        else:
            badge = "🔵 _Particular_"

        maps_url  = f"https://www.google.com/maps/search/?api=1&query={ubs['lat']},{ubs['lng']}"
        maps_link = f"[📍 Ver no mapa]({maps_url})"

        linha  = f"{emoji} *{nome}* {badge}\n"
        linha += f"   📌 {endereco_ubs}\n"

        if ubs.get("telefone"):
            telefone = _escape_md(ubs["telefone"])
            linha += f"   📞 {telefone}\n"

        linha += f"   {maps_link}"
        linhas.append(linha)

    linhas.append(
        "\n_Dados fornecidos pelo OpenStreetMap\\. "
        "Verifique o horário de funcionamento antes de se dirigir à unidade\\._"
    )

    return "\n\n".join(linhas)