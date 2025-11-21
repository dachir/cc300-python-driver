# CC300 Python Driver API

Un driver Python basé sur FastAPI pour communiquer avec le dispositif de contrôle fiscal CC300 de la DGI (Direction Générale des Impôts) du Bénin.

## Description

Ce driver permet de communiquer en HTTP avec le module électronique de contrôle de facturation de la DGI. Il est basé sur [eltrade-cc300-driver](https://github.com/dachir/eltrade-cc300-driver) et reproduit les mêmes endpoints HTTP et schémas JSON, mais est entièrement implémenté en Python en utilisant FastAPI et pyserial.

## Caractéristiques

- **Protocole**: HTTP/REST
- **Format de données**: JSON
- **Port par défaut**: 38917
- **Communication**: pyserial (USB/Serial)
- **Framework**: FastAPI avec validation Pydantic

## Installation

### Prérequis

- Python 3.8 ou supérieur
- Dispositif CC300 connecté via USB

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

### Documentation interactive

Une fois le serveur démarré, accédez à la documentation interactive Swagger UI:
- **Swagger UI**: http://localhost:38917/docs
- **ReDoc**: http://localhost:38917/redoc

## Endpoints API

### 1. `/check` - Vérifier la connexion du dispositif

Vérifie si le périphérique CC300 est connecté à l'ordinateur.

**Méthode**: `GET`  
**URL**: `/check`

**Réponses**:
- **200 OK**: Dispositif connecté
  ```json
  {"status": "Ready"}
  ```
- **503 Service Unavailable**: Dispositif non connecté
  ```json
  {"status": "DeviceNotConnected"}
  ```

**Exemple cURL**:
```bash
curl http://localhost:38917/check
```

### 2. `/info` - Obtenir les informations du dispositif

Récupère les informations sur l'équipement et le contribuable.

**Note**: Cette requête prend environ 4 secondes pour s'exécuter.

**Méthode**: `GET`  
**URL**: `/info`

**Réponses**:
- **200 OK**: Informations du dispositif
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
- **503 Service Unavailable**: Dispositif non connecté
  ```json
  {"status": "DeviceNotConnected"}
  ```

**Exemple cURL**:
```bash
curl http://localhost:38917/info
```

### 3. `/bill` - Créer une facture

Crée une nouvelle facture sur le dispositif CC300.

**Méthode**: `POST`  
**URL**: `/bill`  
**Content-Type**: `application/json`

**Corps de la requête**:

Le corps doit respecter le schéma JSON défini dans `bill.spec.json`. Il existe deux types de factures:

#### Facture de vente (Sale Bill)
```json
{
  "seller_id": "SELLER123",
  "seller_name": "Ma Boutique",
  "vt": "FV",
  "buyer_ifu": "3201910768821",
  "buyer_name": "Client ABC",
  "aib": "N/A",
  "payments": [
    {
      "mode": "E",
      "amount": 10000
    }
  ],
  "products": [
    {
      "label": "Produit Example",
      "tax": "B",
      "price": 10000,
      "items": 1.0
    }
  ]
}
```

#### Facture d'avoir (Refund Bill)
```json
{
  "seller_id": "SELLER123",
  "seller_name": "Ma Boutique",
  "rt": "FA",
  "rn": "ED04000623-12345",
  "buyer_ifu": "3201910768821",
  "buyer_name": "Client ABC",
  "aib": "N/A",
  "payments": [
    {
      "mode": "E",
      "amount": 10000
    }
  ],
  "products": [
    {
      "label": "Produit Example",
      "tax": "B",
      "price": 10000
    }
  ]
}
```

**Modes de paiement**:
- `V`: Virement
- `C`: Carte bancaire
- `M`: Mobile money
- `D`: Chèques
- `E`: Espèces (cash)
- `A`: Autre

**Types de taxes**:
- `A`: Exonéré
- `B`: Taxable
- `C`: Exportation de produits taxables
- `D`: TVA régime d'exception
- `E`: Régime fiscal TPS
- `F`: Taxe de séjour

**Types de factures de vente (vt)**:
- `FV`: Facture de vente
- `CV`: Copie de la dernière facture de vente
- `EV`: Facture de vente à l'exportation
- `EC`: Copie de la dernière facture de vente à l'exportation

**Types de factures d'avoir (rt)**:
- `FA`: Facture d'avoir
- `CA`: Copie de la dernière facture d'avoir
- `EA`: Facture d'avoir à l'exportation
- `ER`: Copie de la dernière facture d'avoir à l'exportation

**Réponses**:
- **200 OK**: Facture créée avec succès
  ```json
  {"qr_code": "F;ED04000623;NW34NID6ZHANFNMZ2IU7LL3H;3201910768821;20200503135002"}
  ```
- **400 Bad Request**: Erreurs de validation
- **503 Service Unavailable**: Dispositif non connecté

**Exemple cURL**:
```bash
curl -X POST http://localhost:38917/bill \
  -H "Content-Type: application/json" \
  -d '{
    "seller_id": "SELLER123",
    "seller_name": "Ma Boutique",
    "vt": "FV",
    "payments": [{"mode": "E", "amount": 10000}],
    "products": [{"label": "Produit", "tax": "B", "price": 10000}]
  }'
```

## Validation du schéma JSON

Utilisez le fichier `bill.spec.json` avec un validateur JSON comme [jsonschemavalidator.net](https://www.jsonschemavalidator.net/) pour valider vos données de facture avant de les envoyer à l'API.

## Structure du projet

```
cc300-python-driver/
├── main.py              # Application FastAPI principale
├── models.py            # Modèles Pydantic pour validation
├── device.py            # Communication série avec le dispositif CC300
├── commands.py          # Commandes de haut niveau
├── requirements.txt     # Dépendances Python
├── bill.spec.json       # Schéma JSON pour validation
└── README.md            # Documentation
```

## Développement

### Exécution en mode développement

```bash
uvicorn main:app --reload --port 38917
```

### Tests

Pour tester l'API sans dispositif physique, vous pouvez utiliser les endpoints de documentation interactive ou des outils comme Postman ou curl.

## Référence

Ce driver est basé sur l'implémentation Go originale: [dachir/eltrade-cc300-driver](https://github.com/dachir/eltrade-cc300-driver)

## Licence

Voir le dépôt de référence pour les informations de licence.
