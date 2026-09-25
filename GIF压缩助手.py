"""A small Windows GUI for reducing animated-GIF frame counts."""

from __future__ import annotations

import queue
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image

from gif_frame_reducer import reduce_gif


WINDOW_TITLE = "GIF 压缩助手"


def size_text(size: int) -> str:
    return f"{size / 1024 / 1024:.1f} MB"


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(WINDOW_TITLE)
        self.minsize(650, 390)
        self.resizable(False, False)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.every = tk.IntVar(value=4)
        self.file_info = tk.StringVar(value="请选择一个 GIF 文件")
        self.mode_info = tk.StringVar()
        self.status = tk.StringVar(value="准备就绪")
        self.frames = 0
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()

        self._make_ui()
        self._update_mode_info()
        self.after(120, self._read_events)

    def _make_ui(self) -> None:
        root = ttk.Frame(self, padding=22)
        root.pack(fill="both", expand=True)
        root.columnconfigure(1, weight=1)

        ttk.Label(root, text="GIF 压缩助手", font=("Microsoft YaHei UI", 18, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(
            root,
            text="减少动画帧数来缩小体积，播放总时长保持不变。",
            foreground="#555555",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(3, 20))

        ttk.Label(root, text="原始 GIF").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(root, textvariable=self.input_path, state="readonly").grid(
            row=2, column=1, sticky="ew", padx=10
        )
        ttk.Button(root, text="选择文件…", command=self.choose_input).grid(row=2, column=2)
        ttk.Label(root, textvariable=self.file_info, foreground="#555555").grid(
            row=3, column=1, columnspan=2, sticky="w", pady=(0, 18)
        )

        ttk.Separator(root).grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 18))
        ttk.Label(root, text="压缩力度").grid(row=5, column=0, sticky="nw", pady=5)
        strength = ttk.Frame(root)
        strength.grid(row=5, column=1, columnspan=2, sticky="ew")
        strength.columnconfigure(0, weight=1)
        tk.Scale(
            strength,
            from_=2,
            to=12,
            orient="horizontal",
            variable=self.every,
            command=lambda _value: self._update_mode_info(),
            showvalue=True,
            resolution=1,
            length=410,
        ).grid(row=0, column=0, sticky="ew")
        ttk.Label(strength, textvariable=self.mode_info, foreground="#555555").grid(
            row=1, column=0, sticky="w", pady=(2, 12)
        )

        ttk.Label(root, text="保存到").grid(row=6, column=0, sticky="w", pady=5)
        ttk.Entry(root, textvariable=self.output_path).grid(row=6, column=1, sticky="ew", padx=10)
        ttk.Button(root, text="更改位置…", command=self.choose_output).grid(row=6, column=2)

        ttk.Separator(root).grid(row=7, column=0, columnspan=3, sticky="ew", pady=18)
        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.grid(row=8, column=0, columnspan=2, sticky="ew", padx=(0, 12))
        self.start_button = ttk.Button(root, text="开始压缩", command=self.start, style="Accent.TButton")
        self.start_button.grid(row=8, column=2, sticky="e")
        ttk.Label(root, textvariable=self.status, foreground="#555555").grid(
            row=9, column=0, columnspan=3, sticky="w", pady=(9, 0))

    def choose_input(self) -> None:
        chosen = filedialog.askopenfilename(
            title="选择 GIF 文件", filetypes=[("GIF 动画", "*.gif"), ("所有文件", "*.*")]
        )
        if not chosen:
            return
        source = Path(chosen)
        self.input_path.set(str(source))
        self.output_path.set(str(source.with_name(f"{source.stem}_reduced.gif")))
        self.file_info.set(f"正在读取 {source.name}…")
        threading.Thread(target=self._inspect_file, args=(source,), daemon=True).start()

    def _inspect_file(self, source: Path) -> None:
        try:
            with Image.open(source) as gif:
                frames = getattr(gif, "n_frames", 1)
            self.events.put(("info", (source, frames, source.stat().st_size)))
        except Exception as error:
            self.events.put(("error", f"无法读取 GIF：{error}"))

    def choose_output(self) -> None:
        current = self.output_path.get() or "压缩后.gif"
        chosen = filedialog.asksaveasfilename(
            title="选择保存位置",
            initialfile=Path(current).name,
            defaultextension=".gif",
            filetypes=[("GIF 动画", "*.gif")],
        )
        if chosen:
            self.output_path.set(chosen)

    def _update_mode_info(self) -> None:
        every = self.every.get()
        kept = (self.frames + every - 1) // every if self.frames else 0
        hint = "推荐" if every == 4 else ("更流畅" if every < 4 else "体积更小")
        estimate = f"预计 {self.frames} 帧 → {kept} 帧；" if self.frames else ""
        self.mode_info.set(f"{estimate}每 {every} 帧保留 1 帧（{hint}）")

    def start(self) -> None:
        source_text, output_text = self.input_path.get().strip(), self.output_path.get().strip()
        if not source_text or not Path(source_text).is_file():
            messagebox.showwarning(WINDOW_TITLE, "请先选择一个存在的 GIF 文件。")
            return
        if not output_text:
            messagebox.showwarning(WINDOW_TITLE, "请设置输出文件位置。")
            return
        source, output = Path(source_text).resolve(), Path(output_text).resolve()
        if source == output:
            messagebox.showwarning(WINDOW_TITLE, "输出文件不能和原文件相同。")
            return
        if output.exists() and not messagebox.askyesno(WINDOW_TITLE, "输出文件已存在，是否覆盖？"):
            return

        self.start_button.configure(state="disabled")
        self.progress.start(12)
        self.status.set("正在抽帧并重新压缩，大文件可能需要几分钟…")
        threading.Thread(target=self._compress, args=(source, output, self.every.get()), daemon=True).start()

    def _compress(self, source: Path, output: Path, every: int) -> None:
        try:
            before = source.stat().st_size
            original_frames, output_frames, after = reduce_gif(source, output, every)
            self.events.put(("done", (output, original_frames, output_frames, before, after)))
        except Exception as error:
            self.events.put(("error", f"压缩失败：{error}"))

    def _read_events(self) -> None:
        try:
            while True:
                event, value = self.events.get_nowait()
                if event == "info":
                    source, self.frames, size = value  # type: ignore[misc]
                    self.file_info.set(f"{source.name}  ·  {self.frames} 帧  ·  {size_text(size)}")
                    self._update_mode_info()
                elif event == "done":
                    output, old_frames, new_frames, before, after = value  # type: ignore[misc]
                    self.progress.stop()
                    self.start_button.configure(state="normal")
                    saved = (1 - after / before) * 100 if before else 0
                    self.status.set(f"完成：{output.name}  ·  {old_frames} → {new_frames} 帧  ·  减少 {saved:.1f}%")
                    messagebox.showinfo(
                        WINDOW_TITLE,
                        f"压缩完成！\n\n输出：{output}\n帧数：{old_frames} → {new_frames}\n大小：{size_text(before)} → {size_text(after)}\n减少：{saved:.1f}%",
                    )
                elif event == "error":
                    self.progress.stop()
                    self.start_button.configure(state="normal")
                    self.status.set(str(value))
                    messagebox.showerror(WINDOW_TITLE, str(value))
        except queue.Empty:
            pass
        self.after(120, self._read_events)


if __name__ == "__main__":
    App().mainloop()
