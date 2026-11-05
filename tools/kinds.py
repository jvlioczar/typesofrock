# Tipo de cada gênero: "genre" (gênero), "sub" (subgênero) ou "fusion" (gênero cruzado: crossover/fusão).
# Gênero: estilo amplo, que tem os próprios subgêneros, ou uma das raízes anteriores ao rock.
# Fusão: nasce do cruzamento de duas linhagens distantes (rock com outro gênero, ou dois ramos separados do rock).
# Subgênero: o resto, um ramo dentro de uma linhagem já existente.
GENRE = {
    "blues", "gospel", "country", "folk", "rnb", "classical-music",
    "rock-n-roll", "pop-rock", "classic-rock", "psychedelic-rock", "progressive-rock", "hard-rock", "heavy-metal",
    "punk-rock", "post-punk", "new-wave", "alternative-rock", "indie-rock",
}
FUSION = {
    "rockabilly", "blues-rock", "folk-rock", "country-rock", "jazz-rock", "funk-rock", "latin-rock", "tropicalia", "baroque-pop",
    "rap-rock", "nu-metal", "alternative-metal", "industrial-metal", "neue-deutsche-harte", "symphonic-metal", "folk-metal",
    "gothic-metal", "post-metal", "sludge-metal", "metalcore", "deathcore", "crust-punk", "psychobilly", "folk-punk", "ska-punk",
    "dance-punk", "synth-pop", "madchester",
}


def kind(gid):
    return "genre" if gid in GENRE else "fusion" if gid in FUSION else "sub"
