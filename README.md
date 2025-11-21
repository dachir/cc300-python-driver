# CC300 Python Driver

Un driver Python FastAPI pour communiquer avec le module électronique de contrôle de facturation CC300 de la DGI (Benin).

## Description

Ce driver est un serveur HTTP REST qui permet de communiquer avec l'équipement CC300 via port série. Il reçoit les commandes par HTTP et les exécute sur l'équipement connecté, puis fournit le résultat en réponse à la requête HTTP.

## Spécifications

- **Protocole**: HTTP/REST
- **Format de données**: JSON
- **Port**: 38917
- **Endpoint**: `http://localhost:38917`

## Installation

### Prérequis

- Python 3.8 ou supérieur
- Port série USB disponible pour la connexion au device CC300
- Driver USB pour l'équipement CC300 (VID: 03EB, PID: 6119)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

## Utilisation

### Démarrer le serveur

```bash
python main.py
```

Le serveur démarre sur `http://localhost:38917`

Ou avec uvicorn directement:

```bash
uvicorn main:app --host 0.0.0.0 --port 38917
```

### Documentation API

Une fois le serveur démarré, la documentation interactive est accessible sur:
- Swagger UI: `http://localhost:38917/docs`
- ReDoc: `http://localhost:38917/redoc`

## Endpoints API

### 1. CHECK - Vérifier la connexion du périphérique

**Endpoint**: `GET /check`

Permet de vérifier si le périphérique CC300 est connecté à l'ordinateur.

**Réponse**:
- **200 OK**: Équipement connecté
  ```json
  {"status": "Ready"}
  ```
- **503 Service Unavailable**: Équipement non connecté
  ```json
  {"status": "DeviceNotConnected"}
  ```

**Exemple**:
```bash
curl http://localhost:38917/check
```

### 2. INFO - Obtenir les informations du périphérique

**Endpoint**: `GET /info`

Permet d'avoir des informations sur l'équipement et sur le contribuable.

**Note**: Cette requête prend environ 4 secondes pour s'exécuter.

**Réponse**:
- **200 OK**: Informations de l'équipement
  ```json
  {
    "NIM": "ED04000623",
    "IFU": "3201910768821",
    "TIME": "2020-05-03 13:24:18 +0100 WAT",
    "COUNTER": "45",
    "SellBillCounter": "40",
    "SettlementBillCounter": "0",
    "TaxA": "0.00",
    "TaxB": "18.00",
    "TaxC": "0.00",
    "TaxD": "18.00",
    "CompanyName": "BFT",
    "CompanyLocationAddress": "RUE 12.170 12 IEME ARRONDISSEMENT",
    "CompanyLocationCity": "COTONOU",
    "CompanyContactPhone": "61006060",
    "CompanyContactEmail": "contact@bftgroup.co",
    "LastConnectionToServer": "2020-05-03 13:23:31 +0100 WAT",
    "DocumentOnDeviceCount": "45",
    "UploadedDocumentCount": "45"
  }
  ```
- **503 Service Unavailable**: Équipement non connecté

**Exemple**:
```bash
curl http://localhost:38917/info
```

### 3. BILL - Créer une facture

**Endpoint**: `POST /bill`

Permet de créer une facture sur l'équipement CC300.

**Corps de la requête**: JSON conforme au schéma défini dans `bill.spec.json`

**Exemple de facture de vente**:
```json
{
  "seller_id": "SELLER123",
  "seller_name": "Mon Magasin",
  "vt": "FV",
  "payments": [
    {
      "mode": "E",
      "amount": 1000.0
    }
  ],
  "products": [
    {
      "label": "Produit Test",
      "tax": "B",
      "price": 1000.0,
      "items": 1.0
    }
  ],
  "buyer_ifu": "1234567890",
  "buyer_name": "Client Test",
  "aib": "N/A"
}
```

**Exemple de facture d'avoir**:
```json
{
  "seller_id": "SELLER123",
  "seller_name": "Mon Magasin",
  "rt": "FA",
  "rn": "ED04000623-123",
  "payments": [
    {
      "mode": "E",
      "amount": 500.0
    }
  ],
  "products": [
    {
      "label": "Remboursement",
      "tax": "B",
      "price": 500.0
    }
  ]
}
```

**Réponse**:
- **200 OK**: Facture créée avec succès
  ```json
  {
    "qr_code": "F;ED04000623;NW34NID6ZHANFNMZ2IU7LL3H;3201910768821;20200503135002"
  }
  ```
- **400 Bad Request**: Données de facture invalides
- **503 Service Unavailable**: Équipement non connecté

**Exemple**:
```bash
curl -X POST http://localhost:38917/bill \
  -H "Content-Type: application/json" \
  -d @bill_example.json
```

## Validation du schéma JSON

Le schéma JSON pour les factures est défini dans `bill.spec.json`. Vous pouvez valider vos données JSON avec des outils comme:
- https://www.jsonschemavalidator.net/
- `jsonschema` Python library (utilisé par l'API)

## Structure du projet

```
cc300-python-driver/
├── main.py              # Application FastAPI principale
├── device.py            # Module de communication série
├── commands.py          # Commandes du périphérique CC300
├── models.py            # Modèles Pydantic
├── bill.spec.json       # Schéma JSON pour les factures
├── requirements.txt     # Dépendances Python
└── README.md           # Cette documentation
```

## Architecture technique

### Communication série

Le driver utilise `pyserial` pour communiquer avec l'équipement CC300 via le protocole propriétaire Eltrade:

- **Baudrate**: 115200
- **Data bits**: 8
- **Stop bits**: 1
- **Parity**: None
- **Timeout**: 0.5s

### Format de message

**Requête**: `<SOH><LEN><SEQ><CMD><DATA><AMB><BCC><ETX>`
**Réponse**: `<SOH><LEN><SEQ><CMD><DATA><BRK><STATUS><AMB><BCC><ETX>`

## Développement

### Structure du code

- `device.py`: Gestion de la connexion série et du protocole bas niveau
- `commands.py`: Implémentation des commandes haut niveau (info, bill)
- `models.py`: Modèles Pydantic pour validation et documentation
- `main.py`: Routes FastAPI et logique de l'API REST

### Tests

Pour tester l'API sans équipement réel, vous pouvez:
1. Vérifier la documentation: `http://localhost:38917/docs`
2. Utiliser les exemples de requêtes fournis
3. Simuler les réponses de l'équipement (mock)

## Dépannage

### L'équipement n'est pas détecté

1. Vérifiez que l'équipement CC300 est connecté via USB
2. Vérifiez que les drivers USB sont installés
3. Vérifiez les permissions du port série (Linux: ajoutez l'utilisateur au groupe `dialout`)
4. Vérifiez les logs du serveur pour plus de détails

### Erreur de communication

1. Vérifiez que le baudrate est correct (115200)
2. Vérifiez qu'aucune autre application n'utilise le port série
3. Essayez de redémarrer l'équipement CC300

## Référence

Ce driver est une implémentation Python du driver original en Go:
https://github.com/dachir/eltrade-cc300-driver

## Licence

Ce projet est fourni tel quel, sans garantie.
