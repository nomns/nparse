class Spell:

    def __init__(self, **kwargs):
        self.id = 0
        self.name = ''
        self.effect_text_you = ''
        self.effect_text_other = ''
        self.effect_text_worn_off = ''
        self.aoe_range = 0
        self.max_targets = 1
        self.cast_time = 0
        self.resist_type = 0
        self.duration_formula = 0
        self.pvp_duration_formula = 0
        self.duration = 0
        self.pvp_duration = 0
        self.type = 0
        self.spell_icon = 0
        self.__dict__.update(kwargs)
