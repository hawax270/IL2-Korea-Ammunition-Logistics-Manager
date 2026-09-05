"""Catalogue de traduction."""

TEXTES = {'admin.daily.current_rate': 'TAUX ACTUEL : {value}',
 'admin.daily.description': 'Cette valeur s’applique à la carrière locale active.\n'
                            'Chaque journée réellement écoulée dans la campagne crédite automatiquement ce montant.',
 'admin.daily.rate_option': '{value} PT / JOUR',
 'admin.daily.saved_body': 'Nouveau gain : +{points} point par jour de campagne.',
 'admin.daily.saved_title': 'Gain journalier enregistré',
 'admin.daily.title': 'GAIN DE POINTS PAR JOUR',
 'admin.daily.window': 'Gain journalier de commandement',
 'admin.points.changed_body': 'Nouveau solde : {points} points.',
 'admin.points.changed_title': 'Points modifiés',
 'admin.points.description': 'Modification directe de la carrière locale.\nRéservé aux tests et à l’administration.',
 'admin.points.title': 'POINTS DE COMMANDEMENT',
 'admin.points.window': 'Points de commandement',
 'admin.required.body': 'Activez le MODE ADMIN depuis les options.',
 'admin.required.title': 'Mode Admin requis',
 'admin.reset_all.button': 'RÉINITIALISER TOUT',
 'admin.reset_all.description': 'Cette opération remet la carrière locale dans l’état d’une première installation du '
                                'logiciel.',
 'admin.reset_all.fail_body': 'La réinitialisation complète a échoué.\n\n{error}',
 'admin.reset_all.keep': 'SERONT CONSERVÉS : vos préréglages de mission et vos modèles de répartition personnalisés. '
                         'La base IL-2 n’est jamais modifiée.',
 'admin.reset_all.success_body': 'La carrière locale a été réinitialisée aux valeurs usine.\n'
                                 '\n'
                                 'Vos préréglages utilisateur ont été conservés.',
 'admin.reset_all.success_title': 'Carrière réinitialisée',
 'admin.reset_all.summary': 'APPAREIL : {aircraft}\nPÉRIODE : {period}\nRÉFÉRENCE IL-2 ammoQty : {ammo}',
 'admin.reset_all.title': 'RÉINITIALISATION COMPLÈTE',
 'admin.reset_all.will': 'SERONT RÉINITIALISÉS\n'
                         '\n'
                         '• stock concret de toutes les munitions\n'
                         '• historique des missions et consommations\n'
                         '• rapports et historique de ravitaillement\n'
                         '• boosts et modificateurs du Haut Commandement\n'
                         '• livraisons urgentes en cours ou terminées\n'
                         '• directives permanentes de répartition\n'
                         '• points de commandement → 1\n'
                         '• gain journalier de commandement → +1 pt/jour\n'
                         '• modèle actif → STANDARD\n'
                         '• paramètres logistiques → valeurs usine\n'
                         '• capacité et référence de synchronisation\n'
                         '• heure et préparation de mission courante',
 'admin.reset_all.window': 'Réinitialiser toute la carrière locale',
 'admin.reset_stock.body': 'Le stock sera recalculé à partir des valeurs STANDARD prévues pour cet appareil et cette '
                           'période.\n'
                           '\n'
                           'La base IL-2, ammoQty et sa référence de synchronisation ne seront pas modifiés.',
 'admin.reset_stock.button': 'RÉINITIALISER LE STOCK',
 'admin.reset_stock.description': 'Cette opération remplace entièrement les quantités actuelles du stock local.',
 'admin.reset_stock.fail_body': 'Impossible de réinitialiser le stock.\n\n{error}',
 'admin.reset_stock.success_body': 'Le stock de munitions a été remplacé par les valeurs STANDARD de la carrière '
                                   'active.',
 'admin.reset_stock.success_title': 'Stock réinitialisé',
 'admin.reset_stock.summary': 'APPAREIL : {aircraft}\nPÉRIODE : {period}',
 'admin.reset_stock.window': 'Réinitialiser le stock STANDARD',
 'admin.stock.confirm_body': 'Appliquer directement ces valeurs au stock local ?\n'
                             '\n'
                             'Cette opération est réservée au MODE ADMIN.',
 'admin.stock.confirm_title': 'Confirmer la modification',
 'admin.stock.description': 'MODE ADMIN • {aircraft} • Uniquement les munitions compatibles avec l’avion de la '
                            'carrière.\n'
                            'Ces valeurs modifient le stock local et n’altèrent jamais la base IL-2.',
 'admin.stock.invalid_body': 'Valeur incorrecte pour :\n{munition}\n\nEntrez un nombre entier positif ou nul.',
 'admin.stock.invalid_title': 'Stock invalide',
 'admin.stock.none': 'Aucune munition compatible détectée pour {aircraft}.',
 'admin.stock.save_button': 'ENREGISTRER LE STOCK',
 'admin.stock.saved_body': 'Les valeurs de stock ont été enregistrées.',
 'admin.stock.saved_title': 'Stock modifié',
 'admin.stock.title': 'MODIFICATION DIRECTE DU STOCK',
 'admin.stock.window': 'Modification directe du stock',
 'admin.value_invalid.body': 'Entrez un nombre positif ou nul, avec au maximum une décimale.',
 'admin.value_invalid.title': 'Valeur invalide',
 'app.title': 'GESTION DU STOCK DE MUNITIONS',
 'app.window_title': 'IL-2 Korea - Gestion du stock de munitions',
 'career.aircraft.empty': 'APPAREIL : —',
 'career.aircraft_unknown': 'APPAREIL : NON RECONNU  •  {config}',
 'career.aircraft_value': 'APPAREIL : {aircraft}',
 'career.ammo.empty': 'MUNITIONS IL-2 ACTUELLES : —',
 'career.analysis.title': 'ANALYSE DE LA CARRIÈRE',
 'career.analyzing': 'ANALYSE EN COURS...',
 'career.banner': 'LIAISON AVEC LA CARRIÈRE IL-2 KOREA',
 'career.choose': 'CHOISIR / CHANGER LA CARRIÈRE',
 'career.current_ammo': 'MUNITIONS IL-2 ACTUELLES : {qty} UNITÉS',
 'career.file_dialog': 'Sélectionner une carrière IL-2 Korea',
 'career.filetype.all': 'Tous les fichiers',
 'career.filetype.db': 'Base de carrière IL-2',
 'career.initialized': 'CARRIÈRE INITIALISÉE',
 'career.last.empty': 'DERNIÈRE LIVRAISON : —',
 'career.last_delivery': 'DERNIÈRE LIVRAISON : +{qty} UNITÉS  •  {date}',
 'career.last_none': 'DERNIÈRE LIVRAISON : AUCUN RAVITAILLEMENT MUNITIONS TROUVÉ',
 'career.none': 'AUCUNE CARRIÈRE SÉLECTIONNÉE',
 'career.read_only': 'CARRIÈRE ANALYSÉE EN LECTURE SEULE',
 'career.select.description': 'Sélectionnez le fichier .db de votre carrière pilote.\n'
                              'Le fichier est analysé en lecture seule : aucune donnée du jeu ne sera modifiée.',
 'career.select.title': 'SÉLECTION DE LA CARRIÈRE',
 'career.supplies.empty': 'RAVITAILLEMENTS MUNITIONS : —',
 'career.supply_summary': 'RAVITAILLEMENTS MUNITIONS : {count}  •  TOTAL HISTORIQUE : {total} UNITÉS',
 'career.waiting': 'EN ATTENTE D’UN FICHIER DE CARRIÈRE',
 'career.window': 'Liaison avec la carrière IL-2 Korea',
 'category.bombs': 'BOMBES',
 'category.napalm': 'NAPALM',
 'category.rockets': 'ROQUETTES',
 'category.special': 'SPÉCIAL',
 'category.tanks': 'RÉSERVOIRS',
 'common.active': 'ACTIF',
 'common.ammunition': 'MUNITION',
 'common.cancel': 'ANNULER',
 'common.close': 'FERMER',
 'common.continue': 'CONTINUER',
 'common.custom': 'PERSONNALISÉ',
 'common.error': 'Erreur',
 'common.month': 'MOIS',
 'common.no': 'NON',
 'common.ok': 'OK',
 'common.options': 'OPTIONS',
 'common.points': 'POINTS',
 'common.quit': 'QUITTER',
 'common.save': 'ENREGISTRER',
 'common.standard': 'STANDARD',
 'common.stock': 'STOCK',
 'common.validate': 'VALIDER',
 'common.warning': 'Attention',
 'common.year': 'ANNÉE',
 'common.yes': 'OUI',
 'delivery.delivered': 'LIVRÉE',
 'delivery.in_transit': 'EN TRANSIT',
 'delivery.large': 'GRANDE',
 'delivery.small': 'PETITE',
 'forecast.active_model': 'MODÈLE ACTIF',
 'forecast.base_share': 'base {value} %',
 'forecast.bonus_note': 'Répartition normale IL-2 + soutien du Haut Commandement.\n'
                        'Les bonus ne réduisent jamais les autres munitions.',
 'forecast.description': 'Anticipez les mois suivants et envoyez une demande au Haut Commandement uniquement en cas de '
                         'pénurie réelle.',
 'forecast.donut': 'RÉPARTITION + BONUS',
 'forecast.estimated': 'RÉPARTITION ESTIMÉE',
 'forecast.importance': 'IMPORTANCE LOGISTIQUE',
 'forecast.list_header': 'MUNITION • IMPORTANCE • PART ESTIMÉE',
 'forecast.modifiers.off': 'VISIBILITÉ MODIFICATEURS : OFF',
 'forecast.modifiers.on': 'VISIBILITÉ MODIFICATEURS : ON',
 'forecast.period_custom': 'PRESET PERSONNALISÉ',
 'forecast.period_standard': 'STANDARD HISTORIQUE',
 'forecast.request': '★  DEMANDE AU COMMANDEMENT',
 'forecast.subtitle': '{aircraft}  •  APERÇU DU PROCHAIN RAVITAILLEMENT',
 'forecast.title': 'RÉPARTITION PRÉVISIONNELLE DU STOCK',
 'forecast.window': 'Répartition du stock',
 'hc.action': 'ACTION DEMANDÉE',
 'hc.admin': '◆ MODE ADMIN ACTIF • CONTRAINTES DE TEST DÉVERROUILLÉES',
 'hc.admin.short': '∞ ADMIN',
 'hc.already_prioritized': 'DÉJÀ PRIORISÉE',
 'hc.balance': 'SOLDE DE POINTS DE COMMANDEMENT',
 'hc.boost.note': 'Les boosts sont une couche temporaire séparée du preset.\n'
                  'Ils n’altèrent jamais les données du modèle.',
 'hc.boost15': 'PRIORISATION ÉLEVÉE\n+15 % DE BOOST POUR CE MOIS\n{cost} POINTS',
 'hc.boost30': 'PRIORISATION TRÈS ÉLEVÉE\n+30 % DE BOOST POUR CE MOIS\n{cost} POINTS',
 'hc.confirm.delivery_body': '{munition}\n'
                             '\n'
                             'Période : {period}\n'
                             'Livraison : {size}\n'
                             'Quantité estimée : {minimum}–{maximum} unités\n'
                             'Délai : 2 à 3 jours de campagne\n'
                             'Coût : {cost}\n'
                             '\n'
                             'La quantité exacte ne sera révélée qu’à la réception.\n'
                             '\n'
                             'Confirmer cette demande ?',
 'hc.confirm.delivery_title': 'Confirmer la livraison urgente',
 'hc.confirm.request_body': '{munition}\n'
                            '\n'
                            'Période : {period}\n'
                            'Priorisation : +{value} %\n'
                            'Coût : {cost}\n'
                            '\n'
                            'Le bonus sera ajouté à la répartition normale sans réduire les autres munitions.\n'
                            '\n'
                            'Confirmer cette demande ?',
 'hc.confirm.request_title': 'Confirmer la demande',
 'hc.cost.admin': 'Coût : 0 point (MODE ADMIN).',
 'hc.cost.points': 'Coût : {cost} points de commandement.',
 'hc.costs': '+15% : {boost15}  •  +30% : {boost30}  •  URGENCES : {small}/{large}  •  DIRECTIVE : {directive} PTS',
 'hc.current_boost': 'Boost déjà accordé : +{boost} %',
 'hc.daily_gain': '+{gain} PT / JOUR DE CAMPAGNE',
 'hc.delivery.button': '{size}  •  {minimum}–{maximum}\n{cost} POINTS',
 'hc.delivery.in_progress.many': '★★  {count} LIVRAISONS EN COURS  •  {range}',
 'hc.delivery.in_progress.one': '★★  LIVRAISON EN COURS  •  {range}',
 'hc.delivery.scheduled': 'Livraison programmée',
 'hc.delivery.scheduled_body': '{munition}\n'
                               '\n'
                               'Livraison {size}\n'
                               'Quantité estimée : {minimum}–{maximum}\n'
                               '{cost}\n'
                               'Arrivée : {arrival}\n'
                               '\n'
                               'La quantité exacte sera révélée à la réception.',
 'hc.directive.active': '★★★  DIRECTIVE ACTIVE',
 'hc.directive.active_generic': 'DIRECTIVE ACTIVE',
 'hc.directive.active_text': 'DIRECTIVE N°{number} ACTIVE',
 'hc.directive.correct_programmed': 'CORRIGER LA DIRECTIVE PROGRAMMÉE',
 'hc.directive.correct_short': 'CORRIGER LA DIRECTIVE',
 'hc.directive.correction_free': '\nDirective déjà payée : correction enregistrée sans coût supplémentaire.',
 'hc.directive.description': 'Modifie les priorités du STANDARD à partir du mois suivant la période sélectionnée et '
                             'reste active jusqu’à renouvellement.',
 'hc.directive.edit': 'MODIFIER LA RÉPARTITION  •  {cost} POINTS',
 'hc.directive.editor_title': 'DIRECTIVE DE RÉPARTITION DU HAUT COMMANDEMENT',
 'hc.directive.effect': '{aircraft}  •  EFFET À PARTIR DE {period}',
 'hc.directive.invalid_body': 'Les quotas de priorité ne sont pas respectés.\n'
                              '\n'
                              'CRITIQUE : maximum 1\n'
                              'FORTE : maximum 2',
 'hc.directive.invalid_title': 'Directive invalide',
 'hc.directive.number': '★★★  DIRECTIVE N°{number}',
 'hc.directive.persistence': 'Cette répartition restera active pour les mois suivants jusqu’à une nouvelle directive '
                             'ou un retour au STANDARD historique.',
 'hc.directive.quota': 'CRITIQUE {critical}/1   •   FORTE {strong}/2',
 'hc.directive.refused': 'Directive refusée',
 'hc.directive.reset_fail': 'Réinitialisation impossible',
 'hc.directive.restore_body': 'Rétablir les priorités historiques d’origine à partir de {period} ?\n'
                              '\n'
                              'Les points déjà dépensés ne seront pas remboursés.',
 'hc.directive.restore_button': 'RÉTABLIR LE STANDARD HISTORIQUE',
 'hc.directive.restore_title': 'Rétablir le STANDARD',
 'hc.directive.restored_body': 'Le retour aux priorités historiques est programmé à partir de {period}.',
 'hc.directive.restored_title': 'STANDARD historique rétabli',
 'hc.directive.saved': 'Directive enregistrée',
 'hc.directive.saved_body': 'Nouvelle répartition du STANDARD enregistrée.\n'
                            '\n'
                            'Effet : {period}\n'
                            '{cost}{correction}\n'
                            '\n'
                            'Elle restera active jusqu’à renouvellement.',
 'hc.directive.send': 'ENVOYER LA DIRECTIVE  •  {cost} POINTS',
 'hc.directive.since': 'ACTIVE DEPUIS {period}',
 'hc.directive.title': 'DIRECTIVE DE RÉPARTITION',
 'hc.directive.window': 'Directive de répartition',
 'hc.emergency.subtitle': 'Livraison indépendante d’ammoQty IL-2 • délai 2–3 jours',
 'hc.emergency.title': 'LIVRAISON URGENTE',
 'hc.error.already_boosted': 'Une demande de priorisation a déjà été accordée à cette munition pour ce mois.\n'
                             '\n'
                             'Une seule priorisation est autorisée par munition et par mois.',
 'hc.error.directive_quota': 'Les quotas CRITIQUE / FORTE ne sont pas respectés.',
 'hc.error.incompatible': 'Cette munition n’est pas compatible avec l’avion de la carrière.',
 'hc.error.insufficient_points': 'Points insuffisants : {cost} nécessaires.',
 'hc.error.invalid_boost': 'Boost de priorité invalide.',
 'hc.error.invalid_delivery_size': 'Taille de livraison invalide.',
 'hc.error.past_delivery': 'Impossible de commander une livraison pour un mois déjà passé.',
 'hc.error.past_month': 'Impossible de modifier un mois déjà passé.',
 'hc.explanation': 'Le Haut Commandement permet d’obtenir un soutien logistique exceptionnel lorsque la situation '
                   'l’exige.\n'
                   'Il peut renforcer temporairement certaines priorités, accorder des boosts ou organiser des '
                   'livraisons urgentes.\n'
                   'Toutes les décisions prises sont enregistrées ci-dessous afin de suivre leur effet au fil de la '
                   'campagne.',
 'hc.history.boost': '★ Boost +{boost} % • {munition} • {period}',
 'hc.history.delivery': '★★ Livraison {size} • {munition} • {status}',
 'hc.history.directive': '★★★ Directive n°{number} • {period}',
 'hc.history.none': '• Aucune action de commandement enregistrée pour cette période.',
 'hc.history.standard': '◇ Retour au STANDARD • {period}',
 'hc.history.title': 'HISTORIQUE DES ACTIONS',
 'hc.period.past_body': 'Ce mois est déjà terminé dans votre carrière.\n'
                        '\n'
                        'Vous pouvez uniquement envoyer une demande pour le mois actuel ou un mois futur.',
 'hc.period.past_title': 'Haut Commandement',
 'hc.points.available': '{points} POINTS DISPONIBLES',
 'hc.points.low_body': 'Vous n’avez plus assez de points de commandement.',
 'hc.points.low_title': 'Haut Commandement',
 'hc.request.approved': 'Demande accordée',
 'hc.request.approved_body': '{munition}\n'
                             '\n'
                             'Boost logistique : +{value} %\n'
                             '{cost}\n'
                             '\n'
                             'Le preset d’origine reste inchangé.',
 'hc.request.denied': 'Demande refusée',
 'hc.request.help': 'Sélectionnez une munition à gauche, puis une seule action à droite.',
 'hc.request.summary': '{aircraft}  •  {period}  •  {points}',
 'hc.request.title': 'DEMANDE AU HAUT COMMANDEMENT',
 'hc.request.window': 'Demande au Haut Commandement',
 'hc.select_ammo': 'Sélectionnez une munition',
 'hc.standard_restored': 'STANDARD HISTORIQUE RÉTABLI',
 'hc.subtitle': 'SOUTIEN LOGISTIQUE ET DÉCISIONS EXCEPTIONNELLES',
 'hc.title': 'HAUT COMMANDEMENT',
 'main.aircraft.image_error': 'ERREUR IMAGE',
 'main.aircraft.image_unavailable': 'IMAGE NON DISPONIBLE',
 'main.aircraft.linked': 'CARRIÈRE LIÉE',
 'main.aircraft.linked_body': "L'appareil est défini par la carrière IL-2 sélectionnée.\n"
                              '\n'
                              'Appareil détecté : {aircraft}\n'
                              'Pour utiliser un autre appareil, chargez une autre carrière au prochain démarrage.',
 'main.aircraft.linked_title': 'Appareil lié à la carrière',
 'main.aircraft.title': 'APPAREIL',
 'main.aircraft_selector.active': 'APPAREIL ACTIF',
 'main.aircraft_selector.compatible_count': '{count} EMPORTS COMPATIBLES',
 'main.aircraft_selector.no_loadout': 'AUCUN EMPORT DISPONIBLE',
 'main.aircraft_selector.subtitle': "Sélectionnez l'appareil utilisé pour la prochaine mission.",
 'main.aircraft_selector.title': "SÉLECTION DE L'APPAREIL",
 'main.aircraft_selector.window': "Sélection de l'appareil",
 'main.generic_squadron': 'ESCADRILLE GÉNÉRIQUE',
 'main.history.clear': "EFFACER L'HISTORIQUE",
 'main.history.clear_confirm': "Supprimer tout l'historique des missions ?",
 'main.history.clear_title': 'Historique',
 'main.history.none': 'AUCUNE MISSION ENREGISTRÉE',
 'main.history.title': 'HISTORIQUE DES MISSIONS',
 'main.loadout.add': 'AJOUTER',
 'main.loadout.add_subtitle': '{aircraft} • seuls les emports compatibles sont proposés',
 'main.loadout.add_title': 'AJOUTER UN EMPORT',
 'main.loadout.add_window': 'Ajouter un emport',
 'main.loadout.already_added': 'DÉJÀ AJOUTÉ',
 'main.loadout.base_stock': '{category}  •  STOCK BASE : {stock}',
 'main.loadout.no_external_body': "{aircraft} ne dispose d'aucun emport externe.",
 'main.loadout.no_external_title': 'Emports',
 'main.loadout.none_available': 'AUCUN EMPORT DISPONIBLE\nPOUR CET APPAREIL',
 'main.loadout.none_selected': 'AUCUN EMPORT SÉLECTIONNÉ\n\nUTILISEZ LE BOUTON + POUR AJOUTER UN ARMEMENT À LA MISSION',
 'main.loadout.stock_base_long': '{category}  •  STOCK DE LA BASE : {stock}',
 'main.mission.aircraft_count': 'APPAREILS',
 'main.mission.career_date': 'DATE CARRIÈRE',
 'main.mission.delete_short': 'SUPPR.',
 'main.mission.load': 'CHARGER',
 'main.mission.no_preset': 'AUCUN PRÉRÉGLAGE',
 'main.mission.per_aircraft': 'PAR AVION',
 'main.mission.preset': 'PRÉRÉGLAGE',
 'main.mission.save': 'SAUVER',
 'main.mission.selected_loadout': 'EMPORT SÉLECTIONNÉ',
 'main.mission.time': 'HEURE',
 'main.mission.title': 'PRÉPARATION DE LA MISSION',
 'main.mission.total': 'TOTAL',
 'main.mission.validate': 'VALIDER LA MISSION',
 'main.preset.delete_body': 'Supprimer définitivement « {name} » pour {aircraft} ?',
 'main.preset.delete_title': 'Supprimer le préréglage',
 'main.preset.deleted': 'PRÉRÉGLAGE SUPPRIMÉ',
 'main.preset.empty_body': 'Ajoutez au moins un emport avant de créer un préréglage.',
 'main.preset.empty_title': 'Préréglage',
 'main.preset.loaded': 'PRÉRÉGLAGE « {name} » CHARGÉ',
 'main.preset.new_prompt': 'Nom du préréglage pour {aircraft} :',
 'main.preset.new_title': 'Nouveau préréglage',
 'main.preset.none_available': 'AUCUN PRÉRÉGLAGE DISPONIBLE',
 'main.preset.not_found': 'PRÉRÉGLAGE INTROUVABLE',
 'main.preset.replace_body': 'Le préréglage « {name} » existe déjà.\nLe remplacer ?',
 'main.preset.replace_title': 'Remplacer le préréglage',
 'main.preset.saved': 'PRÉRÉGLAGE « {name} » ENREGISTRÉ',
 'main.stock.description': 'INVENTAIRE GLOBAL DES MUNITIONS\nET EMPORTS DISPONIBLES SUR LA BASE',
 'main.stock.report': 'RAPPORT',
 'main.stock.title': 'STOCK DE LA BASE AÉRIENNE',
 'main.stock.view': 'CONSULTER LE STOCK',
 'main.title': 'MENU PRINCIPAL',
 'main.validation.aircraft_count_positive': "LE NOMBRE D'AVIONS DOIT ÊTRE SUPÉRIEUR À 0",
 'main.validation.career_date': 'DATE DE CARRIÈRE INDISPONIBLE',
 'main.validation.insufficient_stock': 'STOCK INSUFFISANT : {munition}',
 'main.validation.invalid_aircraft_count': "NOMBRE D'AVIONS INVALIDE",
 'main.validation.invalid_quantity': 'QUANTITÉ INVALIDE : {munition}',
 'main.validation.invalid_time': 'HEURE INVALIDE',
 'main.validation.no_loadout': 'AUCUN EMPORT SÉLECTIONNÉ',
 'main.validation.no_quantity': "AUCUNE QUANTITÉ D'EMPORT RENSEIGNÉE",
 'main.validation.save_error': "ERREUR LORS DE L'ENREGISTREMENT DE LA MISSION",
 'main.validation.saved': 'MISSION ENREGISTRÉE',
 'model.create_with_plus': 'CRÉER UN MODÈLE AVEC +',
 'model.delete.body': 'Supprimer définitivement le modèle « {name} » ?\n'
                      '\n'
                      'Toutes ses périodes mensuelles seront supprimées.\n'
                      'Le modèle STANDARD restera intact.',
 'model.delete.fail_body': 'Le modèle n’a pas pu être supprimé.',
 'model.delete.fail_title': 'Suppression impossible',
 'model.delete.title': 'Supprimer le modèle',
 'model.description': 'L’importance détermine la part du prochain ravitaillement. Les poids sont réglables uniquement '
                      'sur un preset personnalisé.',
 'model.empty.body': 'La période {period} ne contient aucune quantité de référence utilisable.',
 'model.empty.title': 'Répartition vide',
 'model.estimated_share': 'PART ESTIMÉE',
 'model.export.button': 'EXPORTER LE PRESET',
 'model.export.dialog': 'Exporter le preset',
 'model.export.fail_body': 'Le preset n’a pas pu être exporté.\n\n{error}',
 'model.export.fail_title': 'Export impossible',
 'model.export.standard_body': 'Le preset STANDARD est intégré au logiciel et n’est pas exportable comme modèle '
                               'personnalisé.',
 'model.export.success_body': 'Le preset a été exporté avec succès.\n\n{path}',
 'model.export.success_title': 'Preset exporté',
 'model.export.unsaved_body': 'Le modèle contient des modifications encore en brouillon.\n'
                              '\n'
                              'Enregistrez d’abord le modèle complet, puis relancez l’export pour garantir que le '
                              'fichier partagé contient toutes les périodes.',
 'model.export.unsaved_title': 'Modifications non enregistrées',
 'model.filetype.all': 'Tous les fichiers',
 'model.filetype.json': 'Fichiers JSON',
 'model.filetype.preset': 'Preset IL-2 Gestion Stock',
 'model.free': 'LIBRE',
 'model.full': 'COMPLET',
 'model.import.button': 'IMPORTER UN PRESET',
 'model.import.dialog': 'Importer un preset de répartition',
 'model.import.fail_body': 'Le fichier n’a pas été importé.\n\n{error}',
 'model.import.fail_title': 'Import impossible',
 'model.import.success_body': 'Le preset « {name} » a été importé avec succès.\n'
                              '\n'
                              'Une copie normalisée a été ajoutée au dossier presets de cette carrière.',
 'model.import.success_title': 'Preset importé',
 'model.importance': 'IMPORTANCE LOGISTIQUE',
 'model.limit.body': 'Erreur pour {period} :\n\n{details}\n\nCorrigez cette période avant d’enregistrer.',
 'model.limit.title': 'Limite de priorité dépassée',
 'model.name_label': 'Nom du modèle personnalisé',
 'model.no_change.body': 'Aucune période du modèle n’a été modifiée.',
 'model.no_change.title': 'Aucune modification',
 'model.pending.count': '{count} période(s) modifiée(s) en attente d’enregistrement',
 'model.pending.none': 'Aucune modification en attente',
 'model.period': 'PÉRIODE DU MODÈLE',
 'model.period.draft': 'BROUILLON',
 'model.period.historical': 'HISTORIQUE',
 'model.portable_error.body': 'Le modèle a bien été enregistré dans la base, mais son fichier portable JSON n’a pas pu '
                              'être mis à jour.\n'
                              '\n'
                              '{error}',
 'model.portable_error.title': 'Preset enregistré localement',
 'model.portable_path': '\n\nPreset portable :\n{path}',
 'model.save_all': 'ENREGISTRER LE MODÈLE COMPLET',
 'model.save_error.body': 'Le modèle complet n’a pas pu être enregistré.\n\n{error}',
 'model.save_error.title': 'Erreur d’enregistrement',
 'model.saved.body': '{name} a été enregistré.\n\n{count} période(s) mensuelle(s) sauvegardée(s).{portable}',
 'model.saved.title': 'Modèle enregistré',
 'model.selector': 'MODÈLE',
 'model.standard.readonly': 'Le modèle STANDARD est en lecture seule.\n'
                            '\n'
                            'Créez ou sélectionnez un modèle personnalisé pour le modifier.',
 'model.standard.title': 'Modèle STANDARD',
 'model.status.custom': 'PERSONNALISÉ • MODÈLE COMPLET MODIFIABLE',
 'model.status.standard': 'STANDARD • IMPORTANCE HISTORIQUE MENSUELLE • POIDS VERROUILLÉS',
 'model.subtitle': '{aircraft}  •  MODÈLE COMPLET PAR ANNÉE ET PAR MOIS',
 'model.title': 'MODÈLE DE RÉPARTITION',
 'model.validation.assignment': 'Affectation invalide.',
 'model.validation.assignment_month': 'Mois invalide dans une affectation : {month}',
 'model.validation.assignment_year': 'Année invalide dans une affectation : {year}',
 'model.validation.custom_missing': 'Le modèle personnalisé n’existe pas.',
 'model.validation.format': 'Ce fichier n’est pas un preset IL-2 Gestion Stock compatible.',
 'model.validation.global_quantity': 'Quantité globale invalide.',
 'model.validation.incompatible': '{munition} n’est pas compatible avec {aircraft}.',
 'model.validation.invalid_month': 'Mois invalide : {month}',
 'model.validation.invalid_year': 'Année invalide : {year}',
 'model.validation.json_object': 'Le fichier preset n’est pas un objet JSON valide.',
 'model.validation.name': 'Le preset ne contient aucun nom.',
 'model.validation.negative_monthly': 'Une quantité mensuelle ne peut pas être négative.',
 'model.validation.negative_reference': 'Une quantité de référence ne peut pas être négative.',
 'model.validation.period_quantity': 'Période de quantité invalide.',
 'model.validation.section': 'Section preset absente ou invalide.',
 'model.validation.standard_export': 'Le modèle STANDARD n’est pas exportable comme preset personnalisé.',
 'model.validation.unknown_aircraft': 'Avion inconnu : {aircraft}',
 'model.validation.unknown_ammo': 'Munition inconnue : {munition}',
 'model.validation.unknown_level': 'Niveau inconnu : {level}',
 'model.validation.version': 'Version de preset incompatible : {version}.',
 'model.weight': 'poids de répartition',
 'model.weights.description': 'Plus le poids est élevé, plus les munitions de cette importance reçoivent une grande '
                              'part du prochain ravitaillement.',
 'model.weights.title': 'POIDS DE RÉPARTITION PAR IMPORTANCE',
 'model.window': 'Modèle de répartition',
 'month.1': 'JANVIER',
 'month.10': 'OCTOBRE',
 'month.11': 'NOVEMBRE',
 'month.12': 'DÉCEMBRE',
 'month.2': 'FÉVRIER',
 'month.3': 'MARS',
 'month.4': 'AVRIL',
 'month.5': 'MAI',
 'month.6': 'JUIN',
 'month.7': 'JUILLET',
 'month.8': 'AOÛT',
 'month.9': 'SEPTEMBRE',
 'munition.m01': 'Roquette aérienne semi-perforante à haute vitesse HVAR 5"',
 'munition.m02': 'Roquette aérienne à haute vitesse HVAR 5"',
 'munition.m03': 'Réservoir de napalm 110 gal',
 'munition.m04': 'Réservoir largable 110 gal',
 'munition.m05': 'Réservoir largable 75 gal',
 'munition.m06': 'AN-M64A1 500 lb',
 'munition.m07': 'AN-M65A1 1000 lb',
 'munition.m08': 'Bombe éclairante à parachute AN-M26A1',
 'munition.m09': 'M26A2 500 lb à sous-munitions',
 'munition.m10': 'M29A1 500 lb à sous-munitions',
 'munition.m11': 'Roquette ATAR 6,5"',
 'munition.m12': 'AN-M57A1 250 lb',
 'munition.m13': 'AN-M88 220 lb à fragmentation',
 'munition.m14': 'Réservoir largable 165 gal',
 'munition.m15': 'Réservoir largable 265 gal',
 'munition.m16': 'Roquette Tiny Tim 12"',
 'munition.m17': 'Réservoir largable 230 gal',
 'munition.m18': 'Réservoir largable 120 gal',
 'munition.m19': 'Réservoir largable 245 gal',
 'munition.m20': 'M-13UK 132 mm',
 'munition.m21': 'M-8 82 mm',
 'munition.m22': 'PTAB-10-2.5',
 'munition.m23': 'PTAB-2,5-1,5',
 'munition.m24': 'SAB-100-55',
 'munition.m25': 'AO-10sc',
 'munition.m26': 'AO-2,5sc',
 'munition.m27': 'AO-25sl',
 'munition.m28': 'FAB-100sc',
 'munition.m29': 'FAB-250 M43',
 'munition.m30': 'FAB-50sc',
 'munition.m31': 'Réservoir largable 250 L',
 'options.admin.confirm_body': 'Activer le MODE ADMIN ?\n'
                               '\n'
                               'Ce mode déverrouille les outils de modification directe du stock et des points, le '
                               'gain journalier, ainsi que les réinitialisations.\n'
                               'Les demandes au Haut Commandement deviennent gratuites.\n'
                               '\n'
                               'Les modèles personnalisés restent accessibles sans MODE ADMIN.\n'
                               '\n'
                               "Ce mode est destiné aux tests et peut casser l'immersion.",
 'options.admin.confirm_title': 'Activer le mode Admin',
 'options.admin.daily_gain': 'RÉGLER LE GAIN DE POINTS / JOUR',
 'options.admin.description': 'Active les outils de gestion avancée et rend les actions du Haut Commandement '
                              'gratuites.',
 'options.admin.disable': 'DÉSACTIVER LE MODE ADMIN',
 'options.admin.enable': 'ACTIVER LE MODE ADMIN',
 'options.admin.modify_points': 'MODIFIER LE SOLDE DE POINTS',
 'options.admin.modify_stock': 'MODIFIER LE STOCK',
 'options.admin.reset_career': 'RÉINITIALISER TOUTE LA CARRIÈRE LOCALE',
 'options.admin.reset_standard': 'RÉINITIALISER LE STOCK STANDARD',
 'options.admin.status_off': 'MODE ADMIN DÉSACTIVÉ',
 'options.admin.status_on': '◆ MODE ADMIN ACTIF',
 'options.admin.title': 'ADMINISTRATION',
 'options.admin.tools': 'Outils disponibles en mode Admin :\n'
                        '• actions du Haut Commandement gratuites\n'
                        '• modification directe du stock\n'
                        '• modification manuelle du solde de points\n'
                        '• réglage du gain journalier de commandement\n'
                        '• réinitialisation du stock STANDARD\n'
                        '• réinitialisation complète de la carrière locale',
 'options.appearance.description': "Choisissez le style général de l'interface.",
 'options.appearance.theme.clair': 'CLAIR',
 'options.appearance.theme.sombre': 'SOMBRE',
 'options.appearance.title': 'APPARENCE',
 'options.display.description': 'Adaptez la taille du texte et des fenêtres secondaires à votre écran.',
 'options.display.main_fixed': 'La fenêtre principale conserve une taille fixe.',
 'options.display.profile.compact': 'COMPACT',
 'options.display.profile.grand': 'GRAND',
 'options.display.profile.standard': 'STANDARD',
 'options.display.text_size': 'TAILLE DU TEXTE',
 'options.display.title': 'AFFICHAGE',
 'options.display.windows_size': 'TAILLE DES FENÊTRES SECONDAIRES',
 'options.language.description': "Choisissez la langue de l'interface.",
 'options.language.en': 'ENGLISH',
 'options.language.fr': 'FRANÇAIS',
 'options.language.restart': 'Le changement de langue est appliqué au prochain démarrage.',
 'options.language.restart_pending': "Langue enregistrée. Redémarrez l'application pour appliquer le changement.",
 'options.language.title': 'LANGUE',
 'options.title': 'OPTIONS',
 'options.update.check': 'RECHERCHER LES MISES À JOUR',
 'options.update.current': 'VERSION INSTALLÉE : {version}',
 'options.update.description': 'Vérifie sur GitHub Releases si une version officielle plus récente est disponible.',
 'options.update.title': 'MISES À JOUR',
 'update.available.body': "Une version plus récente est disponible.\n\nInstallée : {current}\nDisponible : {latest}\n\nL'installeur officiel sera téléchargé depuis la Release GitHub du projet.",
 'update.available.download': 'TÉLÉCHARGER ET INSTALLER',
 'update.available.later': 'PLUS TARD',
 'update.available.title': 'MISE À JOUR DISPONIBLE',
 'update.check.error.body': "La recherche de mise à jour n'a pas pu aboutir.\n\n{error}",
 'update.check.error.title': 'RECHERCHE DE MISE À JOUR',
 'update.check.up_to_date.body': 'Vous utilisez la dernière version disponible.\n\nInstallée : {current}\nDernière : {latest}',
 'update.check.up_to_date.title': 'À JOUR',
 'update.download.body': 'Téléchargement de {version} depuis GitHub...',
 'update.download.error.body': "La mise à jour n'a pas pu être téléchargée ou lancée.\n\n{error}",
 'update.download.error.title': 'ÉCHEC DE LA MISE À JOUR',
 'update.download.preparing': 'Préparation du téléchargement...',
 'update.download.title': 'TÉLÉCHARGEMENT DE LA MISE À JOUR',
 'options.title': 'OPTIONS',
 'priority.critical': 'CRITIQUE',
 'priority.low': 'FAIBLE',
 'priority.normal': 'NORMALE',
 'priority.rare': 'RARE',
 'priority.strong': 'FORTE',
 'priority.unavailable': 'INDISPONIBLE',
 'reports.date': 'DATE IN-GAME : {date}',
 'reports.delete.body': 'Tous les rapports logistiques de cette carrière vont être supprimés définitivement.',
 'reports.delete.title': 'Supprimer les rapports',
 'reports.delete_all': 'EFFACER TOUS LES RAPPORTS',
 'reports.detail.emergency': '+{qty} {munition}  •  {size}  •  ammoQty IL-2 inchangé',
 'reports.detail.unchanged': 'Stock détaillé inchangé : le type de munition consommé n’est pas connu.',
 'reports.il2_units': 'UNITÉS IL-2 : {old} → {new}   ({delta})',
 'reports.local_stock': 'STOCK LOCAL : {old} → {new}   ({delta})',
 'reports.more': ' +{count} autres',
 'reports.none': 'AUCUN RAPPORT ENREGISTRÉ',
 'reports.subtitle': 'SUIVI DES ÉVOLUTIONS DÉTECTÉES DANS LA CARRIÈRE IL-2',
 'reports.title': 'RAPPORTS LOGISTIQUES',
 'reports.type.consumption': 'CONSOMMATION IL-2 DÉTECTÉE',
 'reports.type.emergency': 'LIVRAISON URGENTE REÇUE',
 'reports.type.initial': 'STOCK DE CARRIÈRE INITIALISÉ',
 'reports.type.other': 'ÉVOLUTION DE LA CARRIÈRE',
 'reports.type.supply': 'RAVITAILLEMENT MUNITIONS DÉTECTÉ',
 'reports.window': 'Rapports logistiques',
 'startup.loading': 'CHARGEMENT EN COURS',
 'startup.new_career.factory': 'Données locales • stock • ravitaillement • synchronisation IL-2',
 'startup.new_career.preparing': 'Préparation de la carrière...',
 'startup.new_career.step.db': 'Chargement de la base locale...',
 'startup.new_career.step.finish': 'Finalisation du chargement...',
 'startup.new_career.step.read': 'Lecture de la carrière IL-2...',
 'startup.new_career.step.standard': 'Chargement du modèle de répartition...',
 'startup.new_career.step.stock': 'Synchronisation du stock...',
 'startup.new_career.title': 'CHARGEMENT DE LA CARRIÈRE',
 'startup.unknown_aircraft': 'APPAREIL INCONNU',
 'startup.unknown_date': 'DATE INCONNUE',
 'stock.capacity.legend.consumed': 'CONSOMMÉ',
 'stock.capacity.legend.remaining': 'RESTANT',
 'stock.capacity.remaining': 'STOCK RESTANT',
 'stock.capacity.subtitle': 'NIVEAU DE STOCK IL-2',
 'stock.capacity.title': 'CAPACITÉ DU DÉPÔT',
 'stock.capacity.units': '{current} / {reference} UNITÉS DE RAVITAILLEMENT',
 'stock.distribution.count': 'MUNITIONS EN STOCK',
 'stock.distribution.edit': 'MODIFIER LE MODÈLE DE RÉPARTITION',
 'stock.distribution.hint': 'CONSULTEZ LA RÉPARTITION PRÉVUE PAR MOIS POUR ANTICIPER LES PROCHAINS RAVITAILLEMENTS',
 'stock.distribution.subtitle': 'COMPOSITION PAR MUNITION',
 'stock.distribution.title': 'RÉPARTITION DU STOCK',
 'stock.distribution.view': 'CONSULTER LA RÉPARTITION DU STOCK',
 'stock.inventory.none': 'AUCUNE MUNITION DISPONIBLE\nPOUR {aircraft}',
 'stock.inventory.subtitle': 'STOCK DISPONIBLE POUR {aircraft}',
 'stock.inventory.title': 'MUNITIONS DISPONIBLES',
 'stock.model_warning.custom_body': 'Créer ou utiliser un modèle personnalisé peut modifier fortement cet équilibre : '
                                    'certaines munitions pourront devenir beaucoup plus fréquentes, plus rares ou '
                                    'presque absentes des futurs ravitaillements.\n'
                                    '\n'
                                    'Ces choix ont donc une importance majeure sur le réalisme et la difficulté de '
                                    'votre gestion de carrière.',
 'stock.model_warning.intro': 'Le modèle de répartition détermine comment les futurs ravitaillements de la carrière '
                              'seront distribués entre les différentes munitions compatibles avec votre appareil.',
 'stock.model_warning.open': "J'AI COMPRIS — OUVRIR L'ÉDITEUR",
 'stock.model_warning.standard_body': 'Le modèle STANDARD cherche à représenter une répartition logistique plausible '
                                      'pour une base aérienne typique durant la guerre de Corée.\n'
                                      '\n'
                                      "Il ne prétend pas reproduire au projectile près les stocks d'une base "
                                      'historique précise. Son objectif est de proposer un équilibre cohérent avec '
                                      "l'appareil utilisé, la période de la campagne et le contexte opérationnel.",
 'stock.model_warning.standard_title': 'MODÈLE STANDARD',
 'stock.model_warning.title': 'IMPORTANCE DU MODÈLE DE RÉPARTITION',
 'stock.model_warning.window': 'Importance du modèle de répartition',
 'stock.window.subtitle': '{aircraft}  •  {qty} UNITÉS DE RAVITAILLEMENT (EXTRAIT DES DONNÉES DE LA CARRIÈRE IL-2)',
 'stock.window.title': 'STOCK DE LA BASE AÉRIENNE',
 'stock_evolution.abstract_notice': 'IL-2 indique uniquement une consommation abstraite.\n'
                                    'Le type exact de munition utilisé n’est pas connu,\n'
                                    'donc aucune munition concrète n’est retirée.',
 'stock_evolution.title': 'ÉVOLUTION DU STOCK CONCRET',
 'stock_evolution.window': 'Évolution du stock de munitions'}
