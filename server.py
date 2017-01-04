from geemusic import app
import os

if __name__ == '__main__':
    debug = str(os.environ.get('DEBUG', "False")).lower() == 'true'
    port = int(os.environ.get("PORT", 4000))
    app.run(host='0.0.0.0', port=port, debug=debug)
