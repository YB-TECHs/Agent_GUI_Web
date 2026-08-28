"""
Module empecher_veille.py.
"""

import platform


class EmpecherVeille:
    """Gestionnaire de contexte : empeche la veille systeme pendant son
    execution, et restaure le comportement normal en sortie (meme en cas
    d'erreur, grace au __exit__)."""

    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __init__(self):
        self._est_windows = platform.system() == "Windows"

    def __enter__(self):
        if self._est_windows:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(
                self.ES_CONTINUOUS | self.ES_SYSTEM_REQUIRED
            )
            print("Mise en veille systeme desactivee pour la duree du script.")
        else:
            print("Systeme non-Windows detecte : aucune action sur la veille.")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._est_windows:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS)
            print("Comportement normal de mise en veille restaure.")
        return False  # ne masque aucune exception eventuelle
