import streamlit as st
from web3 import Web3
from decimal import Decimal
import json 

# Connect to Ethereum (testnet) via Infura or your own node
infura_url = "https://sepolia.infura.io/v3/02e9440d86d543cb816086f31105ff9e"
w3 = Web3(Web3.HTTPProvider(infura_url))

with open("abi.json", "r") as file:  # Vérifie que ce fichier existe dans le même dossier
    abi = json.load(file)

# Make sure connected to Ethereum
if not w3.is_connected():
    st.error("Ethereum node connection failed")
    st.stop()

# Your smart contract's 0x6cdcdba444d203532573d0830c02b55dea6e4665 and Address (replace with your contract's ABI and deployed address)
contract_address = "0x0235a4A62d298b491b1C71C558A5bd0f2c6335E7"
contract_abi = abi

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Add your wallet's private key here (for signing transactions)
private_key = st.sidebar.text_input("Clé privée (utilisateur)", type="password")

account = w3.eth.account.from_key(private_key)

# Function to send a transaction to the Ethereum network
def send_transaction(txn):
    signed_txn = w3.eth.account.sign_transaction(txn, private_key)
    txn_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    return txn_hash

def get_contraparty_data(address):
    try:
        # Fetch the counterparty data
        contra_data = contract.functions.contreparties(address)(address).call()
        
        # Check if the counterparty is active
        if not contra_data[5]:  # `estActif` is the 6th element (index 5)
            return {"error": "Counterparty does not exist or is inactive."}
        
        # Return the data in a structured format
        return {
            "portefeuille": contra_data[0],
            "scoreCredit": contra_data[1],
            "limiteExposition": contra_data[2],
            "expositionCourante": contra_data[3],
            "collateral": contra_data[4],
            "estActif": contra_data[5]
        }
    except Exception as e:
        return {"error": str(e)}
 
# Streamlit UI
st.title('Gestionnaire Risque Contrepartie')

# 1. Add a Counterparty
st.header('Add Counterparty')
portefeuille = st.text_input('Portefeuille Address')
score_credit = st.number_input('Score de Credit', min_value=0)
limite_exposition = st.number_input('Limite d\'Exposition', min_value=0)
collateral = st.number_input('Collateral', min_value=0)

if st.button('Ajouter Contrepartie'):
    if portefeuille and score_credit > 0 and limite_exposition > 0:
        txn = contract.functions.ajouterContrepartie(
            portefeuille, score_credit, limite_exposition, collateral
        ).build_transaction({
            'chainId': 11155111,  # Sepolia testnet
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
        })
        txn_hash = send_transaction(txn)
        st.success(f'Contrepartie ajoutée! Transaction Hash: {txn_hash.hex()}')

# 2. Disable a Counterparty
st.header('Desactiver une Contrepartie')
desactiver_address = st.text_input('Portefeuille Address (à désactiver)')

if st.button('Desactiver Contrepartie'):
    if desactiver_address:
        txn = contract.functions.desactiverContrepartie(desactiver_address).build_transaction({
            'chainId': 11155111,
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
        })
        txn_hash = send_transaction(txn)
        st.success(f'Contrepartie désactivée! Transaction Hash: {txn_hash.hex()}')

# 3. Update a Counterparty
st.header('Mettre à jour une Contrepartie')
update_address = st.text_input('Portefeuille Address (à mettre à jour)')
new_score_credit = st.number_input('Nouveau Score de Credit', min_value=0)
new_limite_exposition = st.number_input('Nouvelle Limite d\'Exposition', min_value=0)

if st.button('Mettre à jour Contrepartie'):
    if update_address:
        txn = contract.functions.mettreAJourContrepartie(
            update_address, new_limite_exposition, new_score_credit
        ).build_transaction({
            'chainId': 11155111,
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
        })
        txn_hash = send_transaction(txn)
        st.success(f'Contrepartie mise à jour! Transaction Hash: {txn_hash.hex()}')

# 4. Add Exposition
st.header('Ajouter Exposition')
contrepartie_address = st.text_input('Portefeuille Contrepartie')
autre_address = st.text_input('Autre Portefeuille')
position = st.number_input('Position', min_value=-1000000, max_value=1000000)

if st.button('Ajouter Exposition'):
    if contrepartie_address and autre_address:
        txn = contract.functions.ajouterExposition(
            contrepartie_address, autre_address, position
        ).build_transaction({
            'chainId': 11155111,
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account.address),
        })
        txn_hash = send_transaction(txn)
        st.success(f'Exposition ajoutée! Transaction Hash: {txn_hash.hex()}')

# 5. Get Counterparty Data
st.header('Obtenir Données de Contrepartie')
check_address = st.text_input('Portefeuille Address (à vérifier)')

if st.button('Obtenir Données'):
    if check_address:
        data = get_contraparty_data(check_address)
        st.write(data)

# Additional functionality like Removing Exposition and Calculating Net Exposure
