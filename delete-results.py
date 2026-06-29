import sqlite3

conn = sqlite3.connect("church_v3.db")
cursor = conn.cursor()

# This deletes everything in competition_results but leaves church_schools alone
cursor.execute("DELETE FROM competition_results")

conn.commit()
print(f"Successfully deleted all records. Rows affected: {cursor.rowcount}")
conn.close()