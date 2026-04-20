from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import db_config
from db_config import get_db_connection
import grok_client 
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles pour les requêtes
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    nom: str
    email: str
    password: str

class UserRequest(BaseModel):
    user_id: int

# ============================================
# ROUTES DE CONNEXION (Restaurées)
# ============================================

@app.post("/login")
async def login(request: LoginRequest):
    # Appelle la fonction verifier_login que tu as dans db_config
    resultat = db_config.verifier_login(request.email, request.password)
    return resultat

@app.post("/register")
async def register(request: RegisterRequest):
    # Appelle la fonction creer_compte que tu as dans db_config
    resultat = db_config.creer_compte(request.nom, request.email, request.password)
    return resultat

# ============================================
# ROUTE DE CHAT IA
# ============================================

@app.post("/chat")
async def chat_bot(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        question = data.get("question")

        # 1. Appel du client Groq & Wikimedia
        reponse_ia, image_url = await grok_client.appeler_groq(question)

        # 2. Sauvegarde dans la base de données
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO historique_conversations (user_id, question, reponse, image_url) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, question, reponse_ia, image_url))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ Historique stocké pour l'user {user_id}")
        except Exception as db_err:
            print(f"❌ Erreur Stockage Base: {db_err}")

        return {
            "status": "success", 
            "reponse": reponse_ia, 
            "image_url": image_url
        }
    except Exception as e:
        print(f"❌ Erreur Route Chat: {str(e)}")
        return {"status": "error", "message": str(e)}

# ============================================
# ROUTE HISTORIQUE
# ============================================

@app.post("/historique-ia")
async def get_historique_ia(request: UserRequest):
    try:
        # On récupère les données via db_config
        conversations = db_config.get_user_conversations(request.user_id)
        
        # Ce print s'affichera dans ton terminal Python pour nous aider à débugger
        print(f"--- Debug Historique IA ---")
        print(f"User ID reçu: {request.user_id}")
        print(f"Nombre de conversations trouvées: {len(conversations)}")
        
        return {
            "status": "success", 
            "conversations": conversations
        }
    except Exception as e:
        print(f"❌ Erreur Route Historique IA: {str(e)}")
        return {"status": "error", "message": str(e), "conversations": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

@app.get("/scans/{user_id}")
async def get_scans(user_id: int):
    # On récupère les données via la fonction corrigée au-dessus
    scans = db_config.get_historique_scans(user_id)
    # Le JS attend la clé "scans" et un status "success"
    return {
        "status": "success",
        "scans": scans
    }

# ============================================
# ROUTE POUR SAUVEGARDER UN SCAN
# ============================================
@app.post("/save-scan")
async def save_scan(request: Request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        nom_plante = data.get('nom_plante')
        nom_scientifique = data.get('nom_scientifique')
        famille = data.get('famille')
        score = data.get('score')
        details = data.get('details')
        image_url = data.get('image_url')
        
        result = db_config.sauvegarder_scan(
            user_id, nom_plante, nom_scientifique,
            famille, score, details, image_url
        )
        return result
    except Exception as e:
        print(f"❌ Erreur sauvegarde scan: {e}")
        return {"status": "error", "message": str(e)}
    
@app.post("/analyze-plant")
async def analyze_plant(request: Request):
    try:
        data = await request.json()
        nom_plante = data.get("nom_plante")
        if not nom_plante:
            return {"status": "error", "message": "Nom de plante manquant"}
        analyse = await grok_client.analyser_plante(nom_plante)
        if analyse is None:
            return {"status": "error", "message": "L'analyse a échoué"}
        return {"status": "success", "analyse": analyse}
    except Exception as e:
        print(f"❌ Erreur /analyze-plant: {e}")
        return {"status": "error", "message": str(e)}