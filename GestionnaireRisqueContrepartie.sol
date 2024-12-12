// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract GestionnaireRisqueContrepartie {

    // Structure pour stocker les informations d'une contrepartie
    struct Contrepartie {
        address portefeuille;
        uint256 scoreCredit;
        uint256 limiteExposition;
        uint256 expositionCourante;
        uint256 collateral;
        bool estActif;
    }

    struct ExpositionIndividuelle {
        address contrepartie;
        int256 position;
    }

    mapping(address => Contrepartie) public contreparties;
    mapping(address => ExpositionIndividuelle[]) public expositions;

    // Événements
    event ContrepartieAjoutee(address indexed contrepartie, uint256 limiteExposition);
    event ContrepartieDesactivee(address indexed contrepartie);
    event ContrepartieMiseAJour(address indexed contrepartie, uint256 nouvelleLimite, uint256 nouveauScoreCredit);
    event ExpositionAjoutee(address indexed contrepartie, address autre, int256 position);
    event ExpositionSupprimee(address indexed contrepartie, uint256 index);
    event LimiteDepassee(address indexed contrepartie, int256 expositionNette);

    modifier contrepartieExistante(address _contrepartie) {
        require(contreparties[_contrepartie].estActif, "Contrepartie inactive ou inexistante");
        _;
    }

    // Ajouter une contrepartie
    function ajouterContrepartie(
        address _portefeuille, 
        uint256 _scoreCredit, 
        uint256 _limiteExposition, 
        uint256 _collateral
    ) public {
        require(contreparties[_portefeuille].portefeuille == address(0), "Contrepartie deja existante");
        require(_scoreCredit > 0 && _limiteExposition > 0, "Score de credit et limite doivent etre positifs");

        contreparties[_portefeuille] = Contrepartie({
            portefeuille: _portefeuille,
            scoreCredit: _scoreCredit,
            limiteExposition: _limiteExposition,
            expositionCourante: 0,
            collateral: _collateral,
            estActif: true
        });

        emit ContrepartieAjoutee(_portefeuille, _limiteExposition);
    }

    // Désactiver une contrepartie
    function desactiverContrepartie(address _contrepartie) public contrepartieExistante(_contrepartie) {
        contreparties[_contrepartie].estActif = false;
        emit ContrepartieDesactivee(_contrepartie);
    }

    // Mettre à jour les limites et scores de crédit
    function mettreAJourContrepartie(
        address _contrepartie,
        uint256 _nouvelleLimite,
        uint256 _nouveauScoreCredit
    ) public contrepartieExistante(_contrepartie) {
        require(_nouvelleLimite > 0 && _nouveauScoreCredit > 0, "Les valeurs doivent etre positives");
        contreparties[_contrepartie].limiteExposition = _nouvelleLimite;
        contreparties[_contrepartie].scoreCredit = _nouveauScoreCredit;
        emit ContrepartieMiseAJour(_contrepartie, _nouvelleLimite, _nouveauScoreCredit);
    }

    // Ajouter une exposition
    function ajouterExposition(
        address _contrepartie, 
        address _autre, 
        int256 _position
    ) public contrepartieExistante(_contrepartie) {
        require(_position != 0, "Position ne peut pas etre nulle");
        require(expositions[_contrepartie].length < 100, "Nombre maximum d'expositions atteint");

        ExpositionIndividuelle memory expo = ExpositionIndividuelle({contrepartie: _autre, position: _position});
        expositions[_contrepartie].push(expo);
        emit ExpositionAjoutee(_contrepartie, _autre, _position);
    }

    // Supprimer une exposition par index
    function supprimerExposition(address _contrepartie, uint256 index) public contrepartieExistante(_contrepartie) {
        require(index < expositions[_contrepartie].length, "Index invalide");

        for (uint256 i = index; i < expositions[_contrepartie].length - 1; i++) {
            expositions[_contrepartie][i] = expositions[_contrepartie][i + 1];
        }
        expositions[_contrepartie].pop();
        emit ExpositionSupprimee(_contrepartie, index);
    }

    // Calculer l'exposition nette
    function calculerExpositionNette(address _contrepartie) public view contrepartieExistante(_contrepartie) returns (int256) {
        ExpositionIndividuelle[] memory liste = expositions[_contrepartie];
        int256 expositionNette = 0;

        for (uint256 i = 0; i < liste.length; i++) {
            expositionNette += liste[i].position;
        }

        return expositionNette;
    }

    // Vérifier et mettre à jour les positions
    function mettreAJourPositions(address _contrepartie) public contrepartieExistante(_contrepartie) {
        int256 expositionNette = calculerExpositionNette(_contrepartie);
        contreparties[_contrepartie].expositionCourante = uint256(expositionNette);

        if (uint256(expositionNette) > contreparties[_contrepartie].limiteExposition) {
            emit LimiteDepassee(_contrepartie, expositionNette);
        }
    }
}
