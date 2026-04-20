import mysql.connector
import bcrypt # Pour la sécurité des mots de passe (remplace password_hash de PHP)
import os 

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST", "localhost"),
        user=os.getenv("MYSQLUSER", "root"),
        password=os.getenv("MYSQLPASSWORD", ""),
        database=os.getenv("MYSQLDATABASE", "whataplant"),
        port=os.getenv("MYSQLPORT", "3306")
    )

# ============================================
# GESTION DES UTILISATEURS (Remplace inscription/connexion.php)
# ============================================

def creer_compte(nom, email, password):
    """Inscrit un nouvel utilisateur avec mot de passe haché"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Vérifier si l'email existe déjà
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            conn.close()
            return {"status": "error", "message": "Cet email existe déjà"}
        
        # Hachage du mot de passe (compatible avec PHP BCRYPT)
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        sql = "INSERT INTO users (nom, email, password) VALUES (%s, %s, %s)"
        cursor.execute(sql, (nom, email, hashed_password.decode('utf-8')))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Compte créé avec succès !"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def verifier_login(email, password):
    """Vérifie les identifiants et retourne les infos user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return {
                "status": "success", 
                "user": {
                    "id": user['id'], 
                    "nom": user['nom'], 
                    "email": user['email']
                }
            }
        return {"status": "error", "message": "Email ou mot de passe incorrect"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================
# GESTION DES SCANS (Remplace save_scan.php)
# ============================================

def sauvegarder_scan(user_id, nom_plante, nom_scientifique, famille, score, details, image_url):
    """Sauvegarde un scan de plante dans la base"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """INSERT INTO historique_scans 
                 (user_id, nom_plante, nom_scientifique, famille, score, details, image_url) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, (user_id, nom_plante, nom_scientifique, famille, score, details, image_url))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return {"status": "success", "scan_id": last_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_historique_scans(user_id):
    """Récupère tous les scans d'un utilisateur avec les noms de colonnes exacts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Utilisation du nom de table exact : historique_scans
        sql = "SELECT * FROM historique_scans WHERE user_id = %s ORDER BY date_scan DESC"
        cursor.execute(sql, (user_id,))
        resultats = cursor.fetchall()
        
        # Formatage de la date pour le JS (date_scan)
        for row in resultats:
            if row['date_scan']:
                row['date_scan'] = row['date_scan'].strftime("%Y-%m-%d %H:%M")
        
        conn.close()
        return resultats
    except Exception as e:
        print(f"Erreur DB Scans: {e}")
        return []

# ============================================
# GESTION DES CONVERSATIONS IA (Tes fonctions originales)
# ============================================

def sauvegarder_conversation(user_id, question, reponse, image_url=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO historique_conversations (user_id, question, reponse, image_url) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (user_id, question, reponse, image_url))
    conn.commit()
    conn.close()

def chercher_historique(user_id, question):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT reponse, image_url FROM historique_conversations WHERE user_id = %s AND question = %s ORDER BY date_conversation DESC LIMIT 1"
    cursor.execute(sql, (user_id, question))
    resultat = cursor.fetchone()
    conn.close()
    if resultat:
        return {"reponse": resultat[0], "image_url": resultat[1]}
    return None

def get_user_conversations(user_id, limit=50):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) 
        
        # On s'assure de récupérer les colonnes exactes de ta table historique_conversations
        # Ton JS attend 'created_at' pour la date
        sql = """
            SELECT id, question, reponse, image_url, date_conversation as created_at 
            FROM historique_conversations 
            WHERE user_id = %s 
            ORDER BY date_conversation DESC LIMIT %s
        """
        cursor.execute(sql, (user_id, limit))
        resultats = cursor.fetchall()
        conn.close()
        
        # Formatage de la date pour éviter les erreurs d'affichage sur le mobile
        for row in resultats:
            if row['created_at']:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M")
            else:
                row['created_at'] = "Date inconnue"
                
        return resultats
    except Exception as e:
        print(f"❌ Erreur DB Historique IA: {e}")
        return []