class RegisterManager:
    def __init__(self):
        self.temps = [5, 6, 7, 28, 29, 30, 31]
        self.saved = [8, 9, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
        
        self.used_temps = set()
        self.used_saved = {}

    def alloc_temp(self):
        for r in self.temps:
            if r not in self.used_temps:
                self.used_temps.add(r)
                return r
        raise Exception("Zonny se quedó sin bolsillos temporales (t)!")

    def free_temp(self, reg):
        if reg in self.used_temps:
            self.used_temps.remove(reg)

    def alloc_variable(self, name):
        for r in self.saved:
            if r not in self.used_saved.values():
                self.used_saved[name] = r
                return r
        raise Exception(f"Demasiadas variables: no hay espacio para '{name}'")

    def get_var_reg(self, name):
        return self.used_saved.get(name)