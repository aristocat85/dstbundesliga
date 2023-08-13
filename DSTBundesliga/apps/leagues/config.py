LEVEL_MAP = {
    1: "Bundesliga",
    2: "2. Bundesliga",
    3: "Conference-Liga",
    4: "Divisionsliga",
    5: "Regionalliga",
    6: "Kreisliga",
}

LOGO_MAP = {
    1: {None: "dst_bl_logo"},
    2: {None: "dst_bl2_logo"},
    3: {"CFFC": "dst_cffc_conf_logo", "AFFC": "dst_affc_conf_logo"},
    4: {"CFFC": "dst_cffc_div_logo", "AFFC": "dst_affc_div_logo"},
    5: {"CFFC": "dst_cffc_reg_logo", "AFFC": "dst_affc_reg_logo"},
    6: {"CFFC": "dst_cffc_reg_logo", "AFFC": "dst_affc_reg_logo"},
}

LEAGUE_SETTINGS_MAP = {
    1: {"max_league_count": 1, "risers": 0, "ascenders": 8},
    2: {"max_league_count": 4, "risers": 2, "ascenders": 6},
    3: {"max_league_count": 20, "risers": 2, "ascenders": 6},
    4: {"max_league_count": 32, "risers": 3, "ascenders": 6},
    5: {"max_league_count": 60, "risers": 3, "ascenders": 8},
    6: {"max_league_count": 128, "risers": 3, "ascenders": 8},
}


POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]
