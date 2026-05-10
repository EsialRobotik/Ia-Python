"""
Lecteur audio simple basé sur pygame.mixer pour le RabbitControlCenter.

Lit toutes les musiques (mp3, ogg, wav, flac) du dossier configuré, démarre
sur une piste aléatoire et enchaîne automatiquement à la fin de chaque
piste. Expose `play / stop / toggle / next / prev`.

pygame.mixer est initialisé paresseusement à la première lecture pour ne
pas bloquer le démarrage de l'UI si la sortie audio ALSA n'est pas prête.
"""

import logging
import os
import random
import sys
from typing import Optional

from PySide6.QtCore import QObject, QTimer

logger = logging.getLogger(__name__)


AUDIO_EXTENSIONS = (".mp3", ".ogg", ".wav", ".flac", ".m4a")


class MusicPlayer(QObject):
    def __init__(self, music_dir: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._music_dir = music_dir
        self._tracks: list[str] = []
        self._index: int = 0
        self._playing: bool = False
        self._initialized: bool = False
        # Vérifie périodiquement la fin de piste pour enchaîner
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(500)
        self._poll_timer.timeout.connect(self._check_track_end)

    # --- API publique --------------------------------------------------------

    def is_playing(self) -> bool:
        return self._playing

    def play(self, random_start: bool = False) -> None:
        if not self._ensure_initialized():
            return
        self._refresh_tracks()
        if not self._tracks:
            logger.warning("Aucune musique trouvée dans %s", self._music_dir)
            return
        if random_start or not (0 <= self._index < len(self._tracks)):
            self._index = random.randrange(len(self._tracks))
        self._play_current()

    def stop(self) -> None:
        if self._initialized:
            try:
                import pygame
                pygame.mixer.music.stop()
            except Exception as exc:
                logger.error("Erreur arrêt musique : %s", exc)
        self._poll_timer.stop()
        self._playing = False

    def toggle(self) -> None:
        if self._playing:
            self.stop()
        else:
            self.play(random_start=True)

    def next(self) -> None:
        self._refresh_tracks()
        if not self._tracks:
            return
        self._index = (self._index + 1) % len(self._tracks)
        if self._playing or self._initialized:
            self._play_current()

    def prev(self) -> None:
        self._refresh_tracks()
        if not self._tracks:
            return
        self._index = (self._index - 1) % len(self._tracks)
        if self._playing or self._initialized:
            self._play_current()

    # --- Interne -------------------------------------------------------------

    def _ensure_initialized(self) -> bool:
        if self._initialized:
            return True
        try:
            import pygame
            pygame.mixer.init()
            self._initialized = True
            logger.info("pygame.mixer initialisé")
            return True
        except Exception as exc:
            logger.error("pygame.mixer.init() a échoué : %s", exc)
            return False

    def _refresh_tracks(self) -> None:
        try:
            entries = os.listdir(self._music_dir)
        except OSError:
            self._tracks = []
            return
        self._tracks = sorted(
            os.path.join(self._music_dir, name)
            for name in entries
            if name.lower().endswith(AUDIO_EXTENSIONS)
        )

    def _play_current(self) -> None:
        if not self._tracks:
            self._playing = False
            return
        path = self._tracks[self._index]
        try:
            import pygame
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self._playing = True
            self._poll_timer.start()
            logger.info("♪ Lecture : %s", os.path.basename(path))
        except Exception as exc:
            logger.error("Lecture impossible (%s) : %s", path, exc)
            self._playing = False

    def _check_track_end(self) -> None:
        if not self._initialized or not self._playing:
            return
        try:
            import pygame
            if not pygame.mixer.music.get_busy():
                # Enchaîne sur la piste suivante
                if self._tracks:
                    self._index = (self._index + 1) % len(self._tracks)
                    self._play_current()
                else:
                    self._playing = False
                    self._poll_timer.stop()
        except Exception as exc:
            logger.error("Erreur polling musique : %s", exc)


def _test_track(path: str) -> int:
    """
    Joue un fichier audio en boucle minimale jusqu'à la fin du morceau ou
    Ctrl+C. Initialise pygame.mixer directement, sans Qt, pour valider la
    sortie audio sans dépendre du reste de l'app.
    """
    import os
    import time

    if not os.path.isfile(path):
        print(f"Fichier introuvable : {path}", file=sys.stderr)
        return 2

    try:
        import pygame
    except ImportError as exc:
        print(f"pygame manquant : {exc}", file=sys.stderr)
        return 3

    try:
        pygame.mixer.init()
    except Exception as exc:
        print(f"pygame.mixer.init() a échoué : {exc}", file=sys.stderr)
        return 4

    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        print(f"♪ Lecture : {os.path.basename(path)} (Ctrl+C pour arrêter)")
        try:
            while pygame.mixer.music.get_busy():
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\nArrêt demandé.")
        pygame.mixer.music.stop()
    finally:
        pygame.mixer.quit()
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test rapide du lecteur audio : joue le fichier fourni jusqu'à la fin ou Ctrl+C.",
    )
    parser.add_argument("track", help="Chemin du fichier audio à jouer (mp3, ogg, wav, flac, m4a)")
    args = parser.parse_args()
    sys.exit(_test_track(args.track))
