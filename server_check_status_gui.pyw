#!/usr/bin/env python3
"""Desktop UI for a single server check status test."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from server_check_status import (
    AttemptResult,
    DEFAULT_PORTS,
    ServerTarget,
    check_once,
    parse_attempts,
    parse_port,
    parse_server,
)


APP_TITLE = "Server Check Status"
CUSTOM_PORT_LABEL = "Custom"


class ServerCheckStatusApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("720x420")
        self.root.minsize(620, 360)

        self.server_var = tk.StringVar()
        self.port_choice_var = tk.StringVar(value=DEFAULT_PORTS[0])
        self.custom_port_var = tk.StringVar()
        self.attempts_var = tk.StringVar(value="1")
        self.status_var = tk.StringVar(value="Ready")

        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.is_checking = False

        self._build_ui()
        self.root.after(100, self._poll_results)

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        form = ttk.Frame(self.root, padding=(16, 14, 16, 10))
        form.grid(row=0, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=1)

        ttk.Label(form, text="Server IP or domain").grid(row=0, column=0, sticky="w", pady=4)
        server_entry = ttk.Entry(form, textvariable=self.server_var)
        server_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)

        ttk.Label(form, text="Port").grid(row=1, column=0, sticky="w", pady=4)
        self.port_combo = ttk.Combobox(
            form,
            textvariable=self.port_choice_var,
            values=DEFAULT_PORTS + (CUSTOM_PORT_LABEL,),
            state="readonly",
            width=14,
        )
        self.port_combo.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=4)
        self.port_combo.bind("<<ComboboxSelected>>", self._sync_custom_port_state)

        self.custom_port_entry = ttk.Entry(form, textvariable=self.custom_port_var, width=16, state=tk.DISABLED)
        self.custom_port_entry.grid(row=1, column=2, sticky="w", padx=(10, 0), pady=4)

        ttk.Label(form, text="Attempts").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.attempts_var, width=16).grid(
            row=2,
            column=1,
            sticky="w",
            padx=(10, 0),
            pady=4,
        )

        self.start_button = ttk.Button(form, text="Start", command=self.start_check)
        self.start_button.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=(10, 0))

        results_frame = ttk.Frame(self.root, padding=(16, 0, 16, 10))
        results_frame.grid(row=1, column=0, sticky="nsew")
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        columns = ("attempt", "status", "latency", "address", "error")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        self.results_tree.heading("attempt", text="Attempt")
        self.results_tree.heading("status", text="Status")
        self.results_tree.heading("latency", text="Latency")
        self.results_tree.heading("address", text="Address")
        self.results_tree.heading("error", text="Error")
        self.results_tree.column("attempt", width=80, stretch=False, anchor=tk.CENTER)
        self.results_tree.column("status", width=110, stretch=False)
        self.results_tree.column("latency", width=90, stretch=False)
        self.results_tree.column("address", width=210)
        self.results_tree.column("error", width=260)
        self.results_tree.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.results_tree.configure(yscrollcommand=scroll.set)
        self.results_tree.tag_configure("available", foreground="#0f7b35")
        self.results_tree.tag_configure("unavailable", foreground="#a12622")

        bottom = ttk.Frame(self.root, padding=(16, 0, 16, 12))
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)

        ttk.Label(bottom, textvariable=self.status_var).grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(bottom, mode="determinate")
        self.progress.grid(row=0, column=1, sticky="e", ipadx=90)

        server_entry.focus_set()
        self.root.bind("<Return>", lambda _event: self.start_check())

    def start_check(self) -> None:
        if self.is_checking:
            return

        try:
            server = parse_server(self.server_var.get())
            port = self._read_port()
            attempts = parse_attempts(self.attempts_var.get())
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))
            return

        self._clear_results()
        self.is_checking = True
        self.start_button.configure(state=tk.DISABLED)
        self.progress.configure(maximum=attempts, value=0)
        self.status_var.set("Checking...")

        target = ServerTarget(host=server, port=port)
        thread = threading.Thread(target=self._run_check, args=(target, attempts), daemon=True)
        thread.start()

    def _run_check(self, target: ServerTarget, attempts: int) -> None:
        for attempt in range(1, attempts + 1):
            self.result_queue.put(("result", check_once(target, attempt)))
        self.result_queue.put(("done", None))

    def _poll_results(self) -> None:
        while True:
            try:
                event, payload = self.result_queue.get_nowait()
            except queue.Empty:
                break

            if event == "result" and isinstance(payload, AttemptResult):
                self._add_result(payload)
            elif event == "done":
                self._finish_check()

        self.root.after(100, self._poll_results)

    def _add_result(self, result: AttemptResult) -> None:
        latency = f"{result.latency_ms:.1f} ms" if result.latency_ms is not None else "-"
        self.results_tree.insert(
            "",
            tk.END,
            values=(result.attempt, result.status, latency, result.address, result.error or ""),
            tags=(result.status,),
        )
        self.progress.configure(value=result.attempt)
        self.status_var.set(f"Completed attempt {result.attempt}")

    def _finish_check(self) -> None:
        available = 0
        total = 0
        for item in self.results_tree.get_children():
            values = self.results_tree.item(item, "values")
            total += 1
            if len(values) > 1 and values[1] == "available":
                available += 1

        unavailable = total - available
        self.is_checking = False
        self.start_button.configure(state=tk.NORMAL)
        self.status_var.set(f"Done: {available} available, {unavailable} unavailable")

    def _clear_results(self) -> None:
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.progress.configure(value=0)

    def _sync_custom_port_state(self, _event=None) -> None:
        if self.port_choice_var.get() == CUSTOM_PORT_LABEL:
            self.custom_port_entry.configure(state=tk.NORMAL)
            self.custom_port_entry.focus_set()
        else:
            self.custom_port_entry.configure(state=tk.DISABLED)

    def _read_port(self) -> int:
        if self.port_choice_var.get() == CUSTOM_PORT_LABEL:
            return parse_port(self.custom_port_var.get())
        return parse_port(self.port_choice_var.get())


def main() -> None:
    root = tk.Tk()
    ServerCheckStatusApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
