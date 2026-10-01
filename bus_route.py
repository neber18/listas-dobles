import tkinter as tk
from tkinter import ttk, messagebox

# Palette (same as the class slides)
NAVY, BLUE, ORANGE, PURPLE = "#253070", "#527BFF", "#FFAA00", "#92208F"
BG, CARD, ORANGE_LIGHT, GRAY = "#F7F8FC", "#FFFFFF", "#FFE9B3", "#7A7F99"
FONT = "Segoe UI"


# ----------------------------------------------------------------- Data layer
class Node:
    def __init__(self, value):
        self.value = value      # (stop_name, zone)
        self.next = None
        self.prev = None


class DoublyLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.length = 0

    def append(self, value):                      # add to end
        node = Node(value)
        if self.head is None:
            self.head = self.tail = node
        else:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        self.length += 1
        return node

    def prepend(self, value):                     # add to start
        node = Node(value)
        if self.head is None:
            self.head = self.tail = node
        else:
            node.next = self.head
            self.head.prev = node
            self.head = node
        self.length += 1
        return node

    def traverse_to_index(self, index):
        """Start from the closest end (the advantage of a double list)."""
        if index < self.length // 2:
            current, i = self.head, 0
            while i != index:
                current = current.next
                i += 1
        else:
            current, i = self.tail, self.length - 1
            while i != index:
                current = current.prev
                i -= 1
        return current

    def insert(self, index, value):
        if index <= 0:
            return self.prepend(value)
        if index >= self.length:
            return self.append(value)
        node = Node(value)
        leader = self.traverse_to_index(index - 1)
        follower = leader.next
        leader.next = node
        node.prev = leader
        node.next = follower
        follower.prev = node
        self.length += 1
        return node

    def remove(self, index):
        """Remove the node at index and return it."""
        if not 0 <= index < self.length:
            raise IndexError("Index out of range")
        node = self.traverse_to_index(index)
        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
        self.length -= 1
        return node

    def nodes(self):                              # head -> tail
        current = self.head
        while current:
            yield current
            current = current.next


# ------------------------------------------------------------------ Frontend
SOFT, LINE, PALE_BLUE = "#F4F6FB", "#DDE1F0", "#DDE3F7"
ZONE_COLORS = {"A": "#527BFF", "B": "#92208F", "C": "#F59E0B", "D": "#10B981"}


def rrect(c, x1, y1, x2, y2, r=12, **kw):
    """Rounded rectangle on a canvas."""
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2,
           x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def draw_bus(c, cx, cy, s=1.0, body=ORANGE):
    w, h = 64 * s, 34 * s
    x1, y1 = cx - w / 2, cy - h / 2
    rrect(c, x1, y1, x1 + w, y1 + h, 9 * s, fill=body, outline="")
    for i in range(3):
        wx = x1 + 7 * s + i * 17 * s
        rrect(c, wx, y1 + 6 * s, wx + 13 * s, y1 + 17 * s, 3 * s, fill="white", outline="")
    c.create_rectangle(x1 + 3 * s, y1 + 22 * s, x1 + w - 3 * s, y1 + 25 * s, fill=NAVY, outline="")
    for wx in (x1 + 14 * s, x1 + w - 14 * s):
        c.create_oval(wx - 6 * s, y1 + h - 6 * s, wx + 6 * s, y1 + h + 6 * s, fill=NAVY, outline="white", width=2)


class RoundButton(tk.Canvas):
    def __init__(self, parent, text, command, color=BLUE, hover=NAVY, bg=CARD, height=40):
        super().__init__(parent, width=10, height=height, bg=bg, highlightthickness=0, cursor="hand2")
        self.text, self.command, self.color, self.hover = text, command, color, hover
        self.bind("<Configure>", lambda e: self._draw(self.color))
        self.bind("<Enter>", lambda e: self._draw(self.hover))
        self.bind("<Leave>", lambda e: self._draw(self.color))
        self.bind("<Button-1>", lambda e: self.command())

    def _draw(self, fill):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        rrect(self, 1, 1, w - 1, h - 1, 14, fill=fill, outline=fill)
        self.create_text(w / 2, h / 2, text=self.text, fill="white", font=(FONT, 10, "bold"))


class BusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ruta de Bus")
        self.geometry("1140x720")
        self.minsize(1000, 680)
        self.configure(bg=SOFT)
        ttk.Style(self).theme_use("clam")

        self.route = DoublyLinkedList()
        self.bus = None
        self.outbound = True          # True: ida (next) | False: regreso (prev)

        self._build_ui()
        for stop in [("Estación Central", "A"), ("Alcaldía", "A"), ("Universidad", "B"),
                     ("Hospital", "B"), ("Aeropuerto", "C")]:
            self.route.append(stop)
        self.bus = self.route.head
        self.refresh()
        self.say("¡Bienvenido! Aquí puedes mover el bus por la ruta, cambiar su sentido "
                 "y agregar o eliminar paradas.")

    # -- UI building
    def _paint_header(self, event):
        c, w = self.header, event.width
        c.delete("all")
        a, b = (37, 48, 112), (82, 123, 255)
        for x in range(0, w, 4):                       # horizontal gradient
            t = x / max(w, 1)
            col = "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
            c.create_rectangle(x, 0, x + 4, 88, fill=col, outline="")
        draw_bus(c, 62, 44, 1.1)
        c.create_text(112, 34, text="Ruta de Bus", anchor="w", fill="white", font=(FONT, 22, "bold"))
        c.create_text(112, 62, text="Sigue el recorrido y administra las paradas", anchor="w",
                      fill="#D6DEFF", font=(FONT, 10))
        rrect(c, w - 200, 30, w - 24, 58, 14, fill=ORANGE, outline="")
        c.create_text(w - 112, 44, text="Transporte público", fill=NAVY, font=(FONT, 10, "bold"))

    def _card(self, parent, title, accent=BLUE):
        outer = tk.Frame(parent, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        tk.Frame(outer, bg=accent, height=4).pack(fill="x")
        tk.Label(outer, text=title, bg=CARD, fg=NAVY, font=(FONT, 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
        return outer

    def _entry(self, parent, label, var):
        tk.Label(parent, text=label, bg=CARD, fg=GRAY, font=(FONT, 9)).pack(anchor="w", padx=14)
        tk.Entry(parent, textvariable=var, font=(FONT, 11), relief="flat", bg=SOFT, fg=NAVY,
                 insertbackground=NAVY, highlightthickness=2, highlightbackground=LINE,
                 highlightcolor=BLUE).pack(fill="x", padx=14, pady=(2, 8), ipady=5)

    def _build_ui(self):
        self.header = tk.Canvas(self, height=88, highlightthickness=0)
        self.header.pack(fill="x")
        self.header.bind("<Configure>", self._paint_header)

        body = tk.Frame(self, bg=SOFT)
        body.pack(fill="both", expand=True, padx=16, pady=14)
        left = tk.Frame(body, bg=SOFT, width=340)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        right = tk.Frame(body, bg=SOFT)
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))

        # Bus status card
        card = self._card(left, "🚌  Estado del bus", ORANGE)
        card.pack(fill="x", pady=(0, 12))
        self.stop_var, self.nav_var = tk.StringVar(), tk.StringVar()
        tk.Label(card, text="Está en la parada", bg=CARD, fg=GRAY, font=(FONT, 9)).pack()
        tk.Label(card, textvariable=self.stop_var, bg=CARD, fg=NAVY, font=(FONT, 17, "bold"),
                 wraplength=300).pack(padx=14)
        self.dir_label = tk.Label(card, bg=BLUE, fg="white", font=(FONT, 9, "bold"), padx=12, pady=3)
        self.dir_label.pack(pady=8)
        tk.Label(card, textvariable=self.nav_var, bg=CARD, fg=GRAY, font=(FONT, 10),
                 justify="left").pack(padx=14)
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", padx=14, pady=14)
        row.columnconfigure((0, 1), weight=1, uniform="a")
        RoundButton(row, "Avanzar ▶", self.advance, ORANGE, "#D98F00").grid(row=0, column=0, sticky="ew", padx=(0, 4))
        RoundButton(row, "⇄ Cambiar sentido", self.toggle_direction, PURPLE, NAVY).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # Form card
        card = self._card(left, "✏️  Administrar paradas", BLUE)
        card.pack(fill="x")
        self.name_var, self.zone_var, self.index_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self._entry(card, "Nombre de la parada", self.name_var)
        self._entry(card, "Zona (A, B, C...)", self.zone_var)
        self._entry(card, "Número de parada (1 = la primera)", self.index_var)
        grid = tk.Frame(card, bg=CARD)
        grid.pack(fill="x", padx=14, pady=(2, 14))
        grid.columnconfigure((0, 1), weight=1, uniform="b")
        for i, (text, cmd, color) in enumerate([
                ("＋ Al inicio", self.add_start, BLUE), ("＋ Al final", self.add_end, BLUE),
                ("↳ En ese número", self.insert_at, BLUE), ("✕ Eliminar número", self.remove_at, "#D9534F")]):
            RoundButton(grid, text, cmd, color, NAVY).grid(row=i // 2, column=i % 2, sticky="ew", padx=3, pady=3)

        # Map card
        card = self._card(right, "🗺️  Recorrido de la ruta", PURPLE)
        card.pack(fill="both", expand=True)
        self.chips_var = tk.StringVar()
        tk.Label(card, textvariable=self.chips_var, bg=CARD, fg=BLUE, font=(FONT, 10, "bold")).place(relx=1.0, x=-16, y=14, anchor="ne")
        self.canvas = tk.Canvas(card, bg=CARD, highlightthickness=0, height=340)
        scroll = ttk.Scrollbar(card, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=scroll.set)
        self.canvas.pack(fill="both", expand=True, padx=8)
        scroll.pack(fill="x", padx=8, pady=(0, 8))

        # Message card
        msg = tk.Frame(right, bg="#FFF8E6", highlightbackground="#FFD98A", highlightthickness=1)
        msg.pack(fill="x", pady=(12, 0))
        tk.Label(msg, text="💡", bg="#FFF8E6", font=(FONT, 20)).pack(side="left", padx=14)
        self.explain_var = tk.StringVar()
        tk.Label(msg, textvariable=self.explain_var, bg="#FFF8E6", fg=NAVY, font=(FONT, 11), justify="left",
                 anchor="w", wraplength=620, height=3).pack(side="left", fill="x", padx=(0, 14), pady=10)

    # -- drawing
    def draw(self):
        c = self.canvas
        c.delete("all")
        SP, X0, Y = 200, 110, 190
        nodes = list(self.route.nodes())
        if not nodes:
            c.create_text(300, 170, text="La ruta está vacía. Agrega una parada.", fill=GRAY, font=(FONT, 13))
            c.configure(scrollregion=(0, 0, 600, 340))
            return
        n = len(nodes)
        end = X0 + (n - 1) * SP
        c.create_line(X0 - 70, Y, end + 70, Y, width=10, fill=PALE_BLUE, capstyle="round")
        if n > 1:
            c.create_line(X0, Y, end, Y, width=10, fill=BLUE, capstyle="round")
            for i in range(n - 1):
                for k in (1, 2, 3):                    # chevrons show the bus direction
                    c.create_text(X0 + i * SP + k * SP / 4, Y, text="›" if self.outbound else "‹",
                                  fill="white", font=(FONT, 16, "bold"))
        target = self._ahead(self.bus) if self.bus else None
        for i, node in enumerate(nodes):
            x = X0 + i * SP
            is_bus = node is self.bus
            ring = ORANGE if is_bus else NAVY
            c.create_oval(x - 24, Y - 24, x + 24, Y + 24, fill="white", outline=ring, width=5)
            c.create_text(x, Y, text=str(i + 1), fill=ring, font=(FONT, 14, "bold"))
            c.create_text(x, Y + 54, text=node.value[0], fill=NAVY, font=(FONT, 12, "bold"),
                          width=SP - 30, justify="center")
            zone = node.value[1]
            rrect(c, x - 36, Y + 84, x + 36, Y + 106, 10, fill=ZONE_COLORS.get(zone.upper(), GRAY), outline="")
            c.create_text(x, Y + 95, text=f"Zona {zone}", fill="white", font=(FONT, 9, "bold"))
            if node is target:
                c.create_text(x, Y + 126, text="▲ Próxima parada", fill=BLUE, font=(FONT, 9, "bold"))
            tag = ("INICIO Y FIN" if node is self.route.head and node is self.route.tail
                   else "INICIO" if node is self.route.head else "FIN" if node is self.route.tail else "")
            if tag:
                rrect(c, x - 42, Y - 58, x + 42, Y - 38, 10, fill="#F1E4F1", outline="")
                c.create_text(x, Y - 48, text=tag, fill=PURPLE, font=(FONT, 9, "bold"))
            if is_bus:
                draw_bus(c, x, Y - 100)
                c.create_polygon(x - 8, Y - 82, x + 8, Y - 82, x, Y - 68, fill=ORANGE, outline="")
        c.configure(scrollregion=(0, 0, end + 110, 340))
        if self.bus:                                   # scroll to the bus
            c.xview_moveto(max(0, (X0 + nodes.index(self.bus) * SP - 300) / (end + 110)))

    # -- helpers
    def _stop(self):
        name, zone = self.name_var.get().strip(), self.zone_var.get().strip()
        if not name or not zone:
            messagebox.showwarning("Faltan datos", "Escribe el nombre de la parada y la zona.")
            return None
        return (name, zone)

    def _index(self):
        """The user types 1 for the first stop; the list uses 0."""
        try:
            n = int(self.index_var.get())
        except ValueError:
            messagebox.showwarning("Número inválido", "Escribe el número de la parada (1, 2, 3...).")
            return None
        if n < 1:
            messagebox.showwarning("Número inválido", "El número de parada debe ser 1 o mayor.")
            return None
        return n - 1

    def _clear_form(self):
        for v in (self.name_var, self.zone_var, self.index_var):
            v.set("")

    def _ahead(self, node):
        return node.next if self.outbound else node.prev

    def _behind(self, node):
        return node.prev if self.outbound else node.next

    def refresh(self):
        if self.outbound:
            self.dir_label.config(text="➜  IDA · hacia el final de la ruta", bg=BLUE)
        else:
            self.dir_label.config(text="⬅  REGRESO · hacia el inicio de la ruta", bg=PURPLE)
        if self.bus:
            self.stop_var.set(self.bus.value[0])
            ahead, behind = self._ahead(self.bus), self._behind(self.bus)
            self.nav_var.set(f"◀  Anterior:  {behind.value[0] if behind else 'ninguna (fin de la ruta)'}\n"
                             f"▶  Próxima:  {ahead.value[0] if ahead else 'ninguna (fin de la ruta)'}")
        else:
            self.stop_var.set("Ruta vacía")
            self.nav_var.set("")
        first = self.route.head.value[0] if self.route.head else "-"
        last = self.route.tail.value[0] if self.route.tail else "-"
        self.chips_var.set(f"{self.route.length} paradas   •   Primera: {first}   •   Última: {last}")
        self.draw()

    # -- actions
    def say(self, text):
        self.explain_var.set(text)

    def advance(self):
        if not self.bus:
            return
        ahead = self._ahead(self.bus)
        if ahead:
            self.say(f"El bus pasó de «{self.bus.value[0]}» a «{ahead.value[0]}».")
            self.bus = ahead
            self.refresh()
        else:
            messagebox.showinfo("Fin de la ruta", "El bus llegó al final de la ruta. Cambia el sentido para regresar.")

    def toggle_direction(self):
        self.outbound = not self.outbound
        self.say("Ahora el bus va hacia el final de la ruta." if self.outbound
                 else "Ahora el bus regresa hacia el inicio de la ruta.")
        self.refresh()

    def _after_add(self, node, msg):
        self.bus = self.bus or node
        self._clear_form()
        self.say(msg)
        self.refresh()

    def add_start(self):
        stop = self._stop()
        if stop:
            node = self.route.prepend(stop)
            self._after_add(node, f"Se agregó «{stop[0]}» como primera parada de la ruta.")

    def add_end(self):
        stop = self._stop()
        if stop:
            node = self.route.append(stop)
            self._after_add(node, f"Se agregó «{stop[0]}» como última parada de la ruta.")

    def insert_at(self):
        stop = self._stop()
        idx = self._index() if stop else None
        if stop and idx is not None:
            node = self.route.insert(idx, stop)
            a, b = node.prev, node.next
            if a and b:
                msg = f"Se agregó «{stop[0]}» entre «{a.value[0]}» y «{b.value[0]}»."
            elif b:
                msg = f"Se agregó «{stop[0]}» como primera parada de la ruta."
            elif a:
                msg = f"Se agregó «{stop[0]}» como última parada de la ruta."
            else:
                msg = f"Se agregó «{stop[0]}», la única parada de la ruta."
            self._after_add(node, msg)

    def remove_at(self):
        idx = self._index()
        if idx is None:
            return
        try:
            removed = self.route.remove(idx)
        except IndexError:
            messagebox.showerror("Error", f"No existe la parada número {idx + 1}.")
            return
        a, b, name = removed.prev, removed.next, removed.value[0]
        if a and b:
            msg = f"Se eliminó «{name}». Ahora «{a.value[0]}» sigue directamente a «{b.value[0]}»."
        elif b:
            msg = f"Se eliminó «{name}», que era la primera parada. Ahora la primera es «{b.value[0]}»."
        elif a:
            msg = f"Se eliminó «{name}», que era la última parada. Ahora la última es «{a.value[0]}»."
        else:
            msg = f"Se eliminó «{name}». La ruta quedó vacía."
        if removed is self.bus:                     # keep a valid bus position
            self.bus = self._ahead(removed) or self._behind(removed)
            msg += " Como el bus estaba ahí, pasó a la parada vecina."
        self._clear_form()
        self.say(msg)
        self.refresh()


if __name__ == "__main__":
    BusApp().mainloop()