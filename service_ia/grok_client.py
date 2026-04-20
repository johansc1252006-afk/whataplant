import httpx
import requests
import json
import unicodedata
from ddgs import DDGS
import os

GROQ_API_KEY =os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ------------------------------------------------------------
# Recherche d'image robuste sur Wikimedia Commons
# ------------------------------------------------------------
def chercher_image_wikimedia_robuste(nom_plat):
    """Recherche une image via DuckDuckGo (méthode qui fonctionnait avant)"""
    if not nom_plat:
        return None
    query = nom_plat
    print(f"🔍 DuckDuckGo: {query[:50]}...")
    
    if not query or len(query) < 3:
        print("❌ Query trop courte")
        return None
    
    # Mots à enlever
    mots_a_enlever = [
        "stew", "sauce", "dish", "recipe", "african", "traditional", 
        "leaves", "leaf", "fresh", "green", "cooked", "preparation",
        "how", "to", "make", "with", "and", "for", "the", "from",
        "version", "recipe", "plate", "food", "meal", "cooking",
        "simple", "easy", "delicious", "homemade", "authentic"
    ]
    
    query_simple = query.lower()
    for mot in mots_a_enlever:
        query_simple = query_simple.replace(mot, "")
    query_simple = " ".join(query_simple.split())
    
    mots_cles = [w for w in query_simple.split() if len(w) > 3]
    if not mots_cles:
        mots_cles = [w for w in query.split() if len(w) > 3]
    
    variations = []
    if query_simple and len(query_simple) > 3:
        variations.append(query_simple)
    if len(mots_cles) >= 2:
        variations.append(f"{mots_cles[0]} {mots_cles[1]}")
        variations.append(f"{mots_cles[0]} {mots_cles[1]} food")
    elif len(mots_cles) == 1:
        variations.append(f"{mots_cles[0]} food")
        variations.append(f"{mots_cles[0]} cuisine")
    for mot in mots_cles[:2]:
        variations.append(mot)
    mots_originaux = query.lower().split()[:3]
    if mots_originaux:
        variations.append(" ".join(mots_originaux))
    
    variations = list(dict.fromkeys(variations))
    variations = [v for v in variations if len(v) > 3]
    print(f"📝 Variations à essayer: {variations[:3]}...")
    
    for i, var in enumerate(variations):
        print(f"🔍 Essai {i+1}/{len(variations)}: '{var}'")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(var, max_results=1))
                if results and len(results) > 0:
                    url = results[0].get("image")
                    if url and url.startswith("http"):
                        print(f"🖼️ IMAGE TROUVÉE avec '{var}'")
                        return url
        except Exception as e:
            print(f"   ⚠️ Erreur: {e}")
            continue
    
    if mots_cles:
        dernier_essai = mots_cles[0]
        print(f"🔍 Dernier essai: '{dernier_essai}'")
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(dernier_essai, max_results=1))
                if results and len(results) > 0:
                    url = results[0].get("image")
                    if url and url.startswith("http"):
                        print(f"🖼️ IMAGE TROUVÉE avec dernier essai")
                        return url
        except Exception as e:
            print(f"   ⚠️ Erreur: {e}")
    
    print("❌ AUCUNE IMAGE TROUVÉE")
    return None

# ------------------------------------------------------------
# Appel à Groq avec prompt structuré et extraction du nom
# ------------------------------------------------------------
async def appeler_groq(question):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = """
Tu es un expert en cuisine africaine et en solutions médicinales à base de plantes (WhatAPlant). Pour la requête de l'utilisateur, réponds UNIQUEMENT au format JSON suivant :
{
    "nom": "nom précis du plat ou de la plante (ex: sauce graine, foutou, tisane de menthe)",
    "contenu": "une réponse TRÈS DÉTAILLÉE et PRÉCISE, structurée ainsi :\\n- **Origine et contexte** (d'où vient ce plat/remède, traditions)\\n- **Ingrédients** (liste à puces, quantités approximatives si possible)\\n- **Préparation** (étapes numérotées, avec temps de cuisson, températures, astuces de chef)\\n- **Conseils de dégustation ou d'utilisation** (accompagnements, moment de la journée, conservation)\\n- **Variantes éventuelles** (selon les régions ou les ingrédients disponibles)\\n- **Bienfaits ou précautions** (si pertinent, pour les plantes médicinales)",
    "image_prompt": "description en anglais simple pour chercher une image (ex: 'sweet potato leaves stew', 'mint plant')"
}
Utilise un ton chaleureux, pédagogue et très descriptif. Donne des détails concrets : temps de cuisson, quantités, textures, couleurs. Si tu parles d'un remède, précise les posologies et contre-indications. Sois précis comme un grand chef ou un herboriste expérimenté.
"""

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.6,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            data = response.json()
            content = data['choices'][0]['message']['content']
            result = json.loads(content)
            nom = result.get("nom", question)
            contenu = result.get("contenu", "Désolé, je n'ai pas de réponse.")
            image_prompt = result.get("image_prompt", nom)
            
            # Recherche d'abord avec nom, puis avec image_prompt
            image_url = chercher_image_wikimedia_robuste(nom)
            if not image_url:
                image_url = chercher_image_wikimedia_robuste(image_prompt)
            
            return contenu, image_url
    except Exception as e:
        print(f"❌ Erreur Groq: {e}")
        return "Désolé, une erreur technique est survenue.", None
    
async def analyser_plante(nom_plante: str):
    """
    Appelle Groq pour obtenir l'analyse détaillée d'une plante.
    Retourne un dictionnaire JSON (ou None en cas d'erreur).
    """
    prompt = f"""Tu es un expert en botanique. Analyse la plante suivante : "{nom_plante}".
Réponds UNIQUEMENT au format JSON suivant, sans aucun texte avant ou après :
{{
  "sante": {{
    "etat": "bonne sante ou description de la maladie detectee",
    "symptomes": "symptomes de la maladie si applicable",
    "traitements_naturels": "traitements naturels recommandes",
    "traitements_chimiques": "traitements chimiques recommandes"
  }},
  "comestible": {{
    "oui_non": "oui / non / partiellement",
    "parties_comestibles": "feuilles, fruits, racines...",
    "recettes": "idees de recettes simples",
    "precautions": "precautions a prendre"
  }},
  "medicinale": {{
    "usages": "usages traditionnels documentes",
    "posologie": "posologie de base",
    "contre_indications": "contre-indications"
  }},
  "toxicite": {{
    "niveau": "faible / moyen / eleve",
    "symptomes": "symptomes d'intoxication",
    "premiers_secours": "premiers secours en cas d'ingestion"
  }},
  "nuisibilite": {{
    "invasive": "oui / non",
    "impact": "impact sur l'environnement, le sol ou les cultures"
  }}
}}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 800,
        "response_format": {"type": "json_object"}
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                return json.loads(content)   # retourne directement le dict
            else:
                print(f"Erreur Groq analyse: {response.status_code}")
                return None
    except Exception as e:
        print(f"Exception dans analyser_plante: {e}")
        return None