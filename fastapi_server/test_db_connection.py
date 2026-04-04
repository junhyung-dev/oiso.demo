import traceback
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        from db.session import engine
        with engine.connect() as connection:
            print("\nSUCCESS! Connected to remote PostgreSQL DB.")
            print(f"URL: {engine.url.render_as_string(hide_password=True)}\n")
    except Exception as e:
        print("\nCONNECTION FAILED:")
        print(str(e))
        with open('error_log.txt', 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    test_connection()
