def G(id, pt_name, en_name, year, clade, parents, similar, ext, place_pt, place_en, genome, sound, names, pt, en):
    return dict(id=id, name=dict(pt=pt_name, en=en_name), year=year, clade=clade, parents=parents,
                similar=similar, ext=ext, place=dict(pt=place_pt, en=place_en), genome=genome,
                sound=sound, names=names, text=dict(pt=pt, en=en))
