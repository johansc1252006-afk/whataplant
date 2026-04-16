import httpx
import json
import db_config
from ddgs import DDGS
import os 

from config import GROQ_API_KEY


# ============================================
# CONFIGURATION GROQ
# ============================================

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ============================================
# FONCTION DUCKDUCKGO IMAGE SEARCH
# ============================================
def chercher_image_duckduckgo(query):
    """Cherche une image via DuckDuckGo avec plusieurs stratégies génériques"""
    print(f"🔍 DuckDuckGo: {query[:50]}...")
    
    if not query or len(query) < 3:
        print("❌ Query trop courte")
        return None
    
    # ============================================
    # STRATÉGIE 1: Nettoyer et simplifier la requête
    # ============================================
    # Mots communs à enlever (indépendants du contexte)
    mots_a_enlever = [
        "stew", "sauce", "dish", "recipe", "african", "traditional", 
        "leaves", "leaf", "fresh", "green", "cooked", "preparation",
        "how", "to", "make", "with", "and", "for", "the", "from",
        "version", "recipe", "plate", "food", "meal", "cooking",
        "simple", "easy", "delicious", "homemade", "authentic"
    ]
    
    # Nettoyer la requête
    query_simple = query.lower()
    for mot in mots_a_enlever:
        query_simple = query_simple.replace(mot, "")
    query_simple = " ".join(query_simple.split())
    
    # ============================================
    # STRATÉGIE 2: Extraire les mots clés
    # ============================================
    mots_cles = [w for w in query_simple.split() if len(w) > 3]
    if not mots_cles:
        mots_cles = [w for w in query.split() if len(w) > 3]
    
    # ============================================
    # STRATÉGIE 3: Créer des variations de recherche
    # ============================================
    variations = []
    
    # Variation 1: requête simplifiée
    if query_simple and len(query_simple) > 3:
        variations.append(query_simple)
    
    # Variation 2: combinaisons de mots clés
    if len(mots_cles) >= 2:
        variations.append(f"{mots_cles[0]} {mots_cles[1]}")
        variations.append(f"{mots_cles[0]} {mots_cles[1]} food")
    elif len(mots_cles) == 1:
        variations.append(f"{mots_cles[0]} food")
        variations.append(f"{mots_cles[0]} cuisine")
    
    # Variation 3: mots clés séparés
    for mot in mots_cles[:2]:
        variations.append(mot)
    
    # Variation 4: requête originale courte
    mots_originaux = query.lower().split()[:3]
    if mots_originaux:
        variations.append(" ".join(mots_originaux))
    
    # Supprimer les doublons et les requêtes trop courtes
    variations = list(dict.fromkeys(variations))
    variations = [v for v in variations if len(v) > 3]
    
    print(f"📝 Variations à essayer: {variations[:3]}...")
    
    # ============================================
    # ESSAYER CHAQUE VARIATION
    # ============================================
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
    
    # ============================================
    # STRATÉGIE 4: Dernier essai avec le premier mot clé
    # ============================================
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

# ============================================
# FONCTION PRINCIPALE GROQ
# ============================================
async def appeler_groq(question, user_id):
    """
    Appelle Groq et gère cache + historique
    """
    print(f"\n📝 Question: {question[:80]}...")
    print(f"👤 User ID: {user_id}")
    
    # 1. Vérifier dans l'historique de l'utilisateur
    try:
        existe = db_config.chercher_historique(user_id, question)
        if existe:
            print(f"✅ Trouvé dans historique!")
            return existe["reponse"], existe["image_url"]
    except Exception as e:
        print(f"⚠️ Erreur chercher_historique: {e}")
    
    # 2. Appeler Groq
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": """Tu es WhatAPlant 🌿, un assistant expert en plantes médicinales ET en recettes de cuisine.

Tu dois répondre UNIQUEMENT au format JSON suivant:
{
    "reponse": "ta réponse textuelle ici",
    "nom_plante": "nom de la plante principale",
    "type": "plante ou recette",
    "image_prompt": "description en anglais pour chercher une image"
}

RÈGLES SELON LE TYPE DE QUESTION:

1. SI l'utilisateur demande une RECETTE DE CUISINE (même avec une plante médicinale):
   - type = "recette"
   - reponse: nom de la recette + ingrédients COMPLETS + étapes DÉTAILLÉES + temps cuisson
   - image_prompt: description du PLAT FINI en anglais simple
     Exemples:
     * "sauce feuille patate" → "sweet potato leaves stew"
     * "tisane menthe" → "mint tea herbal drink"
     * "sauce graine palmier" → "palm nut soup"

2. SI l'utilisateur demande les BIENFAITS, PROPRIÉTÉS ou UTILISATION MÉDICINALE:
   - type = "plante"
   - reponse: propriétés médicinales + bienfaits + mode d'utilisation + précautions
   - image_prompt: description de la PLANTE en anglais
     Exemples:
     * "menthe bienfaits" → "mint plant fresh leaves"
     * "feuille patate médicinale" → "sweet potato leaves plant"

RÈGLES POUR IMAGE_PROMPT:
- Toujours en anglais
- Simple et court (max 50 caractères)
- Pas de mots compliqués
- Pour les recettes → décrire le plat
- Pour les plantes → décrire la plante

RÈGLES GÉNÉRALES:
- Réponds toujours en français
- Sois complet et précis
- Max 500 mots"""
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "response_format": {"type": "json_object"}
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                print(f"📝 Groq réponse: {text[:200]}...")
                
                # Extraire le JSON
                try:
                    result = json.loads(text)
                except:
                    debut = text.find("{")
                    fin = text.rfind("}") + 1
                    if debut != -1 and fin > debut:
                        result = json.loads(text[debut:fin])
                    else:
                        return text, None

                reponse = result.get("reponse", "Désolé, je n'ai pas pu traiter ta demande.")
                nom_plante = result.get("nom_plante", "").lower()
                type_reponse = result.get("type", "plante")
                image_prompt = result.get("image_prompt", "")
                
                print(f"🌿 Nom plante: {nom_plante}")
                print(f"📷 Image prompt: {image_prompt}")
                
                image_url = None
                
                # 3. Chercher dans le cache (images_plantes)
                if nom_plante:
                    try:
                        image_url = db_config.chercher_image_locale(nom_plante, type_reponse)
                        if image_url:
                            print(f"✅ Image trouvée dans cache local")
                    except Exception as e:
                        print(f"⚠️ Erreur chercher_image_locale: {e}")
                
                # 4. Pas trouvée → DuckDuckGo
                if not image_url and image_prompt and len(image_prompt) > 5:
                    print(f"🔍 Appel DuckDuckGo avec: {image_prompt}")
                    # Note: chercher_image_duckduckgo n'est pas async, on l'exécute dans un thread
                    import asyncio
                    image_url = await asyncio.to_thread(chercher_image_duckduckgo, image_prompt)
                    
                    if image_url and nom_plante:
                        try:
                            db_config.sauvegarder_image_google(nom_plante, type_reponse, image_url)
                            print(f"💾 Image sauvegardée dans cache")
                        except Exception as e:
                            print(f"⚠️ Erreur sauvegarde cache: {e}")
                
                # 5. Sauvegarder dans l'historique
                try:
                    db_config.sauvegarder_conversation(user_id, question, reponse, image_url)
                    print(f"💾 Conversation sauvegardée")
                except Exception as e:
                    print(f"⚠️ Erreur sauvegarde historique: {e}")
                
                return reponse, image_url
            else:
                print(f"❌ Erreur Groq: {response.status_code}")
                return f"🌿 Erreur API ({response.status_code})", None
                
    except httpx.TimeoutException:
        print("❌ Timeout Groq")
        return "🌿 Le service met trop de temps à répondre.", None
    except Exception as e:
        print(f"❌ Erreur Groq: {e}")
        return "🌿 Une erreur technique est survenue.", None