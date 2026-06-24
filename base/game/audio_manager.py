"""
--- Channel layout -----------------------------------------------------------
    0  - Ambient A   (looping background environment)
    1  - Ambient B   (optional second ambient layer)
    2  - UI / SFX    (menu clicks, item pickups SFX)
    3  - Voice       (per-character typewriter tick for dialogue, for Nina)
    4  - Event SFX   (separate from UI)
    5–7 - Overflow   (extra SFX channels)
-------------------------------------------------------------------------------
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

try:
    import pygame.mixer as _mixer

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Channel index constants
CH_AMBIENT_A = 0
CH_AMBIENT_B = 1
CH_UI = 2
CH_VOICE = 3
CH_EVENT = 4
_TOTAL_CHANNELS = 8  # Channels 5–7 are overflow for rapid SFX bursts


# noinspection PyTypeChecker
class AudioManager:
    """
    Parameters:
        assets_dir : str or Path
            Directory where all audio files live.
            Defaults to  {script_location}/assets/audio/
        enabled : bool
            Set to False to run in silent mode. Defaults to True.
        frequency : int
            Sample rate for the audio mixer. 44100 Hz is CD quality and
            works on virtually all hardware. Defaults to 44100.
        buffer : int
            Mixer buffer size in samples. Smaller = lower latency but
            more CPU load. 256 works well for games. Defaults to 256.
    """

    def __init__(
            self,
            assets_dir: str | Path = "assets/audio",
            enabled: bool = True,
            frequency: int = 44100,
            buffer: int = 256,
    ) -> None:
        self._enabled: bool = enabled and AUDIO_AVAILABLE
        self._assets_dir: Path = Path(assets_dir)
        self._lock = threading.Lock()

        # State flags
        self._muted: bool = False
        self._paused: bool = False

        # Per-category base volumes (0.0 – 1.0).
        # Effective volume = master_vol * category_vol  (clamped to [0, 1]).
        self._master_vol: float = 1.0
        self._music_vol: float = 0.6
        self._ambient_vol: float = 0.5
        self._sfx_vol: float = 0.7
        self._voice_vol: float = 0.8

        # Sound object cache: resolved path string -> pygame.mixer.Sound
        # Avoids re-reading the disk on every play() call.
        self._cache: dict = {}

        if self._enabled:
            try:
                _mixer.pre_init(
                    frequency=frequency,
                    size=-16,  # 16-bit signed PCM
                    channels=2,  # stereo
                    buffer=buffer,
                )
                _mixer.init()
                _mixer.set_num_channels(_TOTAL_CHANNELS)
            except Exception as e:
                self._enabled = False
                print(f"[AudioManager] Warning: could not initialise audio - {e}")

    # Internal helpers

    def _resolve(self, filename: str) -> Optional[Path]:
        """
        Return the full Path for a filename inside assets_dir, or None if the
        file does not exist. Prints a warning in the latter case only for music
        and ambient (callers for SFX suppress warnings to avoid spam).
        """
        path = self._assets_dir / filename
        return path if path.exists() else None

    def _load(self, path: Path) -> Optional[object]:
        """
        Return a cached pygame.mixer.Sound for the given path, loading from
        disk only on the first call. Returns None on failure.
        """
        key = str(path)
        if key not in self._cache:
            try:
                self._cache[key] = _mixer.Sound(key)
            except Exception as e:
                print(f"[AudioManager] Could not load '{path.name}': {e}")
                return None
        return self._cache[key]

    def _effective_vol(self, category_vol: float) -> float:
        """
        Apply master volume and mute flag on top of a category volume.
        Returns 0.0 when muted, otherwise master × category clamped to [0, 1].
        """
        if self._muted:
            return 0.0
        return max(0.0, min(1.0, self._master_vol * category_vol))

    # Music (pygame.mixer.music + single streaming track)

    def play_music(
            self,
            filename: str,
            loops: int = -1,
            fade_in_ms: int = 1500,
    ) -> None:
        """
        Stream a background music file. Replaces any currently playing track.

        Parameters:
            filename: audio file inside assets_dir
            loops: number of repeats -1 = loop forever
            fade_in_ms: milliseconds to fade in from silence
        """
        if not self._enabled:
            return
        path = self._resolve(filename)
        if path is None:
            print(f"[AudioManager] Music file not found: {filename}")
            return
        with self._lock:
            _mixer.music.load(str(path))
            _mixer.music.set_volume(self._effective_vol(self._music_vol))
            _mixer.music.play(loops=loops, fade_ms=fade_in_ms)

    def crossfade_music(
            self,
            filename: str,
            fade_ms: int = 1500,
            loops: int = -1,
    ) -> None:
        """
        Smoothly transition from the current track to a new one.
        The current track fades out while the new one fades in.

        Parameters:
            filename: new music file inside assets_dir
            fade_ms: duration of both the fade-out and fade-in
            loops: repeat count for the incoming track; -1 = forever
        """
        if not self._enabled:
            return
        path = self._resolve(filename)
        if path is None:
            print(f"[AudioManager] Music file not found: {filename}")
            return
        with self._lock:
            _mixer.music.fadeout(fade_ms)
            _mixer.music.load(str(path))
            _mixer.music.set_volume(self._effective_vol(self._music_vol))
            _mixer.music.play(loops=loops, fade_ms=fade_ms)

    def stop_music(self, fade_out_ms: int = 0) -> None:
        """
        Stop background music. Pass fade_out_ms > 0 for a smooth end.
        """
        if not self._enabled:
            return
        with self._lock:
            if fade_out_ms:
                _mixer.music.fadeout(fade_out_ms)
            else:
                _mixer.music.stop()

    def pause_music(self) -> None:
        """Pause the music track (preserves playback position)."""
        if self._enabled:
            _mixer.music.pause()

    def resume_music(self) -> None:
        """Resume a paused music track from where it left off."""
        if self._enabled:
            _mixer.music.unpause()

    def music_is_playing(self) -> bool:
        """Return True if a music track is currently active (not paused/stopped)."""
        return self._enabled and bool(_mixer.music.get_busy())

    # Ambient sounds using (channels CH_AMBIENT_A and CH_AMBIENT_B)

    def play_ambient(
            self,
            filename: str,
            layer: int = CH_AMBIENT_A,
            fade_in_ms: int = 2000,
    ) -> None:
        """
        Play a looping ambient sound (tavern noise, forest birds, rain, etc.).
        Two independent layers are available: CH_AMBIENT_A (default) and
        CH_AMBIENT_B, so you can stack, different ambiences.

        Parameters:
            filename: audio file inside assets_dir
            layer: CH_AMBIENT_A (0) or CH_AMBIENT_B (1)
            fade_in_ms: milliseconds to fade in from silence
        """
        if not self._enabled:
            return
        if layer not in (CH_AMBIENT_A, CH_AMBIENT_B):
            print(f"[AudioManager] Invalid ambient layer: {layer}. Use CH_AMBIENT_A or CH_AMBIENT_B.")
            return
        path = self._resolve(filename)
        if path is None:
            print(f"[AudioManager] Ambient file not found: {filename}")
            return
        sound = self._load(path)
        if sound is None:
            return
        with self._lock:
            sound.set_volume(self._effective_vol(self._ambient_vol))
            _mixer.Channel(layer).play(sound, loops=-1, fade_ms=fade_in_ms)

    def stop_ambient(
            self,
            layer: int = CH_AMBIENT_A,
            fade_out_ms: int = 1500,
    ) -> None:
        """
        Stop an ambient layer. Pass fade_out_ms=0 for an immediate cut.
        """
        if not self._enabled:
            return
        with self._lock:
            ch = _mixer.Channel(layer)
            if fade_out_ms:
                ch.fadeout(fade_out_ms)
            else:
                ch.stop()

    def stop_all_ambient(self, fade_out_ms: int = 1500) -> None:
        """Stop both ambient layers at once."""
        self.stop_ambient(CH_AMBIENT_A, fade_out_ms)
        self.stop_ambient(CH_AMBIENT_B, fade_out_ms)

    # UI / SFX (channel CH_UI)

    def play_sfx(self, filename: str) -> None:
        """
        Plays a Sound Effect of choice.
        Missing files are silently ignored to avoid spamming the log.

        Parameters:
            filename : file inside assets_dir (e.g. "menu_click.wav")
        """
        if not self._enabled:
            return
        path = self._resolve(filename)
        if path is None:
            return  # Silent — missing SFX shouldn't break gameplay
        sound = self._load(path)
        if sound is None:
            return
        with self._lock:
            sound.set_volume(self._effective_vol(self._sfx_vol))
            _mixer.Channel(CH_UI).play(sound)

    # Event SFX (channel CH_EVENT, separate from UI)

    def play_event_sfx(self, filename: str) -> None:
        """
        Plays an important sound effect that comes from an event.
        Uses a dedicated channel so it never cuts off a UI click mid-play.

        Parameters:
            filename: file inside assets_dir (e.g. "milestone.wav")
        """
        if not self._enabled:
            return
        path = self._resolve(filename)
        if path is None:
            return
        sound = self._load(path)
        if sound is None:
            return
        with self._lock:
            sound.set_volume(self._effective_vol(self._sfx_vol))
            _mixer.Channel(CH_EVENT).play(sound)

    # Voice tick (channel CH_VOICE)

    def play_voice_tick(self, filename: str = "voice_tick.wav") -> None:
        """
        Play a short click once per dialogue character (typewriter effect).
        Silently skips if a tick is already playing to prevent rapid overlap.

        Parameters:
            filename : short click/tick sound inside assets_dir
        """
        if not self._enabled:
            return
        path = self._resolve(filename)
        if path is None:
            return
        sound = self._load(path)
        if sound is None:
            return
        with self._lock:
            ch = _mixer.Channel(CH_VOICE)
            if not ch.get_busy():  # Don't stack ticks on rapid text output
                sound.set_volume(self._effective_vol(self._voice_vol))
                ch.play(sound)

    # Pause / Resume all

    def pause_all(self) -> None:
        """
        Pause every channel and the music stream simultaneously.
        Playback positions are preserved. Call resume_all() to continue.
        """
        if not self._enabled or self._paused:
            return
        with self._lock:
            _mixer.pause()  # Pauses all Sound channels
            _mixer.music.pause()  # Pauses the music stream
            self._paused = True

    def resume_all(self) -> None:
        """Resume everything that was paused with pause_all()."""
        if not self._enabled or not self._paused:
            return
        with self._lock:
            _mixer.unpause()
            _mixer.music.unpause()
            self._paused = False

    # Stop everything

    def stop_all(self, fade_out_ms: int = 0) -> None:
        """
        Stop all audio immediately or with a fade-out.
        Use at scene exits, game over screens, or application shutdown.

        Parameters:
            fade_out_ms: if > 0, fade all channels out over this duration
        """
        if not self._enabled:
            return
        with self._lock:
            if fade_out_ms:
                _mixer.fadeout(fade_out_ms)
                _mixer.music.fadeout(fade_out_ms)
            else:
                _mixer.stop()
                _mixer.music.stop()
        self._paused = False

    # Mute toggle

    def mute(self) -> None:
        """
        Silence all audio output without stopping or unloading anything.
        Playback continues internally. unmute() restores all sounds instantly.
        """
        self._muted = True
        self._apply_all_volumes()

    def unmute(self) -> None:
        """Restore audio after muting."""
        self._muted = False
        self._apply_all_volumes()

    def toggle_mute(self) -> bool:
        """
        Flip the mute state and return the new value.
        Returns True if now muted, False if now unmuted.
        """
        if self._muted:
            self.unmute()
        else:
            self.mute()
        return self._muted

    # Volume control

    def set_master_volume(self, volume: float) -> None:
        """
        Set the master volume multiplier (0.0–1.0).
        Effective volume for every category = master * category, clamped.
        """
        self._master_vol = max(0.0, min(1.0, volume))
        self._apply_all_volumes()

    def set_music_volume(self, volume: float) -> None:
        """Set the background music volume (0.0–1.0)."""
        self._music_vol = max(0.0, min(1.0, volume))
        if self._enabled:
            _mixer.music.set_volume(self._effective_vol(self._music_vol))

    def set_ambient_volume(self, volume: float) -> None:
        """Set the ambient layer volume (0.0–1.0). Affects both layers."""
        self._ambient_vol = max(0.0, min(1.0, volume))
        if self._enabled:
            for layer in (CH_AMBIENT_A, CH_AMBIENT_B):
                _mixer.Channel(layer).set_volume(
                    self._effective_vol(self._ambient_vol)
                )

    def set_sfx_volume(self, volume: float) -> None:
        """Set the SFX / event sound volume (0.0–1.0)."""
        self._sfx_vol = max(0.0, min(1.0, volume))

    def set_voice_volume(self, volume: float) -> None:
        """Set the voice tick volume (0.0–1.0)."""
        self._voice_vol = max(0.0, min(1.0, volume))

    def _apply_all_volumes(self) -> None:
        """
        Reapply effective volumes to all live channels.
        Called automatically after mute/unmute or master volume changes.
        Only music and the ambient channels can be updated mid-playback;
        SFX and voice volumes take effect on the next play() call.
        """
        if not self._enabled:
            return
        _mixer.music.set_volume(self._effective_vol(self._music_vol))
        for layer in (CH_AMBIENT_A, CH_AMBIENT_B):
            _mixer.Channel(layer).set_volume(
                self._effective_vol(self._ambient_vol)
            )

    # Scene transitions

    def transition_scene(
            self,
            music: Optional[str] = None,
            ambient_a: Optional[str] = None,
            ambient_b: Optional[str] = None,
            fade_ms: int = 1500,
    ) -> None:
        """
        Perform a full scene audio transition in one call.
        Crossfades the music and replaces the ambient layer(s) with a brief
        delay so the old ambient finishes fading before the new one starts.

        Parameters:
            music     : new music filename, or None to leave unchanged
            ambient_a : new primary ambient filename, or None to leave unchanged
            ambient_b : new secondary ambient filename, or None to stop layer B
            fade_ms   : duration of all crossfades in milliseconds

        Example — entering a dungeon from a forest:
            audio.transition_scene(
                music="dungeon_theme.ogg",
                ambient_a="stone_dripping.ogg",
                fade_ms=2000,
            )
        """
        if music:
            self.crossfade_music(music, fade_ms=fade_ms)

        if ambient_a is not None:
            self.stop_ambient(CH_AMBIENT_A, fade_out_ms=fade_ms)
            # Delay the new ambient until after the old one has faded out
            threading.Timer(
                fade_ms / 1000.0,
                self.play_ambient,
                args=(ambient_a,),
                kwargs={"layer": CH_AMBIENT_A, "fade_in_ms": fade_ms // 2},
            ).start()

        if ambient_b is not None:
            self.stop_ambient(CH_AMBIENT_B, fade_out_ms=fade_ms)
            threading.Timer(
                fade_ms / 1000.0,
                self.play_ambient,
                args=(ambient_b,),
                kwargs={"layer": CH_AMBIENT_B, "fade_in_ms": fade_ms // 2},
            ).start()
        elif ambient_b == "":
            # Passing an empty string explicitly stops layer B without
            # starting anything new. Passing None leaves it alone.
            self.stop_ambient(CH_AMBIENT_B, fade_out_ms=fade_ms)

    # Sound cache management

    def preload(self, *filenames: str) -> None:
        """
        Load one or more sound files into the cache at startup.
        Call this during your game's loading screen so the first in-game
        play() call has zero disk latency.

        Example:
            audio.preload(
                "menu_click.wav",
                "sword_hit.wav",
                "voice_tick.wav",
                "item_pickup.wav",
            )
        """
        for filename in filenames:
            path = self._resolve(filename)
            if path:
                self._load(path)
            else:
                print(f"[AudioManager] Preload — file not found: {filename}")

    def clear_cache(self) -> None:
        """
        Evict all cached Sound objects from memory.
        Call between major scenes if RAM is tight. Sounds will be reloaded
        from disk on the next play() call.
        """
        with self._lock:
            self._cache.clear()

    # Status / introspection

    @property
    def available(self) -> bool:
        """False if pygame is not installed or audio initialization failed."""
        return self._enabled

    @property
    def is_muted(self) -> bool:
        """True if mute() has been called and unmute() has not."""
        return self._muted

    @property
    def is_paused(self) -> bool:
        """True while pause_all() is active."""
        return self._paused

    def __repr__(self) -> str:
        status = "enabled" if self._enabled else "disabled (no pygame)"
        flags = ""
        if self._muted:  flags += " [MUTED]"
        if self._paused: flags += " [PAUSED]"
        return (
            f"<AudioManager {status}{flags} | "
            f"master={self._master_vol:.2f}  "
            f"music={self._music_vol:.2f}  "
            f"ambient={self._ambient_vol:.2f}  "
            f"sfx={self._sfx_vol:.2f}  "
            f"voice={self._voice_vol:.2f}  "
            f"cache={len(self._cache)} sounds>"
        )


# SoundEffect class. Allows for insances of sound effects that can be played manually.

class SoundEffect:
    """
    A thin wrapper around a single pygame Sound object.
    Useful when you want to hold a reference to one specific sound and call
    .play() on it directly, rather than going through the AudioManager each time.
    """

    def __init__(self, path: str, volume: float = 1.0) -> None:
        """
        Parameters:
            path   : full path to the sound file
            volume : initial playback volume (0.0–1.0)
        """
        if not AUDIO_AVAILABLE:
            self._sound = None
            return
        try:
            self._sound = _mixer.Sound(path)
            self._sound.set_volume(max(0.0, min(1.0, volume)))
        except Exception as e:
            print(f"[SoundEffect] Could not load '{path}': {e}")
            self._sound = None

    def play(self) -> None:
        """Play the sound (non-blocking, returns immediately)."""
        if self._sound is not None:
            self._sound.play()

    def set_volume(self, volume: float) -> None:
        """Adjust the playback volume (0.0–1.0)."""
        if self._sound is not None:
            self._sound.set_volume(max(0.0, min(1.0, volume)))


audio = AudioManager()
