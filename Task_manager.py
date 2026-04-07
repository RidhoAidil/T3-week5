import sys
import json
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QComboBox, QLineEdit, QDialog, QFormLayout, QDateEdit,
    QMessageBox, QLabel, QStatusBar, QToolBar, QMenu,
    QAbstractItemView, QStyledItemDelegate, QStyleOptionViewItem
)
from PySide6.QtCore import Qt, QDate, QSize, QRect
from PySide6.QtGui import (
    QColor, QBrush, QFont, QAction, QPainter, QPainterPath,
    QFontMetrics, QPen
)

DATA_FILE = os.path.join(os.path.dirname(__file__), "tasks.json")

PRIORITY_ROW_BG = {
    "High":   "#FFEBEE",
    "Medium": "#FFF8E1",
    "Low":    "#E8F5E9",
}
PRIORITY_BADGE = {
    "High":   ("#EF5350", "#FFFFFF"),
    "Medium": ("#FFA726", "#FFFFFF"),
    "Low":    ("#66BB6A", "#FFFFFF"),
}

STATUS_TODO = "Todo"
STATUS_PROG = "In Progress"
STATUS_DONE = "Done"

QSS = """
QMainWindow { background-color: #F0F4F8; }
QMenuBar {
    background-color: #1E2A38; color: #E0E8F0;
    padding: 2px 4px; font-size: 13px;
}
QMenuBar::item:selected { background-color: #2D3E50; border-radius: 4px; }
QMenu { background-color: #1E2A38; color: #E0E8F0; border: 1px solid #2D3E50; }
QMenu::item:selected { background-color: #3D6B9E; }
QToolBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #D0DAE5;
    spacing: 6px; padding: 6px 12px;
}
QToolBar::separator { background-color: #D0DAE5; width: 1px; margin: 4px 8px; }
QPushButton {
    border-radius: 6px; padding: 6px 14px;
    font-size: 13px; font-weight: 600; border: none;
}
QPushButton#btnAdd    { background-color: #2ECC71; color: white; }
QPushButton#btnAdd:hover { background-color: #27AE60; }
QPushButton#btnEdit   { background-color: #3498DB; color: white; }
QPushButton#btnEdit:hover { background-color: #2980B9; }
QPushButton#btnDelete { background-color: #E74C3C; color: white; }
QPushButton#btnDelete:hover { background-color: #C0392B; }
QPushButton#btnOk     { background-color: #3498DB; color: white; min-width: 80px; }
QPushButton#btnOk:hover { background-color: #2980B9; }
QPushButton#btnCancel { background-color: #95A5A6; color: white; min-width: 80px; }
QPushButton#btnCancel:hover { background-color: #7F8C8D; }
QComboBox, QLineEdit, QDateEdit {
    background-color: #FFFFFF; border: 1px solid #C8D6E0;
    border-radius: 6px; padding: 5px 10px;
    font-size: 13px; color: #2C3E50; min-height: 28px;
}
QComboBox:focus, QLineEdit:focus, QDateEdit:focus { border-color: #3498DB; }
QComboBox::drop-down { border: none; padding-right: 8px; }
QComboBox QAbstractItemView {
    background: #FFFFFF; selection-background-color: #D6EAF8;
    border: 1px solid #C8D6E0;
}
QTableWidget {
    gridline-color: #E8EEF3;
    border: none; font-size: 13px; color: #2C3E50;
}
QTableWidget::item { padding: 0px; border-bottom: 1px solid #EBF0F5; }
QTableWidget::item:selected { background-color: rgba(52, 152, 219, 0.3); color: #1A5276; }
QHeaderView::section {
    background-color: #1E2A38; color: #A8C0D0;
    padding: 10px 12px; border: none;
    font-size: 12px; font-weight: 700; letter-spacing: 0.5px;
}
QScrollBar:vertical { border: none; background: #F0F4F8; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: #C8D6E0; border-radius: 4px; }
QStatusBar {
    background-color: #1E2A38; color: #7FB3C8;
    font-size: 12px; padding: 2px 10px;
}
QStatusBar::item { border: none; }
QDialog { background-color: #F0F4F8; }
QFormLayout QLabel { font-size: 13px; color: #5D6D7E; font-weight: 600; }
"""


class BadgeDelegate(QStyledItemDelegate):
    """Paints a coloured pill badge directly onto the Prioritas cell."""

    def paint(self, painter: QPainter, option, index):
        text = index.data(Qt.DisplayRole) or ""
        bg_hex, fg_hex = PRIORITY_BADGE.get(text, ("#AAAAAA", "#FFFFFF"))
        row_bg = index.data(Qt.UserRole)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill row background
        if row_bg:
            painter.fillRect(option.rect, QColor(row_bg))

        # Badge dimensions
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        fm = QFontMetrics(font)
        text_w = fm.horizontalAdvance(text)
        badge_w = text_w + 22
        badge_h = 22
        cx = option.rect.center().x()
        cy = option.rect.center().y()
        badge_rect = QRect(cx - badge_w // 2, cy - badge_h // 2, badge_w, badge_h)

        path = QPainterPath()
        path.addRoundedRect(badge_rect, badge_h / 2, badge_h / 2)
        painter.fillPath(path, QColor(bg_hex))
        painter.setPen(QColor(fg_hex))
        painter.drawText(badge_rect, Qt.AlignCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(100, 46)


class TaskDialog(QDialog):
    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.setWindowTitle("Add Task" if task is None else "Edit Task")
        self.setMinimumWidth(420)
        self.setModal(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet("background-color:#1E2A38;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 0, 18, 0)
        lbl = QLabel("➕  Add Task" if task is None else "✏️  Edit Task")
        lbl.setStyleSheet("color:#E0E8F0; font-size:15px; font-weight:700;")
        hl.addWidget(lbl)
        root.addWidget(header)

        body = QWidget()
        body.setStyleSheet("background:#FFFFFF;")
        form = QFormLayout(body)
        form.setSpacing(14)
        form.setContentsMargins(24, 20, 24, 10)

        self.txt_judul    = QLineEdit()
        self.txt_judul.setPlaceholderText("Masukkan judul task...")
        self.cmb_prioritas = QComboBox()
        self.cmb_prioritas.addItems(["High", "Medium", "Low"])
        self.cmb_status   = QComboBox()
        self.cmb_status.addItems([STATUS_TODO, STATUS_PROG, STATUS_DONE])
        self.date_edit    = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")

        form.addRow("Judul Task :", self.txt_judul)
        form.addRow("Prioritas  :", self.cmb_prioritas)
        form.addRow("Status     :", self.cmb_status)
        form.addRow("Due Date   :", self.date_edit)
        root.addWidget(body)

        btn_bar = QWidget()
        btn_bar.setStyleSheet("background:#FFFFFF;")
        bl = QHBoxLayout(btn_bar)
        bl.setContentsMargins(24, 4, 24, 20)
        bl.addStretch()
        self.btn_cancel = QPushButton("Batal")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_ok = QPushButton("💾  Simpan")
        self.btn_ok.setObjectName("btnOk")
        bl.addWidget(self.btn_cancel)
        bl.addWidget(self.btn_ok)
        root.addWidget(btn_bar)

        self.btn_ok.clicked.connect(self._on_ok)
        self.btn_cancel.clicked.connect(self.reject)

        if task:
            self.txt_judul.setText(task.get("judul", ""))
            i = self.cmb_prioritas.findText(task.get("prioritas", "Medium"))
            if i >= 0: self.cmb_prioritas.setCurrentIndex(i)
            i = self.cmb_status.findText(task.get("status", STATUS_TODO))
            if i >= 0: self.cmb_status.setCurrentIndex(i)
            d = QDate.fromString(task.get("due_date", ""), "yyyy-MM-dd")
            if d.isValid(): self.date_edit.setDate(d)

    def _on_ok(self):
        if not self.txt_judul.text().strip():
            QMessageBox.warning(self, "Validasi", "Judul task tidak boleh kosong!")
            return
        self.accept()

    def get_data(self):
        return {
            "judul":     self.txt_judul.text().strip(),
            "prioritas": self.cmb_prioritas.currentText(),
            "status":    self.cmb_status.currentText(),
            "due_date":  self.date_edit.date().toString("yyyy-MM-dd"),
        }


class TaskManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Manager")
        self.setMinimumSize(860, 520)
        self.tasks = []
        self._load_data()
        self._build_ui()
        self._refresh_table()

    def _load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
                return
            except Exception:
                pass
        self.tasks = [
            {"judul": "Sholat", "prioritas": "High",
             "status": STATUS_PROG, "due_date": "2026-04-01"},
            {"judul": "Membuat tugas pemvis", "prioritas": "Medium",
             "status": STATUS_TODO, "due_date": "2026-04-05"},
            {"judul": "Push hasilnya ke GitHub", "prioritas": "Low",
             "status": STATUS_DONE, "due_date": "2026-03-30"},
        ]

    def _save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False)

    def _build_ui(self):
        mb = self.menuBar()
        fm = mb.addMenu("File")
        fm.addAction(QAction("💾  Simpan Data", self, triggered=self._save_data))
        fm.addSeparator()
        fm.addAction(QAction("❌  Keluar", self, triggered=self.close))
        tm = mb.addMenu("Task")
        tm.addAction(QAction("➕  Add Task",  self, triggered=self._add_task))
        tm.addAction(QAction("✏️  Edit Task", self, triggered=self._edit_task))
        tm.addAction(QAction("🗑  Delete",    self, triggered=self._delete_task))
        hm = mb.addMenu("Help")
        hm.addAction(QAction("ℹ️  Tentang", self, triggered=lambda: QMessageBox.information(
            self, "Tentang", "Task Manager v1.0\nDibuat dengan PySide6")))

        tb = QToolBar()
        tb.setMovable(False)
        self.addToolBar(tb)

        self.btn_add  = QPushButton("➕  Add Task"); self.btn_add.setObjectName("btnAdd")
        self.btn_edit = QPushButton("✏️  Edit");    self.btn_edit.setObjectName("btnEdit")
        self.btn_del  = QPushButton("🗑  Delete");  self.btn_del.setObjectName("btnDelete")
        self.btn_add.clicked.connect(self._add_task)
        self.btn_edit.clicked.connect(self._edit_task)
        self.btn_del.clicked.connect(self._delete_task)

        self.cmb_filter = QComboBox()
        self.cmb_filter.setFixedWidth(120)
        self.cmb_filter.addItems(["Semua","High","Medium","Low",
                                  STATUS_TODO, STATUS_PROG, STATUS_DONE])
        self.cmb_filter.currentTextChanged.connect(self._refresh_table)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍  Cari task...")
        self.txt_search.setFixedWidth(180)
        self.txt_search.textChanged.connect(self._refresh_table)

        for w in [self.btn_add, self.btn_edit, self.btn_del]:
            tb.addWidget(w)
        tb.addSeparator()
        lbl_f = QLabel("  Filter: ")
        lbl_f.setStyleSheet("color:#5D6D7E; font-size:13px;")
        tb.addWidget(lbl_f)
        tb.addWidget(self.cmb_filter)
        tb.addWidget(self.txt_search)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["No", "Judul Task", "Prioritas", "Status", "Due Date"])

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed); self.table.setColumnWidth(0, 40)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Fixed); self.table.setColumnWidth(2, 100)
        hh.setSectionResizeMode(3, QHeaderView.Fixed); self.table.setColumnWidth(3, 120)
        hh.setSectionResizeMode(4, QHeaderView.Fixed); self.table.setColumnWidth(4, 100)

        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setShowGrid(False)

        self._badge_delegate = BadgeDelegate(self.table)
        self.table.setItemDelegateForColumn(2, self._badge_delegate)
        self.table.doubleClicked.connect(self._edit_task)

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(12, 12, 12, 0)
        lay.setSpacing(0)
        lay.addWidget(self.table)
        self.setCentralWidget(central)

        sb = QStatusBar(); self.setStatusBar(sb)
        self.lbl_summary = QLabel()
        self.lbl_file = QLabel("tasks.json")
        self.lbl_file.setStyleSheet("color:#3D8DB0;")
        sb.addWidget(self.lbl_summary)
        sb.addPermanentWidget(self.lbl_file)

    def _filtered_tasks(self):
        flt = self.cmb_filter.currentText()
        q   = self.txt_search.text().strip().lower()
        return [t for t in self.tasks
                if (flt == "Semua" or flt in (t["prioritas"], t["status"]))
                and (not q or q in t["judul"].lower())]

    def _refresh_table(self):
        visible = self._filtered_tasks()
        self.table.setRowCount(len(visible))
        for row, task in enumerate(visible):
            pri    = task["prioritas"]
            row_bg = PRIORITY_ROW_BG.get(pri, "#FFFFFF")
            bg     = QColor(row_bg)

            # capture bg/row_bg by value to avoid closure bug
            def make_cell(text, _bg=QColor(row_bg), _rbg=row_bg,
                          align=Qt.AlignVCenter | Qt.AlignLeft):
                it = QTableWidgetItem(text)
                it.setTextAlignment(align)
                it.setBackground(QBrush(_bg))
                it.setData(Qt.UserRole, _rbg)
                return it

            self.table.setItem(row, 0, make_cell(str(row+1), align=Qt.AlignCenter))
            self.table.setItem(row, 1, make_cell(f"  {task['judul']}"))
            self.table.setItem(row, 2, make_cell(pri, align=Qt.AlignCenter))

            status = task["status"]
            if status == STATUS_DONE: status = "Done ✓"
            self.table.setItem(row, 3, make_cell(f"  {status}"))
            self.table.setItem(row, 4, make_cell(task["due_date"], align=Qt.AlignCenter))
            self.table.setRowHeight(row, 46)

        self._update_status()

    def _update_status(self):
        total = len(self.tasks)
        done  = sum(1 for t in self.tasks if t["status"] == STATUS_DONE)
        prog  = sum(1 for t in self.tasks if t["status"] == STATUS_PROG)
        todo  = sum(1 for t in self.tasks if t["status"] == STATUS_TODO)
        self.lbl_summary.setText(
            f"  Total: {total} tasks  |  Done: {done}  |  "
            f"In Progress: {prog}  |  Todo: {todo}  ")

    def _selected_idx(self):
        row = self.table.currentRow()
        if row < 0: return -1
        visible = self._filtered_tasks()
        if row >= len(visible): return -1
        target = visible[row]
        for i, t in enumerate(self.tasks):
            if t is target: return i
        return -1

    def _add_task(self):
        dlg = TaskDialog(self)
        dlg.setStyleSheet(QSS)
        if dlg.exec() == QDialog.Accepted:
            self.tasks.append(dlg.get_data())
            self._save_data(); self._refresh_table()

    def _edit_task(self):
        idx = self._selected_idx()
        if idx < 0:
            QMessageBox.information(self, "Edit Task", "Pilih task yang ingin diedit.")
            return
        dlg = TaskDialog(self, task=self.tasks[idx])
        dlg.setStyleSheet(QSS)
        if dlg.exec() == QDialog.Accepted:
            self.tasks[idx] = dlg.get_data()
            self._save_data(); self._refresh_table()

    def _delete_task(self):
        idx = self._selected_idx()
        if idx < 0:
            QMessageBox.information(self, "Delete Task", "Pilih task yang ingin dihapus.")
            return
        ans = QMessageBox.question(
            self, "Konfirmasi Hapus",
            f"Yakin ingin menghapus task:\n«{self.tasks[idx]['judul']}»?",
            QMessageBox.Yes | QMessageBox.No)
        if ans == QMessageBox.Yes:
            self.tasks.pop(idx)
            self._save_data(); self._refresh_table()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Task Manager")
    app.setStyleSheet(QSS)
    win = TaskManager()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()