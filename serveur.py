from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pyswip import Prolog
import logging
import traceback
import os


app = Flask(__name__)
CORS(app)

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialiser Prolog
prolog = Prolog()

def load_prolog_knowledge():
    """Charge la base de connaissances Prolog"""
    try:
        logger.info("Chargement de la base de connaissances Prolog...")
        
        # Nettoyer d'abord (au cas où)
        try:
            prolog.retractall("suspect(_)")
            prolog.retractall("crime_type(_)")
            prolog.retractall("has_motive(_, _)")
            prolog.retractall("was_near_crime_scene(_, _)")
            prolog.retractall("has_fingerprint_on_weapon(_, _)")
            prolog.retractall("has_bank_transaction(_, _)")
            prolog.retractall("owns_fake_identity(_, _)")
            prolog.retractall("eyewitness_identification(_, _)")
            prolog.retractall("is_guilty(_, _)")
        except:
            pass  # Normal si les prédicats n'existent pas encore

        # Types de crime
        prolog.assertz("crime_type(vol)")
        prolog.assertz("crime_type(assassinat)")
        prolog.assertz("crime_type(escroquerie)")

        # Suspects
        prolog.assertz("suspect(john)")
        prolog.assertz("suspect(mary)")
        prolog.assertz("suspect(alice)")
        prolog.assertz("suspect(bruno)")
        prolog.assertz("suspect(sophie)")

        # Motifs
        prolog.assertz("has_motive(john, vol)")
        prolog.assertz("has_motive(mary, assassinat)")
        prolog.assertz("has_motive(alice, escroquerie)")

        # Proximité de la scène de crime
        prolog.assertz("was_near_crime_scene(john, vol)")
        prolog.assertz("was_near_crime_scene(mary, assassinat)")

        # Empreintes digitales
        prolog.assertz("has_fingerprint_on_weapon(john, vol)")
        prolog.assertz("has_fingerprint_on_weapon(mary, assassinat)")

        # Transactions bancaires
        prolog.assertz("has_bank_transaction(alice, escroquerie)")
        prolog.assertz("has_bank_transaction(bruno, escroquerie)")

        # Fausse identité
        prolog.assertz("owns_fake_identity(sophie, escroquerie)")

        # Témoins oculaires
        prolog.assertz("eyewitness_identification(john, vol)")

        # Règles de culpabilité - Version sans duplicatas
        prolog.assertz("""
        is_guilty(Suspect, vol) :-
            suspect(Suspect),
            has_motive(Suspect, vol),
            was_near_crime_scene(Suspect, vol),
            (has_fingerprint_on_weapon(Suspect, vol) -> true ; eyewitness_identification(Suspect, vol))
        """)

        prolog.assertz("""
        is_guilty(Suspect, assassinat) :-
            suspect(Suspect),
            has_motive(Suspect, assassinat),
            was_near_crime_scene(Suspect, assassinat),
            (has_fingerprint_on_weapon(Suspect, assassinat) -> true ; eyewitness_identification(Suspect, assassinat))
        """)

        prolog.assertz("""
        is_guilty(Suspect, escroquerie) :-
            suspect(Suspect),
            has_motive(Suspect, escroquerie),
            (has_bank_transaction(Suspect, escroquerie) -> true ; owns_fake_identity(Suspect, escroquerie))
        """)

        logger.info("Base de connaissances Prolog chargée avec succès!")
        return True

    except Exception as e:
        logger.error(f"Erreur lors du chargement de la base de connaissances: {e}")
        logger.error(traceback.format_exc())
        return False

# Route principale - Page d'accueil
@app.route('/', methods=['GET'])
def home():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/query', methods=['POST', 'OPTIONS'])
def query():
    """Endpoint principal pour les requêtes Prolog"""
    if request.method == 'OPTIONS':
        # Réponse préflight CORS
        response = jsonify({'status': 'allowed'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    try:
        # Essayer de lire JSON
        data = request.get_json(silent=True)
        
        if not data:
            # Sinon, essayer en form-urlencoded
            data = request.form.to_dict()
        
        if not data:
            logger.error("Aucune donnée fournie (ni JSON, ni form)")
            return jsonify({'error': 'Aucune donnée fournie'}), 400
        
        # Extraire la requête
        query_str = data.get('query')
        if not query_str:
            logger.error("Champ 'query' manquant")
            return jsonify({'error': 'Champ \"query\" manquant'}), 400
        
        logger.info(f"Requête reçue: {query_str}")
        
        # Nettoyage de la requête
        query_str = query_str.strip()
        if not query_str.endswith('.'):
            query_str += '.'
        
        # Exécution Prolog
        try:
            results = list(prolog.query(query_str))
            logger.info(f"Résultats: {results}")
            
            if results:
                if any(isinstance(result, dict) and result for result in results):
                    processed_results = []
                    for result in results:
                        if isinstance(result, dict):
                            processed_results.append(result)
                        else:
                            processed_results.append({'result': str(result)})
                    return jsonify({
                        'success': True,
                        'results': processed_results,
                        'count': len(processed_results)
                    })
                else:
                    return jsonify({
                        'success': True,
                        'result': 'true',
                        'message': 'La requête est vraie'
                    })
            else:
                return jsonify({
                    'success': True,
                    'result': 'false',
                    'message': 'La requête est fausse'
                })
                
        except Exception as prolog_error:
            logger.error(f"Erreur Prolog: {prolog_error}")
            return jsonify({
                'error': 'Erreur dans la requête Prolog',
                'details': str(prolog_error),
                'query': query_str
            }), 400
            
    except Exception as e:
        logger.error(f"Erreur générale: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Erreur interne du serveur',
            'details': str(e)
        }), 500


@app.route('/test', methods=['GET'])
def test():
    """Endpoint de test pour vérifier le fonctionnement"""
    try:
        logger.info("Exécution des tests automatiques")
        
        # Test simple
        test_queries = [
            "suspect(john)",
            "is_guilty(john, vol)",
            "is_guilty(mary, assassinat)",
            "is_guilty(alice, escroquerie)"
        ]
        
        results = {}
        for query_str in test_queries:
            try:
                result = list(prolog.query(query_str))
                results[query_str] = {
                    'success': True,
                    'result': bool(result),
                    'details': result
                }
            except Exception as e:
                results[query_str] = {
                    'success': False,
                    'error': str(e)
                }
        
        return jsonify({
            'message': 'Tests effectués',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Erreur lors des tests: {e}")
        return jsonify({
            'error': 'Erreur lors des tests',
            'details': str(e)
        }), 500

@app.route('/reload', methods=['POST'])
def reload_knowledge():
    """Recharge la base de connaissances"""
    try:
        logger.info("Rechargement de la base de connaissances")
        
        # Recharger
        success = load_prolog_knowledge()
        
        if success:
            return jsonify({'message': 'Base de connaissances rechargée avec succès'})
        else:
            return jsonify({'error': 'Erreur lors du rechargement'}), 500
            
    except Exception as e:
        logger.error(f"Erreur lors du rechargement: {e}")
        return jsonify({
            'error': 'Erreur lors du rechargement',
            'details': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de santé"""
    try:
        # Test rapide de Prolog
        test_result = list(prolog.query("suspect(john)"))
        prolog_status = "OK" if test_result else "WARNING"
        
        return jsonify({
            'status': 'OK',
            'message': 'Serveur Prolog opérationnel',
            'prolog_status': prolog_status,
            'endpoints_available': ['/query', '/test', '/health', '/reload']
        })
    except Exception as e:
        logger.error(f"Erreur health check: {e}")
        return jsonify({
            'status': 'ERROR',
            'message': 'Erreur du serveur Prolog',
            'error': str(e)
        }), 500

# Gestion des erreurs 404
@app.errorhandler(404)
def not_found(error):
    logger.error(f"Route non trouvée: {request.url}")
    return jsonify({
        'error': 'Route non trouvée',
        'available_endpoints': {
            'GET /': 'Page d\'accueil',
            'POST /query': 'Exécuter une requête Prolog',
            'GET /health': 'Vérifier le statut du serveur',
            'GET /test': 'Tests automatiques',
            'POST /reload': 'Recharger la base de connaissances'
        },
        'requested_url': request.url
    }), 404

# Gestion des erreurs 500
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erreur interne: {error}")
    return jsonify({
        'error': 'Erreur interne du serveur',
        'message': 'Une erreur inattendue s\'est produite'
    }), 500

if __name__ == '__main__':
    print("=== SERVEUR CRIME DETECTIVE PROLOG ===")
    print("Démarrage du serveur Flask-Prolog...")
    
    # Charger la base de connaissances au démarrage
    if load_prolog_knowledge():
        print("✅ Base de connaissances chargée avec succès!")
        print("🚀 Serveur prêt!")
        print("📍 URL: http://127.0.0.1:5000")
        print("🌐 Interface: Ouvrez index.html dans votre navigateur")
        print("🔍 API: Utilisez /query pour les requêtes Prolog")
        print("\n--- Endpoints disponibles ---")
        print("GET  /         - Page d'accueil")
        print("POST /query    - Requêtes Prolog")
        print("GET  /health   - Statut serveur")
        print("GET  /test     - Tests automatiques")
        print("POST /reload   - Recharger base de données")
        print("\nCtrl+C pour arrêter le serveur")
        print("=" * 50)
        
        app.run(debug=True, host='127.0.0.1', port=5000)
    else:
        print("❌ Erreur: Impossible de charger la base de connaissances!")
        print("Vérifiez que SWI-Prolog est installé et accessible.")
        exit(1)