import sys
import json
import requests
import os
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, 
                             QMessageBox, QHeaderView, QCalendarWidget,
                             QDialog, QFormLayout, QFrame, QStackedWidget)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor
from dotenv import load_dotenv

load_dotenv()

# --- KONFIGURASI ---
DB_FILE = "kasir_data.json"
API_KEY = os.getenv("WEATHER_API_KEY") 
CITY = "Pontianak"

# --- STYLESHEET (High Contrast & Modern) ---
STYLE_SHEET = """
QMainWindow { background-color: #ffffff; }
QFrame#Sidebar { background-color: #2c3e50; min-width: 200px; }
QLabel#Logo { color: #ffffff; font-size: 20px; font-weight: bold; padding: 20px; }
QPushButton#SideBtn { 
    background-color: transparent; color: #ecf0f1; border: none; padding: 15px; 
    text-align: left; font-size: 14px; border-left: 5px solid transparent;
}
QPushButton#SideBtn:checked { background-color: #34495e; color: white; border-left: 5px solid #3498db; }

QLabel { color: #2c3e50; }
QTableWidget { background-color: #ffffff; color: #000000; gridline-color: #dcdde1; border: 1px solid #dcdde1; }
QHeaderView::section { background-color: #f8f9fa; color: #000000; font-weight: bold; border: 1px solid #dcdde1; }

QPushButton#BlueBtn { background-color: #3498db; color: white; border-radius: 5px; padding: 10px; font-weight: bold; }
QPushButton#GreenBtn { background-color: #62f05d; color: green; border-radius: 5px; padding: 10px; font-weight: bold; }
QPushButton#RedBtn { background-color: #ffffff; color: red; border-radius: 5px; padding: 10px; font-weight: bold; }
"""
#Input Menu
class InputDialog(QDialog):
    def __init__(self, title, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(300)
        layout = QFormLayout(self)
        self.inputs = {}
        for field in fields:
            self.inputs[field] = QLineEdit()
            layout.addRow(QLabel(field), self.inputs[field])
        self.btn = QPushButton("SIMPAN"); self.btn.clicked.connect(self.accept)
        layout.addRow(self.btn)

    def get_data(self):
        return {f: self.inputs[f].text() for f in self.inputs}

#Tab Kasir
class CashierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kasir Warung Kak San")
        self.resize(1200, 800)
        self.setStyleSheet(STYLE_SHEET)
        
        self.data = self.load_data()
        self.cart = [] # List untuk menampung item sementara sebelum bayar
        self.selected_date = QDate.currentDate().toString("dd/MM/yyyy")
        
        self.init_ui()
        self.refresh_ui()
 
    # Logika Memuat Data
    def load_data(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f: return json.load(f)
            except: pass
        return {"menu": [], "transaksi": [], "pengeluaran": []}

    # Logika Menyimpan Data
    def save_data(self):
        with open(DB_FILE, "w") as f: json.dump(self.data, f, indent=4)
    
    # Logika Mendapatkan Data Cuaca
    def get_weather(self):
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=id"
            res = requests.get(url, timeout=2)
            if res.status_code == 200:
                return res.json()['weather'][0]['description'].capitalize()
            return "Cuaca Tidak Tersedia"
        except: return "Offline"

    # Inisialisasi UI
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)

        sidebar = QFrame(); sidebar.setObjectName("Sidebar")
        side_layout = QVBoxLayout(sidebar)
        lbl_logo = QLabel("KASIR KAK SAN"); lbl_logo.setObjectName("Logo"); side_layout.addWidget(lbl_logo)
        
        self.btn_nav_kasir = QPushButton("KASIR"); self.btn_nav_kasir.setCheckable(True); self.btn_nav_kasir.setChecked(True)
        self.btn_nav_log = QPushButton("LOG OMSET"); self.btn_nav_log.setCheckable(True)
        for b in [self.btn_nav_kasir, self.btn_nav_log]:
            b.setObjectName("SideBtn"); side_layout.addWidget(b)
        
        self.btn_nav_kasir.clicked.connect(lambda: self.switch_tab(0))
        self.btn_nav_log.clicked.connect(lambda: self.switch_tab(1))
        side_layout.addStretch(); layout.addWidget(sidebar)

        self.stack = QStackedWidget(); layout.addWidget(self.stack)
        self.setup_kasir_page(); self.setup_log_page()

    #Halaman Kasir
    def setup_kasir_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(20,20,20,20)
        
        # Atas: Manajemen Menu
        top = QHBoxLayout()
        top.addWidget(QLabel("<h2>Pilih Menu</h2>"))
        btn_add_m = QPushButton("+ Menu Baru"); btn_add_m.setObjectName("BlueBtn")
        btn_add_m.clicked.connect(self.pop_add_menu)
        top.addStretch(); top.addWidget(btn_add_m)
        layout.addLayout(top)

        # Tengah: Selector & Keranjang
        mid = QHBoxLayout()
        
        # Left: Tabel Menu Tersedia
        self.table_menu = QTableWidget(0, 2)
        self.table_menu.setHorizontalHeaderLabels(["Menu", "Harga"])
        self.table_menu.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        mid.addWidget(self.table_menu, 1)

        # Right: Keranjang Belanja
        cart_box = QFrame(); cart_box.setStyleSheet("background: #fdfdfd; border: 1px solid #ddd; border-radius: 8px;")
        cart_layout = QVBoxLayout(cart_box)
        cart_layout.addWidget(QLabel("<b>KERANJANG BELANJA</b>"))
        
        self.table_cart = QTableWidget(0, 3)
        self.table_cart.setHorizontalHeaderLabels(["Item", "Qty", "Subtotal"])
        self.table_cart.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        cart_layout.addWidget(self.table_cart)
        
        self.lbl_total_cart = QLabel("TOTAL: Rp 0"); self.lbl_total_cart.setStyleSheet("font-size: 20px; font-weight: bold; color: #27ae60;")
        cart_layout.addWidget(self.lbl_total_cart)
        
        btn_pay = QPushButton("PROSES & BAYAR SEKARANG"); btn_pay.setObjectName("GreenBtn"); btn_pay.setFixedHeight(50)
        btn_pay.clicked.connect(self.process_payment)
        cart_layout.addWidget(btn_pay)
        
        btn_clear = QPushButton("Kosongkan Keranjang"); btn_clear.setObjectName("RedBtn")
        btn_clear.clicked.connect(self.clear_cart)
        cart_layout.addWidget(btn_clear)

        mid.addWidget(cart_box, 1)
        layout.addLayout(mid)

        # Bottom: Input Area
        input_bar = QHBoxLayout()
        self.cb_menu = QComboBox(); self.cb_menu.setMinimumHeight(35)
        self.ent_qty = QLineEdit(); self.ent_qty.setPlaceholderText("Qty"); self.ent_qty.setFixedWidth(60)
        btn_add_cart = QPushButton("TAMBAH KE KERANJANG"); btn_add_cart.setObjectName("BlueBtn")
        btn_add_cart.clicked.connect(self.add_to_cart)
        
        input_bar.addWidget(QLabel("Pilih:")); input_bar.addWidget(self.cb_menu)
        input_bar.addWidget(QLabel("Jumlah:")); input_bar.addWidget(self.ent_qty)
        input_bar.addWidget(btn_add_cart)
        layout.addLayout(input_bar)
        
        self.stack.addWidget(page)

    #Log Omset
    def setup_log_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(20,20,20,20)
        
        split = QHBoxLayout()
        self.cal = QCalendarWidget(); self.cal.setFixedWidth(300); self.cal.clicked.connect(self.on_date_selected)
        split.addWidget(self.cal)

        self.card = QFrame(); self.card.setStyleSheet("background: white; border: 1px solid #3498db; border-radius: 10px; padding: 15px;")
        c_lay = QVBoxLayout(self.card)
        self.lbl_sum_date = QLabel("DATE"); self.lbl_sum_date.setStyleSheet("font-weight: bold; color: #3498db;")
        self.lbl_in = QLabel("Pemasukan: Rp 0"); self.lbl_out = QLabel("Pengeluaran: Rp 0")
        self.lbl_net = QLabel("Net: Rp 0"); self.lbl_net.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        btn_exp = QPushButton("+ Biaya Operasional"); btn_exp.setObjectName("RedBtn")
        btn_exp.clicked.connect(self.pop_add_expense)
        c_lay.addWidget(self.lbl_sum_date); c_lay.addWidget(self.lbl_in); c_lay.addWidget(self.lbl_out); c_lay.addStretch(); c_lay.addWidget(self.lbl_net); c_lay.addWidget(btn_exp)
        split.addWidget(self.card)
        layout.addLayout(split)

        self.table_log = QTableWidget(0, 5)
        self.table_log.setHorizontalHeaderLabels(["Tipe", "Keterangan (Item)", "Total", "Cuaca", "Waktu"])
        self.table_log.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_log.cellDoubleClicked.connect(self.prepare_edit)
        layout.addWidget(self.table_log)
        
        foot = QHBoxLayout()
        btn_del = QPushButton("Hapus Baris"); btn_del.setObjectName("RedBtn"); btn_del.clicked.connect(self.delete_entry)
        self.btn_upd = QPushButton("SIMPAN EDIT"); self.btn_upd.setObjectName("BlueBtn"); self.btn_upd.setVisible(False); self.btn_upd.clicked.connect(self.update_entry)
        foot.addWidget(btn_del); foot.addStretch(); foot.addWidget(self.btn_upd)
        layout.addLayout(foot)

        self.stack.addWidget(page)

    # LOGIKA KERANJANG & PROSES

    def switch_tab(self, i):
        self.stack.setCurrentIndex(i)
        self.btn_nav_kasir.setChecked(i==0); self.btn_nav_log.setChecked(i==1)

    # Logika Keranjang & Proses Pembayaran
    def add_to_cart(self):
        name = self.cb_menu.currentText()
        qty_str = self.ent_qty.text()
        if not name or not qty_str.isdigit(): return
        
        qty = int(qty_str)
        price = next(m['harga'] for m in self.data['menu'] if m['nama'] == name)
        
        # Cek jika item sudah ada di keranjang, tinggal update qty
        found = False
        for item in self.cart:
            if item['nama'] == name:
                item['qty'] += qty
                item['subtotal'] = item['qty'] * price
                found = True
                break
        
        if not found:
            self.cart.append({'nama': name, 'qty': qty, 'harga_satuan': price, 'subtotal': qty * price})
        
        self.ent_qty.clear()
        self.update_cart_display()

    # Perbarui Tampilan Keranjang
    def update_cart_display(self):
        self.table_cart.setRowCount(len(self.cart))
        total = 0
        for i, item in enumerate(self.cart):
            self.table_cart.setItem(i, 0, QTableWidgetItem(item['nama']))
            self.table_cart.setItem(i, 1, QTableWidgetItem(str(item['qty'])))
            self.table_cart.setItem(i, 2, QTableWidgetItem(f"Rp {item['subtotal']}"))
            total += item['subtotal']
        self.lbl_total_cart.setText(f"TOTAL: Rp {total}")

    # Kosongkan Keranjang
    def clear_cart(self):
        self.cart = []; self.update_cart_display()

    # Proses Pembayaran & Simpan ke Log
    def process_payment(self):
        if not self.cart:
            QMessageBox.warning(self, "Kosong", "Keranjang masih kosong!")
            return

        total_final = sum(item['subtotal'] for item in self.cart)
        # Gabungkan nama-nama menu untuk log
        items_summary = ", ".join([f"{item['nama']} (x{item['qty']})" for item in self.cart])
        
        weather = self.get_weather()
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Simpan ke log transaksi
        self.data["transaksi"].append({
            "ket": items_summary,
            "nominal": total_final,
            "cuaca": weather,
            "waktu": now
        })
        
        self.save_data()
        self.clear_cart()
        self.refresh_ui()
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Sukses")
        msg.setText(f"Pembayaran Rp {total_final} Berhasil dicatat!\nCuaca: {weather}")

        msg.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton {
                color: #ffffff;
                background-color: #3a3a3a;
                border: 1px solid #ff8c66;
                padding: 5px 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)

        msg.exec()

    # Perbarui Tampilan UI
    def refresh_ui(self):
        self.cb_menu.clear()
        self.table_menu.setRowCount(len(self.data["menu"]))
        for i, m in enumerate(self.data["menu"]):
            self.cb_menu.addItem(m["nama"])
            self.table_menu.setItem(i, 0, QTableWidgetItem(m["nama"]))
            self.table_menu.setItem(i, 1, QTableWidgetItem(f"Rp {m['harga']}"))
        self.on_date_selected(self.cal.selectedDate())

    # Menampilkan Data Log Berdasarkan Tanggal Terpilih
    def on_date_selected(self, qdate):
        self.selected_date = qdate.toString("dd/MM/yyyy")
        self.lbl_sum_date.setText(self.selected_date)
        filtered = []; inc = 0; exp = 0
        for i, t in enumerate(self.data["transaksi"]):
            if t['waktu'].startswith(self.selected_date):
                filtered.append(["Pemasukan", t['ket'], t['nominal'], t['cuaca'], t['waktu'], 'transaksi', i])
                inc += t['nominal']
        for i, e in enumerate(self.data["pengeluaran"]):
            if e['waktu'].startswith(self.selected_date):
                filtered.append(["Pengeluaran", e['ket'], e['nominal'], e['cuaca'], e['waktu'], 'pengeluaran', i])
                exp += e['nominal']
        
        self.lbl_in.setText(f"Pemasukan: Rp {inc}"); self.lbl_out.setText(f"Pengeluaran: Rp {exp}")
        self.lbl_net.setText(f"Net Omset: Rp {inc-exp}")
        
        self.table_log.setRowCount(len(filtered))
        for i, r in enumerate(filtered):
            for j in range(5):
                item = QTableWidgetItem(str(r[j]))
                if j == 0: 
                    item.setData(Qt.UserRole, r[5]); item.setData(Qt.UserRole + 1, r[6])
                self.table_log.setItem(i, j, item)

    # Popup Tambah Menu Baru
    def pop_add_menu(self):
        d = InputDialog("Tambah Menu", ["Nama", "Harga"], self)
        if d.exec():
            res = d.get_data()
            if res["Nama"] and res["Harga"].isdigit():
                self.data["menu"].append({"nama": res["Nama"], "harga": int(res["Harga"])})
                self.save_data(); self.refresh_ui()

    # Popup Tambah Pengeluaran
    def pop_add_expense(self):
        d = InputDialog("Input Pengeluaran", ["Ket", "Nominal"], self)
        if d.exec():
            res = d.get_data()
            if res["Ket"] and res["Nominal"].isdigit():
                now = datetime.now().strftime("%H:%M:%S")
                self.data["pengeluaran"].append({"ket": res["Ket"], "nominal": int(res["Nominal"]), "cuaca": "-", "waktu": f"{self.selected_date} {now}"})
                self.save_data(); self.refresh_ui()

    # Siapkan Edit Entry
    def prepare_edit(self, r, c):
        self.current_edit_type = self.table_log.item(r, 0).data(Qt.UserRole)
        self.current_edit_index = self.table_log.item(r, 0).data(Qt.UserRole + 1)
        self.btn_upd.setVisible(True)

    # Perbarui Entry Setelah Edit
    def update_entry(self):
        for r in range(self.table_log.rowCount()):
            if (self.table_log.item(r, 0).data(Qt.UserRole) == self.current_edit_type and 
                self.table_log.item(r, 0).data(Qt.UserRole + 1) == self.current_edit_index):
                target = self.data["transaksi"] if self.current_edit_type == "transaksi" else self.data["pengeluaran"]
                target[self.current_edit_index]["ket"] = self.table_log.item(r, 1).text()
                val = self.table_log.item(r, 2).text()
                target[self.current_edit_index]["nominal"] = int(val) if val.isdigit() else 0
                break
        self.save_data(); self.btn_upd.setVisible(False); self.refresh_ui()

    # Hapus Entry dari Log
    def delete_entry(self):
        row = self.table_log.currentRow()
        if row < 0: return
        t = self.table_log.item(row,0).data(Qt.UserRole); idx = self.table_log.item(row,0).data(Qt.UserRole+1)
        if QMessageBox.question(self, "Hapus", "Yakin hapus?") == QMessageBox.Yes:
            if t == "transaksi": self.data["transaksi"].pop(idx)
            else: self.data["pengeluaran"].pop(idx)
            self.save_data(); self.refresh_ui()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CashierApp()
    window.show()
    sys.exit(app.exec())