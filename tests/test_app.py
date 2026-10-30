from fastapi.testclient import TestClient

def test_text_sha256():
    from app import app
    with TestClient(app, base_url='http://192.168.31.150:5082') as client:
        response = client.post('/api/text', data={'operation':'sha256','text':'hello'})
        assert response.status_code == 200
        assert response.json()['result'] == '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824'
