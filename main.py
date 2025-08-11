import app

# Default database: casino.db


def start():
    app.get_overview_data()
    app.fill_casino_frame()
    app.fill_transaction_frame()

    app.root.mainloop()

def close():
    app.read_data.close()

if __name__ == "__main__":
    start()
    close()