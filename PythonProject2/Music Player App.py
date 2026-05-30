import os
import vlc

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty
from kivymd.app import MDApp

Window.size = (400, 600)


class MusicPlayerApp(MDApp):
    current_song_name = StringProperty("No song loaded")
    status_text = StringProperty("Ready")
    time_text = StringProperty("00:00 / 00:00")
    progress_value = NumericProperty(0)

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"

        self.music_dir = "music"
        self.song_list = []
        self.current_song_index = 0

        # ساخت موتور VLC
        # کامنت فارسی: این instance موتور پخش VLC است
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()

        # کامنت فارسی: مدت زمان آهنگ فعلی (ms)
        self.duration_ms = 0

        self.load_song_list()

        # کامنت فارسی: آپدیت UI و تشخیص پایان آهنگ
        Clock.schedule_interval(self._tick, 0.25)

        return Builder.load_file("musicplayer.kv")

    # -------------------------
    # ابزار کمکی
    # -------------------------
    def _fmt(self, sec):
        # کامنت فارسی: تبدیل ثانیه به دقیقه:ثانیه
        sec = int(max(0, sec))
        return f"{sec//60:02}:{sec%60:02}"

    def _song_path(self):
        # کامنت فارسی: ساخت مسیر آهنگ فعلی
        if not self.song_list:
            return None
        return os.path.join(self.music_dir, self.song_list[self.current_song_index])

    # -------------------------
    # کتابخانه آهنگ‌ها
    # -------------------------
    def load_song_list(self):
        # کامنت فارسی: ساخت پوشه در صورت نبود
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir)

        self.song_list = sorted([
            f for f in os.listdir(self.music_dir)
            if f.lower().endswith((".mp3", ".wav", ".ogg", ".flac", ".m4a"))
        ])

        if self.song_list:
            self.current_song_index = max(0, min(self.current_song_index, len(self.song_list) - 1))
            self.current_song_name = self.song_list[self.current_song_index]
            self.status_text = f"{len(self.song_list)} songs found"
        else:
            self.current_song_name = "No audio file found"
            self.status_text = "Put audio files into music/ folder"

    def reload_library(self):
        # کامنت فارسی: بازخوانی پوشه موزیک
        self.stop_music()
        self.load_song_list()

    # -------------------------
    # کنترل پخش
    # -------------------------
    def play_music(self):
        if not self.song_list:
            self.status_text = "Library is empty"
            return

        path = self._song_path()
        if not path or not os.path.exists(path):
            self.status_text = "File not found"
            return

        try:
            # کامنت فارسی: ساخت مدیا و ست کردن روی پلیر
            media = self.vlc_instance.media_new(path)
            self.player.set_media(media)

            # کامنت فارسی: شروع پخش
            self.player.play()

            self.current_song_name = os.path.basename(path)
            self.status_text = "Playing"

            # کامنت فارسی: ریست UI
            self.progress_value = 0
            self.time_text = "00:00 / 00:00"
            self.duration_ms = 0

        except Exception as e:
            self.status_text = f"VLC error: {e}"

    def pause_or_resume(self):
        # کامنت فارسی: pause/resume در VLC با toggle انجام می‌شود
        try:
            if self.player.is_playing():
                self.player.pause()
                self.status_text = "Paused"
            else:
                # اگر قبلاً مدیا ست شده باشد، دوباره play می‌شود
                self.player.play()
                self.status_text = "Playing"
        except Exception as e:
            self.status_text = f"Pause error: {e}"

    def stop_music(self):
        # کامنت فارسی: توقف کامل
        try:
            self.player.stop()
        except Exception:
            pass
        self.status_text = "Stopped"
        self.progress_value = 0
        self.time_text = "00:00 / 00:00"
        self.duration_ms = 0

    def next_song(self):
        if not self.song_list:
            return
        self.current_song_index = (self.current_song_index + 1) % len(self.song_list)
        self.play_music()

    def previous_song(self):
        if not self.song_list:
            return
        self.current_song_index = (self.current_song_index - 1) % len(self.song_list)
        self.play_music()

    # -------------------------
    # حلقه آپدیت
    # -------------------------
    def _tick(self, dt):
        # کامنت فارسی: اگر مدیا نداریم کاری نکن
        if not self.player:
            return

        try:
            # کامنت فارسی: زمان فعلی (ms) و طول کل (ms)
            cur = self.player.get_time()        # ms
            length = self.player.get_length()   # ms

            if length and length > 0:
                self.duration_ms = length

            if cur is None or cur < 0:
                cur = 0

            # کامنت فارسی: آپدیت متن زمان
            if self.duration_ms > 0:
                self.time_text = f"{self._fmt(cur/1000)} / {self._fmt(self.duration_ms/1000)}"
                self.progress_value = min((cur / self.duration_ms) * 100.0, 100.0)
            else:
                self.time_text = f"{self._fmt(cur/1000)} / --:--"
                self.progress_value = 0

            # کامنت فارسی: تشخیص اتمام آهنگ (وقتی طول مشخص است و به آخر می‌رسیم)
            if self.duration_ms > 0 and cur >= self.duration_ms - 250 and self.player.get_state() in (
                vlc.State.Ended,
                vlc.State.Stopped,
            ):
                self.next_song()

        except Exception:
            # کامنت فارسی: در صورت خطا فعلاً سکوت می‌کنیم تا برنامه کرش نکند
            pass


if __name__ == "__main__":
    MusicPlayerApp().run()
