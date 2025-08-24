% Types de crime
crime_type(vol).
crime_type(assassinat).
crime_type(escroquerie).

% Faits - Suspects
suspect(john).
suspect(mary).
suspect(alice).
suspect(bruno).
suspect(sophie).

% Faits - Motifs
has_motive(john, vol).
has_motive(mary, assassinat).
has_motive(alice, escroquerie).

% Faits - Proximité de la scène de crime
was_near_crime_scene(john, vol).
was_near_crime_scene(mary, assassinat).

% Faits - Empreintes digitales
has_fingerprint_on_weapon(john, vol).
has_fingerprint_on_weapon(mary, assassinat).

% Faits - Transactions bancaires
has_bank_transaction(alice, escroquerie).
has_bank_transaction(bruno, escroquerie).

% Faits - Fausse identité
owns_fake_identity(sophie, escroquerie).

% Faits additionnels pour témoins oculaires
eyewitness_identification(john, vol).

% Règles de culpabilité
is_guilty(Suspect, vol) :-
    suspect(Suspect),
    has_motive(Suspect, vol),
    was_near_crime_scene(Suspect, vol),
    (has_fingerprint_on_weapon(Suspect, vol) ; 
     eyewitness_identification(Suspect, vol)).

is_guilty(Suspect, assassinat) :-
    suspect(Suspect),
    has_motive(Suspect, assassinat),
    was_near_crime_scene(Suspect, assassinat),
    (has_fingerprint_on_weapon(Suspect, assassinat) ; 
     eyewitness_identification(Suspect, assassinat)).

is_guilty(Suspect, escroquerie) :-
    suspect(Suspect),
    has_motive(Suspect, escroquerie),
    (has_bank_transaction(Suspect, escroquerie) ; 
     owns_fake_identity(Suspect, escroquerie)).


% Prédicat utilitaire pour interroger manuellement le système
check_guilt(Suspect, CrimeType) :-
    (is_guilty(Suspect, CrimeType) ->
        format('~w est coupable de ~w~n', [Suspect, CrimeType])
    ;   format('~w n\'est pas coupable de ~w~n', [Suspect, CrimeType])
    ).